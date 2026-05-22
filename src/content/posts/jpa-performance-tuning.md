---
author: "luca"
pubDatetime: 2023-08-16T17:49:19+09:00
title: "JPA 성능 최적화 — batch_fetch_size 와 OSIV 의 진짜 의미"
slug: "jpa-performance-tuning"
featured: false
draft: false
tags: ["jpa", "performance", "n+1", "fetch-join", "batch-size", "osiv"]
description: "default_batch_fetch_size 와 OSIV 설정이 N+1 과 커넥션 풀에 미치는 영향을, 5-6년차 운영 시각으로 다시 정리."
---

> 2023-08 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 그때는 "이렇게 설정하면 빨라진다" 정도로 적었던 두 옵션의, 운영에서 보이는 진짜 의미를 함께 적었습니다.

지연 로딩이 깔린 도메인을 처음 운영에 올렸을 때, 한 화면 조회에서 쿼리가 200개씩 나가는 것을 본 적이 있습니다. APM 에서 빨갛게 표시되어 있었고, DB 의 active connection 은 평소의 5배였습니다. 이건 ORM 의 문제가 아니라 **연관 로딩 전략을 다시 들여다보라는 신호** 였습니다.

이 글은 `default_batch_fetch_size` 와 `OSIV` 두 옵션을 중심으로 풀어봅니다. 둘 다 한 줄 설정이지만, 의미를 모르고 켜면 운영에서 다른 식으로 터집니다.

## N+1 의 정체부터

먼저 N+1 이 무엇인지 짧게 정리하고 갑니다.

```kotlin
// 1) 회원의 주문을 N개 조회
val orders: List<Order> = orderRepository.findByUserId(userId)  // SELECT 1번

// 2) 각 주문의 주문 항목을 출력
for (order in orders) {
    val items = order.orderItems  // 지연 로딩 → SELECT N번
    log.info(items.toString())
}
```

쿼리가 `1 + N` 번 나가서 N+1 입니다. 주문이 100건이면 쿼리는 101번. 이게 무서운 이유는 **로컬에서는 데이터 1~2건으로 테스트하기 때문에 안 보이고, 운영에서 폭발한다**는 점입니다.

해결책은 크게 셋입니다.

- **`fetch join`** — JPQL 에 `join fetch` 명시. 한 번의 쿼리로 join.
- **`@EntityGraph`** — Repository 메서드에 attributePaths 선언. JPQL 안 건드림.
- **`default_batch_fetch_size`** — 일괄 `IN` 절로 묶어 조회. 쿼리 수를 `1 + ceil(N/size)` 로 줄임.

이 글에서는 세 번째에 집중합니다. 앞의 두 개는 별도 글에서 다룹니다.

## default_batch_fetch_size — IN 절로 묶기

설정은 한 줄입니다.

```yaml
# application.yml
spring:
  jpa:
    properties:
      hibernate:
        default_batch_fetch_size: 100
```

이 옵션을 켜면 Hibernate 가 지연 로딩 대상을 즉시 N번 조회하지 않고, **이미 로딩된 부모 엔티티의 ID 를 모아 `IN` 절로 한 번에** 가져옵니다.

### Before / After

**적용 전 — N+1**

```sql
SELECT * FROM orders WHERE user_id = ?;          -- 1번
SELECT * FROM order_item WHERE order_id = ?;     -- order 1
SELECT * FROM order_item WHERE order_id = ?;     -- order 2
SELECT * FROM order_item WHERE order_id = ?;     -- order 3
-- ... order 개수만큼
```

**적용 후 — `IN` 묶음**

```sql
SELECT * FROM orders WHERE user_id = ?;                          -- 1번
SELECT * FROM order_item WHERE order_id IN (?, ?, ?, ..., ?);    -- 한 번에 묶음
```

쿼리 수가 `1 + N` → `1 + ceil(N / batch_size)` 로 줄어듭니다. `batch_size = 100`, `N = 1000` 이면 `1001 → 11` 번이 됩니다.

