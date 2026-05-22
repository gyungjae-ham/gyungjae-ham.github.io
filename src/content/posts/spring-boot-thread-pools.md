---
author: "luca"
pubDatetime: 2024-12-18T23:29:10+09:00
modDatetime: 2026-05-23T00:00:00+09:00
title: "Spring Boot 배포 시 스레드는 어디서 어떻게 생기는가 — Tomcat · @Async · Coroutine 세 풀의 합"
slug: "spring-boot-thread-pools"
featured: false
draft: false
tags:
  - spring-boot
  - thread-pool
  - kotlin
  - coroutine
  - tomcat
  - performance
description: "Tomcat 200 개를 잡아두면 끝일 줄 알았는데, 실은 @Async 풀과 Coroutine Dispatchers 풀이 각자 따로 살고 있습니다. 세 풀의 관계와 컨테이너 환경에서 신경 써야 할 합계를 정리합니다."
---

> 그때는 "풀 크기를 얼마로 잡을까" 에만 관심이 있었는데, 지금은 "풀이 차오를 때 어디서 차오르는가 — Tomcat 인지 `@Async` 인지 `Dispatchers.IO` 인지 — 를 보는 게 먼저" 라고 봅니다. 컨테이너 한 대 위에 세 풀이 동시에 살고 있다는 사실을 운영을 거치고 나서야 몸으로 알았습니다.

배포 직전에 흔히 던지는 질문은 "Tomcat 스레드 풀을 몇 개로 잡아야 하나" 입니다. 그런데 Kotlin 으로 Spring Boot 를 굴리는 서비스에서는, Tomcat 풀 옆에 `@Async` 전용 풀과 Coroutine `Dispatchers` 풀이 각자 따로 살아갑니다. 세 풀은 서로의 크기를 모릅니다. 컨테이너의 자원 한도는 한 줄인데, 세 풀의 합은 따로 계산됩니다.

## 1. Tomcat 요청 처리 풀

내장 Tomcat 은 HTTP 요청을 받기 위해 워커 스레드 풀을 둡니다. Spring Boot 의 기본 설정은 `server.tomcat.threads.max=200` 입니다. 이 풀의 스레드는 모두 **OS 네이티브 스레드와 1:1 로 매핑** 됩니다. JVM 안에서만 보이는 가상 스레드가 아니라, 컨테이너 위의 리눅스 커널이 실제로 스케줄링하는 스레드입니다.

- 한 요청 = 한 워커 스레드. 요청이 끝날 때까지 그 스레드는 점유됩니다.
- 동기 블로킹 호출(JDBC, 외부 API 동기 호출 등)이 끼면, 그 시간 동안 스레드 하나가 통째로 묶입니다.
- 200 이라는 숫자는 "동시에 처리 가능한 HTTP 요청의 상한" 입니다. 그 이상은 큐잉되거나 거부됩니다.

여기까지가 1 차원입니다. 문제는 이 200 이 서비스 전체의 스레드 한도가 아니라는 점입니다.

## 2. `@Async` 전용 풀

Spring 의 `@Async` 어노테이션이 붙은 메서드는 Tomcat 워커 스레드에서 실행되지 않습니다. 별도의 `ThreadPoolTaskExecutor` 빈에 위임됩니다. 설정 예시는 다음과 같습니다.

```kotlin
@Configuration
@EnableAsync
class AsyncConfig : AsyncConfigurer {

    @Bean(name = ["asyncExecutor"])
    override fun getAsyncExecutor(): Executor {
        val executor = ThreadPoolTaskExecutor()
        executor.corePoolSize = 10
        executor.maxPoolSize = 50
        executor.queueCapacity = 100
        executor.setThreadNamePrefix("Async-")
        executor.initialize()
        return executor
    }
}
```

- `corePoolSize` 만큼은 상시 살아 있고, 부하가 오르면 `maxPoolSize` 까지 늘어납니다.
- 큐(`queueCapacity`)가 먼저 차고, 그 다음 스레드가 늘어납니다. 큐를 너무 크게 잡으면 부하가 와도 스레드는 늘지 않고 응답만 느려집니다.
- 이 풀의 스레드도 전부 OS 네이티브 스레드입니다. Tomcat 풀과 자원은 공유하지만 카운터는 별개입니다.

