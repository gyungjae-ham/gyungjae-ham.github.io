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
description: "Tomcat 200 개를 잡아두면 끝일 줄 알았는데, 실은 @Async 풀과 Coroutine Dispatchers 풀이 각자 따로 살고 있습니다. 세 풀이 어디서 차오르는지를 APM 지표로 짚어보고, CPU bound · IO bound 별 풀 크기 잡는 결정 트리를 정리합니다."
---

> 2024-12 에 정리한 tistory 글을 5~6년차 시각으로 다시 손본 글입니다. 그때는 "Tomcat 풀 크기를 얼마로 잡을까" 가 질문이었는데, 지금 다시 들여다보면 같은 자리에서 묻는 질문이 바뀌어 있습니다. "어느 풀이 먼저 차오르는지 보고 있는가" 가 더 앞에 와야 했다는 것을 운영을 거치고 보면 알게 됩니다.

배포 직전에 가장 많이 던지는 질문은 `server.tomcat.threads.max` 를 얼마로 잡을지였습니다. 그 자리에서 한 번 더 들여다보면, Tomcat 풀 옆에 `@Async` 의 `ThreadPoolTaskExecutor` 와 Kotlin Coroutine 의 `Dispatchers.IO`·`Dispatchers.Default` 가 같이 살고 있습니다.

세 풀은 서로의 크기를 모르는데 컨테이너 cgroup CPU 한도는 한 줄입니다. 그 합을 의식하지 않으면 어느 한 풀이 차오른 자리에서 엉뚱한 풀의 크기를 만지게 됩니다.

## 세 풀이 한 박스 안에 같이 살아 있다는 사실

8 코어 컨테이너 한 대를 기준으로 세 풀의 이론치를 박아 두겠습니다. 숫자를 한 번 보면 "Tomcat 200 만 잡으면 끝" 이 아니라는 사실이 명확해집니다.

| 풀 | 기본 최대 | 비고 |
|---|---|---|
| Tomcat 요청 처리 | 200 | `server.tomcat.threads.max` |
| `@Async` (예시 설정) | 50 | `maxPoolSize=50` 일 때 |
| Coroutine `Dispatchers.Default` | 16 | `min(8 × 2, 128) = 16` |
| Coroutine `Dispatchers.IO` | 64 | 기본 상한 |
| **합계** | **약 330** | 모두 OS 네이티브 스레드 |

세 풀 모두 JVM 가상 객체가 아니라 OS 네이티브 스레드와 1:1 매핑됩니다. 컨테이너 위의 리눅스 커널이 실제로 스케줄링하는 스레드라는 뜻이고, cgroup CPU 한도 안에서 같이 압박을 만들어냅니다. 한 풀이 차오를 때 다른 풀은 멀쩡하다는 게 디버깅의 출발점이지만, **풀이 차오를 때 보이는 증상의 결이 셋이 서로 다르다** 는 사실을 먼저 봐야 합니다. 그래서 운영에서 가장 먼저 묻는 질문은 풀 크기가 아니라 "지금 어느 풀이 빨갛게 떴는가" 가 됩니다.

## Tomcat 풀이 차오를 때 보이는 신호

Tomcat 워커는 한 요청을 받으면 응답이 나갈 때까지 그 스레드를 통째로 점유합니다. JDBC·외부 API 동기 호출이 끼면 그 시간만큼 워커가 묶입니다. 200 이라는 숫자는 동시에 처리 가능한 HTTP 요청의 상한이고, 그 위로 들어오는 요청은 `acceptCount` 큐에 쌓이거나 거부됩니다.

운영에서 이 풀이 차오르는 자리는 다음 지표에서 동시에 떠오릅니다.

- **Spring Boot Actuator** `tomcat.threads.busy` 가 `tomcat.threads.config.max` 근처에 붙음
- **APM (Datadog · NewRelic · Pinpoint)** 의 request queue depth 가 비어 있다가 급등
- **응답 시간 분포** 가 p50 은 멀쩡한데 p99 만 폭증 — 큐잉 latency 가 끼는 모양

그 자리에서 가장 자주 확인되는 원인은 워커가 외부 호출이나 DB 를 동기로 기다리느라 점유 시간이 길어진 경우입니다. 풀 크기를 200 에서 400 으로 올려서 증상은 잠시 가라앉아도, **풀 크기를 키우는 게 답이 아니라 점유 시간을 줄이는 게 답인 자리** 가 대부분입니다. DB 커넥션 풀이 10 개인데 Tomcat 워커가 400 개라면 워커 390 개가 커넥션을 기다리며 묶이는 모양이 됩니다.

## @Async 풀과 곁가지의 본가지화

`@Async` 가 붙은 메서드는 Tomcat 워커가 아니라 별도의 `ThreadPoolTaskExecutor` 빈에 위임됩니다. 메일 발송·알림·비동기 로깅 같은 곁가지 작업을 메인 흐름에서 떼어내려는 것이 본 의도입니다.

```kotlin
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
```

이 풀의 동작 결을 한 번 짚고 가야 합니다. `corePoolSize` 만큼은 상시 살아 있고, 부하가 오르면 `queueCapacity` 가 먼저 차고 그 다음에 `maxPoolSize` 까지 늘어납니다. 큐를 크게 잡으면 부하가 와도 스레드는 늘지 않고 응답 latency 만 길어집니다. 그러고는 큐가 끝까지 차면 `RejectedExecutionException` 으로 떨어집니다.