### batch_size 의 적정값

옛 글에는 "100~1000 사이를 권장" 으로만 적었는데, 실제로는 다음 기준으로 잡습니다.

| 고려 요소 | 영향 |
|---|---|
| DB 의 `IN` 절 한도 | Oracle 1000개, MySQL/PostgreSQL 은 더 큼 (실질 제약 적음) |
| 쿼리 plan cache | `IN` 절 파라미터 수가 자주 바뀌면 plan cache hit 률 하락 |
| 메모리 / 응답 시간 | size 가 크면 한 쿼리가 무거워져 P99 latency 가 튐 |
| 네트워크 round-trip | size 가 작으면 round-trip 이 늘어 전체 시간 증가 |

실무에서는 **100 으로 시작 → 부하 테스트에서 P95/P99 보며 조정**이 정석입니다. 무작정 1000 으로 두지 않습니다.

### 함정 — `@OneToOne` 과 페이징

이 옵션이 만능은 아닙니다.

- **`@OneToOne` 지연 로딩**은 `batch_fetch_size` 가 적용되지 않는 경우가 있습니다. nullable 한 `@OneToOne` 은 proxy 가 불가능하기 때문입니다. `optional = false` 로 명시하거나 양방향이면 mapped 쪽을 조회.
- **페이징 + `fetch join`** 의 함정 — `OneToMany` 컬렉션을 `fetch join` 하면 결과 row 가 카르테시안 곱으로 늘어, Hibernate 가 **메모리에서 페이징** 합니다 (`HHH000104` 경고). 이때는 `fetch join` 대신 `batch_fetch_size` 가 정답입니다.

## OSIV — 영속성 컨텍스트의 수명을 어디까지

`OSIV (Open Session In View)` 는 Spring Boot 기본값이 `true` 입니다.

```yaml
spring:
  jpa:
    open-in-view: true   # 기본값
```

이 한 줄이 무엇을 하는지 명확히 짚어야 합니다.

### `true` 일 때 — 컨트롤러 끝까지 세션 유지

- 영속성 컨텍스트가 **HTTP 응답이 클라이언트로 나가기 직전까지** 살아 있습니다.
- 결과: 컨트롤러에서 `order.orderItems` 같이 lazy 필드를 접근해도 `LazyInitializationException` 이 나지 않습니다.
- 비용: **DB 커넥션을 그만큼 오래 잡고 있습니다**.

### `false` 일 때 — 트랜잭션 종료 시점에 세션 종료

- 영속성 컨텍스트는 `@Transactional` 메서드 (보통 Service 레이어) 가 끝나는 순간 닫힙니다.
- 결과: 컨트롤러에서 lazy 필드를 접근하면 `LazyInitializationException` 폭발.
- 이득: **DB 커넥션을 빠르게 반환합니다**.

### 어느 쪽을 골라야 하는가

| 환경 | 권장 | 이유 |
|---|---|---|
| 학습·사이드 프로젝트 | `true` | 편함이 가치보다 큼 |
| 트래픽 낮은 사내 어드민 | `true` | 커넥션 부족 위험 거의 없음 |
| **실시간 API 서비스** | **`false`** | 커넥션 풀 부족이 곧 장애 |
| 마이크로서비스 (외부 호출 많음) | `false` | 외부 호출 동안 커넥션을 점유하면 풀 고갈 |

운영 서비스에서 `OSIV = true` 의 진짜 문제는 다음 시나리오입니다.

```
[Controller]
  └── [Service @Transactional 종료]    ← 여기서 끝나야 할 트랜잭션
        └── [외부 API 호출 3초]          ← 이 동안 DB 커넥션 점유 중
              └── [View 렌더링 / JSON 직렬화]
```

`OSIV = true` 면 외부 API 호출 3초 동안 DB 커넥션 1개가 점유됩니다. 동시 요청이 100개면 풀 100개가 묶입니다. **DB 는 멀쩡한데 서비스만 다운되는 장애** 가 여기서 나옵니다.

