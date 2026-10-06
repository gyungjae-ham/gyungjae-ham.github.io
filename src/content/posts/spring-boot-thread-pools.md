---
author: "luca"
pubDatetime: 2024-12-18T23:29:10+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Spring Boot 요청이 느릴 때 어느 스레드가 기다리는지 확인하기"
slug: "spring-boot-thread-pools"
featured: false
draft: false
tags:
  - 학습노트
  - spring-boot
  - thread-pool
  - kotlin
  - coroutine
  - tomcat
  - performance
description: "Tomcat, @Async, Kotlin 코루틴의 실행 위치와 병렬도를 구분하고, DB·외부 호출 대기를 찾아 풀 설정을 조정하는 방법을 정리합니다."
---

Spring MVC 서버에서 요청이 느려지면 Tomcat 스레드 수부터 보게 됩니다. 하지만 요청 안에서 JDBC를 호출하고, 알림은 `@Async`로 보내고, 일부 계산은 코루틴으로 넘긴다면 기다리는 곳이 여러 군데입니다. 어느 작업이 어떤 실행기에 올라가는지 알아야 설정을 바꿀 수 있습니다.

이 글은 **플랫폼 스레드를 사용하는 Spring Boot 3.x의 Servlet 애플리케이션과 Kotlin/JVM 코루틴**을 기준으로 설명합니다. 가상 스레드를 활성화한 환경이나 WebFlux에는 같은 수치를 그대로 적용하지 않습니다.

## 실행 위치와 병렬도는 따로 본다

| 실행기                   | 담당 작업                     | 확인할 설정                                    |
| ------------------------ | ----------------------------- | ---------------------------------------------- |
| Tomcat                   | HTTP 요청 처리                | `server.tomcat.threads.max`, 연결 수와 대기 큐 |
| `ThreadPoolTaskExecutor` | 명시적으로 위임한 비동기 작업 | core/max pool size, queue capacity             |
| `Dispatchers.Default`    | CPU를 사용하는 코루틴 작업    | 기본 병렬도는 CPU 코어 수, 최소 2              |
| `Dispatchers.IO`         | 블로킹 I/O 작업               | 기본 병렬도는 64와 CPU 코어 수 중 큰 값        |

예를 들어 8코어 환경의 `Default` 기본 병렬도는 8입니다. `IO`의 기본 병렬도는 64지만 **두 디스패처는 내부 스레드를 공유**합니다. 각 설정값을 더해서 프로세스의 실제 스레드 수라고 볼 수는 없습니다. JVM 자체 스레드와 다른 라이브러리의 실행기도 별도로 존재합니다. [Kotlin Default 문서](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-default.html), [IO 문서](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html)

## Tomcat이 바쁜 이유가 DB일 수 있다

동기 Servlet 요청이 JDBC 응답을 기다리는 동안 요청 처리 스레드는 다른 요청을 처리하지 못합니다. 이때 Tomcat 워커만 늘리면 DB 커넥션을 기다리는 요청이 더 많아질 수 있습니다.

`maxThreads`는 요청 처리 스레드의 한도이고, `maxConnections`는 연결 수의 한도입니다. `acceptCount`는 연결 한도에 도달했을 때 운영체제의 연결 대기 큐에 관한 설정입니다. 이를 모두 하나의 HTTP 요청 큐로 해석하면 병목 위치를 잘못 짚게 됩니다. [Tomcat HTTP Connector](https://tomcat.apache.org/tomcat-10.1-doc/config/http.html)

확인할 것은 바쁜 스레드 수와 함께 그 스레드가 기다리는 대상입니다. 스레드 덤프에서 JDBC 대기가 많다면 DB 실행 시간과 커넥션 획득 대기를 나눠 보고, 외부 HTTP 호출이 많다면 호출별 타임아웃과 동시 요청 수를 봅니다. 응답 지연만으로 풀 부족을 확정하지 않습니다.

## 비동기 큐가 길어질 때

다음은 동작을 설명하기 위한 설정입니다. 이 실행기를 쓰려면 `@EnableAsync`와 함께 호출 메서드에 `@Async("notificationExecutor")`를 지정합니다. 같은 객체 내부 호출에는 기본 프록시 방식의 `@Async`가 적용되지 않습니다.

```kotlin
@Bean
fun notificationExecutor(): ThreadPoolTaskExecutor =
    ThreadPoolTaskExecutor().apply {
        corePoolSize = 4
        maxPoolSize = 8
        queueCapacity = 100
        setThreadNamePrefix("notification-")
    }
```

core 크기까지 스레드를 만든 뒤에는 우선 큐에 작업을 넣고, 큐가 가득 차면 max 크기까지 늘어납니다. 기본적으로 모든 core 스레드가 시작부터 만들어지는 것은 아닙니다. 큐와 스레드가 모두 찼을 때는 거절 정책이 적용됩니다.

큐가 잠깐 생기는 것과 계속 늘어나는 것은 다릅니다. 알림이 허용 시간 안에 도착하는지, 오래된 작업을 언제 포기할지, 실패한 작업을 누가 다시 실행할지까지 함께 정해야 합니다. [Spring 비동기 실행 설명](https://docs.spring.io/spring-framework/reference/integration/scheduling.html)

## 코루틴으로 바꿔도 블로킹 호출은 남는다

`suspend` 함수 안에서 JDBC를 호출한다고 JDBC가 비동기로 바뀌지는 않습니다. 블로킹 작업은 `IO`, 계산 작업은 `Default`처럼 작업의 특성에 맞춰 실행 위치를 고릅니다.

`Dispatchers.IO.limitedParallelism(8)`은 특정 작업의 동시 실행을 제한하는 데 쓸 수 있습니다. 다만 독립된 전용 스레드 풀을 만드는 기능은 아닙니다. IO의 여러 view는 기본 IO 병렬도와 별개로 확장될 수 있으므로, view를 늘리면서 전체 DB·외부 API 용량을 넘어가지 않는지 확인해야 합니다.

설정 변경의 기준은 스레드 수의 합계가 아니라 대기 원인입니다. 같은 부하에서 실행 중인 작업, 대기 시간, DB와 외부 서비스의 처리량을 비교해야 풀을 늘리는 변경이 도움이 됐는지 알 수 있습니다.