이 풀이 차오르는 신호는 `executor.active`·`executor.queued` Actuator metric 에서 떠오릅니다. **`executor.queued` 가 지속적으로 0 이 아니면** 곁가지가 본가지를 압박하기 시작했다는 신호입니다. 알림이 30 초 늦게 도착하거나 비동기 로깅이 spike 치는 자리가 여기서 나옵니다.

## Coroutine Dispatchers — 가벼울 거라는 직관의 함정

Kotlin 코루틴은 코드 위에서는 가볍지만, 실행되는 곳은 OS 스레드 위입니다. 그 "스레드 위" 가 어느 풀이냐는 디스패처가 결정합니다. `Dispatchers.Default` 는 CPU 바운드 작업용으로 `min(코어 수 × 2, 128)`, `Dispatchers.IO` 는 블로킹 I/O 용으로 기본 최대 64 개까지 늘어납니다.

```kotlin
suspend fun loadProfile(userId: Long): Profile = coroutineScope {
    val basic = async(Dispatchers.IO) { repository.find(userId) }
    val score = async(Dispatchers.Default) { scoring.calculate(userId) }
    Profile(basic.await(), score.await())
}
```

여기서 잘 깨지는 직관 두 가지입니다. 두 디스패처 풀이 **JVM 프로세스당 1 세트씩 공유** 라는 점이 첫째입니다. 컨테이너 안의 모든 코루틴이 같은 64 슬롯을 나눠 쓰니, "내가 만든 코루틴이라 가벼울 거야" 라는 직관이 가장 자주 깨지는 자리입니다. 둘째, `Dispatchers.IO` 가 64 슬롯에 붙는 신호는 외부 호출 timeout 증가와 함께 옵니다. 평소 200ms 로 끝나던 외부 API 가 갑자기 5 초씩 걸리기 시작하는 자리, 그게 IO 슬롯이 모자라거나 한 슬롯이 너무 오래 묶여 있다는 신호입니다.

운영 시점에는 `kotlinx.coroutines.debug` 로 활성 코루틴 트리를 떠 보거나, `Dispatchers.IO.limitedParallelism(N)` 으로 슬롯 점유를 도메인별로 갈라 두는 게 안전합니다. 한 도메인의 외부 호출 지연이 다른 도메인까지 끌고 들어가지 않게 분리하는 결입니다.

## CPU bound · IO bound · mixed 의 결정 트리

세 풀 모두 크기를 잡을 때의 결정 트리가 결국 같은 결입니다. 작업의 모양이 CPU bound 인지 IO bound 인지 mixed 인지를 먼저 봅니다.

- **CPU bound** — 영상 인코딩·해시·직렬화. 풀 크기 ≈ 할당된 코어 수 부근. 코어보다 크게 잡으면 컨텍스트 스위치 비용으로 처리량이 오히려 떨어집니다.
- **IO bound** — DB·외부 API·파일 I/O. 풀 크기 ≈ 동시 대기 가능한 외부 응답 수. 외부 호출 평균 latency × 초당 요청 수가 출발점입니다.
- **Mixed** — 일반 웹 요청. IO 비중에 가중치를 두되, 풀 크기 합이 cgroup CPU 한도를 의식하는 한도 안에 들어가야 합니다.

다만 cgroup 8 코어 컨테이너에서 330 개의 스레드가 동시에 RUNNABLE 이 되면, 8 코어가 330 스레드를 돌리는 모양이 됩니다. 한 스레드가 CPU 를 받는 시간이 짧아지고 컨텍스트 스위치 비용이 폭증합니다. 풀 크기의 합은 CPU 한도와 짝으로 본다는 의식이 결국 같은 결의 결정 트리입니다.

## 컨테이너 두 대가 한 호스트 위에 있을 때

같은 호스트에 같은 컨테이너를 두 대 올리면 산술적으로는 약 660 개의 OS 스레드가 한 박스 위에 살게 됩니다. 실제로는 동시에 다 채워지지 않지만, 한 풀이 폭주하면 옆 컨테이너까지 같이 느려지는 자리가 여기서 나옵니다. 쿠버네티스 환경에서는 Pod 의 `resources.requests.cpu` 와 `limits.cpu` 가 이 합산을 통제하는 자리입니다.

이건 같은 결의 **Bulkhead 패턴** 입니다. DB 커넥션 풀을 도메인별로 갈라 두는 결, `Dispatchers.IO.limitedParallelism(N)` 으로 외부 호출을 분리하는 결, 컨테이너 단위로 `resources.limits` 를 거는 결 — 모두 "한 자원의 폭주가 옆 자원을 끌고 들어가지 않게" 라는 같은 의식입니다. DB connection pool 의 결정도 결국 같은 자리에 있습니다.

## 정리

세 풀을 한 번에 튜닝하지 않습니다. 부하 테스트를 걸어두고 `tomcat.threads.busy`·`executor.queued`·`kotlinx.coroutines.debug` 로 어느 풀이 먼저 차오르는지부터 봅니다. Tomcat 이 200 에 붙으면 동기 블로킹 호출을 의심하고, `@Async` 큐가 길어지면 곁가지의 SLA 를 다시 정의하고, `Dispatchers.IO` 가 64 에 붙으면 한 도메인이 IO 슬롯을 독점하지 않는지 봅니다.

DB 는 멀쩡한데 응답이 느려진다면 셋 중 어느 한 풀이 차오르고 있다는 신호이고, 풀 크기는 한도이고 한도는 합산으로 정해진다는 사실을 한 번 더 들여다봐야 합니다. 총 스레드 수가 늘었다는 사실보다, 어느 풀이 막혔는지부터 측정합니다.