### `OSIV = false` 로 옮길 때의 비용

`false` 로 바꾸면 다음 작업이 따라옵니다.

- 컨트롤러에서 lazy 필드 접근 코드 모두 제거 → Service 에서 필요한 모양으로 미리 로딩.
- DTO 변환을 Service 레이어로 옮김 → 컨트롤러는 DTO 만 받습니다.
- N+1 이 표면화 됨 → `fetch join` · `@EntityGraph` · `batch_fetch_size` 조합 필요.

이 비용을 감수해야 하므로, 신규 프로젝트라면 **처음부터 `false`** 가 정답입니다. 기존 프로젝트는 점진적으로 옮기는데, 도메인 한 개씩 entity-to-dto 변환을 끌어올리는 작업이 됩니다.

## Kotlin 에서 자주 만나는 함정

JPA 를 Kotlin 에서 쓸 때 같이 보이는 함정 둘만 짚습니다.

### 1) `data class` 를 `@Entity` 로 쓰지 않는다

```kotlin
// 권장하지 않음
@Entity
data class Order(@Id val id: Long, ...)
```

- `data class` 는 `equals` / `hashCode` 를 모든 필드로 자동 생성합니다. lazy 필드가 끼면 `equals` 호출만으로 추가 쿼리가 나갑니다.
- `final` 클래스가 기본 → JPA proxy 가 불가능. `kotlin-allopen` 플러그인이 풀어주지만, `data class` 결 자체가 entity 와 안 맞습니다.

권장: `open class` + `kotlin-jpa` 플러그인.

```kotlin
@Entity
class Order(
    @Id @GeneratedValue val id: Long = 0,
    val userId: Long,
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    val orderItems: MutableList<OrderItem> = mutableListOf(),
)
```

### 2) `findById` 와 `getReferenceById` 의 차이

- `findById` — 즉시 SELECT. 없으면 `Optional.empty`.
- `getReferenceById` — proxy 만 반환. 접근 시점에 SELECT. 없으면 `EntityNotFoundException`.

연관 관계 설정용 (예: `order.user = userRepository.getReferenceById(userId)`) 이라면 `getReferenceById` 가 한 번의 SELECT 를 절약합니다. 옛 글에는 안 적었지만 실무에서 자주 씁니다.

## 그래서 어떻게 시작하는가

성능 튜닝의 출발점을 잡는다면 다음 순서가 현실적입니다.

1. **`spring.jpa.show_sql` 또는 p6spy 로 쿼리를 본다.** N+1 이 일어나는 자리가 식별되어야 시작합니다.
2. **`default_batch_fetch_size: 100` 켠다.** 가장 적은 비용으로 대부분의 N+1 을 잡습니다.
3. **`open-in-view: false` 로 옮길 계획을 세운다.** 신규 프로젝트면 즉시, 기존이면 도메인별 단계 적용.
4. **부하 테스트로 P95/P99 본다.** `batch_size` 조정은 여기서.
5. **APM (Datadog, NewRelic, Pinpoint) 으로 운영 모니터링.** 새로 추가되는 쿼리 패턴은 곧 N+1 의 후보입니다.

## 정리

`default_batch_fetch_size` 와 `OSIV` 는 한 줄짜리 설정이지만, 그 한 줄이 운영에서 의미하는 바는 완전히 다릅니다. 전자는 **쿼리 수의 신호**, 후자는 **커넥션 풀의 신호** 에 대응합니다. ORM 이 토해내는 쿼리 수와 DB 의 active connection 수, 두 지표를 보지 않고 ORM 을 튜닝하는 것은 어둠 속에서 칼을 휘두르는 것에 가깝습니다.

다음 글에서는 `fetch join` 과 `@EntityGraph` 의 사용 결을 좀 더 깊이 들여다보고, 컬렉션 페이징의 진짜 패턴 (no-offset / cursor) 을 정리합니다.