`@Async` 풀은 보통 "메일 발송, 알림, 비동기 로깅" 같은 곁가지 작업에 쓰이지만, 운영 트래픽이 몰리면 곁가지가 본가지를 마비시키는 경우가 자주 나옵니다.

## 3. Coroutine `Dispatchers` 풀

Kotlin 코루틴은 코드 위에서는 가볍지만, 결국 실행되는 곳은 OS 스레드 위입니다. 코루틴 전환은 OS 컨텍스트 스위치보다 비용이 훨씬 적습니다. 다만 그 "스레드 위" 가 어느 풀이냐는 디스패처가 결정합니다.

- **`Dispatchers.Default`**: CPU 바운드 작업용. 기본 크기는 `min(코어 수 × 2, 128)`.
- **`Dispatchers.IO`**: 블로킹 I/O 용. 기본 최대 64 개까지 늘어남.
- **`Dispatchers.Main`**: 안드로이드/UI 용. 서버에서는 거의 안 씀.

```kotlin
suspend fun loadProfile(userId: Long): Profile = coroutineScope {
    val basic = async(Dispatchers.IO) { repository.find(userId) }
    val score = async(Dispatchers.Default) { scoring.calculate(userId) }
    Profile(basic.await(), score.await())
}
```

여기서 중요한 사실은 이 두 디스패처 풀이 **JVM 프로세스당 1 세트씩 공유** 라는 점입니다. 컨테이너 안의 모든 코루틴이 같은 `Dispatchers.IO` 64 개 슬롯을 나눠 쓰는 구조입니다. "내가 만든 코루틴이라 가벼울 거야" 라는 직관이 가장 자주 깨지는 지점입니다.

## 합계 — 8 코어 컨테이너 한 대의 이론치

세 풀이 각자 살아 있다는 사실을 숫자로 박아두면 감각이 잡힙니다. 8 코어가 할당된 컨테이너 한 대를 기준으로 정리합니다.

| 풀 | 기본 최대 | 비고 |
|---|---|---|
| Tomcat 요청 처리 | 200 | `server.tomcat.threads.max` |
| `@Async` (예시 설정) | 50 | `maxPoolSize=50` 일 때 |
| Coroutine `Dispatchers.Default` | 16 | `min(8 × 2, 128) = 16` |
| Coroutine `Dispatchers.IO` | 64 | 기본 상한 |
| **합계** | **약 330** | 모두 OS 네이티브 스레드 |

- 같은 호스트에 컨테이너를 두 대 올리면 산술적으로는 약 660 개의 OS 스레드가 한 박스 위에 살게 됩니다.
- 실제로는 동시에 다 안 채워지지만, **한 풀이 차오를 때 다른 풀은 멀쩡** 하다는 게 디버깅의 출발점입니다.
- 컨테이너 자원 제한(`cpus`, `pids_limit`)을 안 걸어두면, 풀 하나가 폭주할 때 옆 컨테이너가 같이 죽습니다.

## 그래서 어떻게 시작하는가

세 풀을 한 번에 튜닝하지 않습니다. 부하 테스트를 걸어두고 어느 풀이 먼저 차오르는지부터 봅니다.

- Tomcat 워커가 200 에 붙으면 → 동기 블로킹 호출(특히 DB · 외부 API)을 의심합니다.
- `@Async` 큐가 길어지면 → `corePoolSize` 와 `queueCapacity` 의 비율을 다시 봅니다.
- `Dispatchers.IO` 가 64 에 붙으면 → 코루틴 안에서 블로킹 I/O 를 쓰고 있지 않은지부터 점검합니다.

DB 는 멀쩡한데 응답이 느려진다면, 그건 셋 중 어느 한 풀이 차오르고 있다는 신호 입니다. 풀 크기는 곧 한도이고, 한도는 측정으로만 정해집니다.

총 스레드 수가 늘었다는 사실보다, 어느 풀이 막혔는지부터 측정합니다.
