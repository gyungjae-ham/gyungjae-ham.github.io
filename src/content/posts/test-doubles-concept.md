---
author: "luca"
pubDatetime: 2023-06-19T00:00:52+09:00
title: "개념, 대역 — 테스트가 빌려 쓰는 가짜들"
slug: "test-doubles-concept"
featured: false
draft: false
tags: ["testing", "test-double", "mock", "stub", "fake"]
description: "SUT, BDD, 상태 검증과 행위 검증, 그리고 Dummy·Fake·Stub·Mock·Spy 다섯 가지 테스트 대역을 5-6년차 시각으로 다시 정리합니다."
---

> 2023-06 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 테스트 학습 시리즈의 첫 글이며, 이후 글은 "의존성과 Testability", "레이어별 테스트", 그리고 "레이어드 아키텍처의 문제점과 해결책" 으로 이어집니다.

테스트를 처음 배울 때는 `Mockito` 의 `when(...).thenReturn(...)` 한 줄이면 모든 것이 풀리는 듯 보입니다. 그러나 어느 순간 같은 mock 이 글 곳곳에 반복 등장하고, 테스트가 깨질 때마다 `verify(...)` 가 실제 동작이 아니라 "내가 적어둔 호출 약속" 만 검증하고 있다는 사실을 마주하게 됩니다. 이 지점에서 필요한 것은 더 정교한 mock 사용법이 아니라 **테스트 대역(Test Double) 의 종류와 역할** 을 한 번 정리하는 일입니다.

## 용어 정리부터 — SUT 와 BDD

테스트 글을 읽다 보면 `SUT`, `BDD`, `given-when-then` 같은 약어가 전제처럼 깔려 있습니다. 출처가 흔들리지 않게 먼저 짚고 갑니다.

### SUT (System Under Test)

> **SUT** 는 테스트의 대상이 되는 시스템·객체·함수를 가리키는 용어입니다.

학습 노트로 적자면 다음과 같습니다.

- 단위 테스트라면 SUT 는 보통 **하나의 클래스 또는 함수** 입니다.
- 통합 테스트라면 SUT 는 **여러 컴포넌트가 묶인 모듈** 일 수 있습니다.
- 테스트 코드 안에서 변수명을 `sut` 로 두면 "이 변수가 검증 대상이다" 라는 의도가 그대로 드러납니다.

```kotlin
@Test
fun `즐겨찾기 토글 시 북마크 상태가 반전된다`() {
    // given
    val sut = User(id = UserId(1), bookmarked = false)

    // when
    sut.toggleBookmark()

    // then
    assertThat(sut.bookmarked).isTrue()
}
```

`sut` 라는 이름 하나로 "여기가 검증 대상이고, 나머지는 협력자다" 가 분리됩니다. 협력자 변수와 한눈에 구분되는 효과가 있습니다.

### BDD (Behaviour Driven Development)

> **BDD** 는 "어디에서 무엇을 테스트할지" 를 행위(behavior) 관점으로 정렬하는 접근입니다.

핵심은 `given-when-then` 세 단계입니다.

- **given** — 테스트의 사전 조건. 객체 상태, 입력 데이터, 협력자 설정.
- **when** — 검증하고 싶은 행위. SUT 의 메서드 호출 한 번이 이상적입니다.
- **then** — 기대 결과. 상태 검증 또는 행위 검증.

이 세 줄을 주석으로라도 적어두면 테스트가 길어졌을 때도 흐름이 사라지지 않습니다. 시리즈의 뒤쪽 글 ("레이어별 테스트") 에서 controller/service/repository 각각의 테스트가 동일하게 이 골격을 따르는 것을 보게 됩니다.

## 검증 방식 — 상태 vs 행위

테스트가 "무엇을" 검증하느냐에 따라 두 가지 결로 나뉩니다.

### State-Based Verification (상태 검증)

입력을 넣고 SUT 의 **출력 또는 상태 변화** 를 기대값과 비교합니다.

```kotlin
@Test
fun `재고가 차감되어 0이 된다`() {
    val product = Product(stock = 1)
    product.decreaseStock(1)
    assertThat(product.stock).isEqualTo(0)
}
```

- 검증 대상은 **결과** 입니다. 어떤 경로로 도달했는지는 묻지 않습니다.
- 리팩토링에 강합니다. 내부 구현이 바뀌어도 결과만 같으면 통과합니다.

### Behaviour-Based Verification (행위 검증)

SUT 가 협력자의 **어떤 메서드를** 호출했는지를 검증합니다.

```kotlin
@Test
fun `결제 성공 시 알림이 발송된다`() {
    val notifier: Notifier = mock()
    val sut = OrderService(notifier = notifier)

    sut.placeOrder(request)

    verify(notifier).notify(any())
}
```

- 검증 대상은 **상호작용** 입니다. "이 협력자에게 이런 명령을 내렸는가" 가 핵심입니다.
- 부수효과(이메일 발송, 큐 적재) 처럼 상태로 확인하기 어려운 행위에 유용합니다.
- 다만 **구현에 결합** 됩니다. SUT 의 내부 호출 방식을 바꾸면 테스트가 깨집니다.

### 어느 쪽을 먼저 잡아야 하나

| 상황 | 권장 검증 |
|---|---|
| 도메인 메서드의 결과·상태 변화 | 상태 검증 |
| 부수효과가 본질인 행위 (발송·적재·로깅) | 행위 검증 |
| 협력자 호출 횟수가 의미를 가질 때 (캐시 hit, 재시도) | 행위 검증 |
| 그 외 — 가능하면 | 상태 검증 |

행위 검증은 강력하지만 과용하면 **테스트가 SUT 의 구현을 베껴 적은 또 하나의 사본** 이 됩니다. 시리즈의 "의존성과 Testability" 글에서 같은 주제를 다른 각도로 다시 짚습니다.

### Interaction Test 의 함정

> "Interaction Test 는 캡슐화 원칙을 위배한다는 의견이 있습니다."

원본 노트에 한 줄로 적혀 있던 이 문장은 학습용 메모지만, 운영에서도 그대로 유효합니다. `verify(sut).markModified()` 같은 호출은 SUT 의 내부 메서드 호출까지 들여다보고 있기 때문에, 그 메서드의 이름만 바뀌어도 테스트가 깨집니다. 보통은 **결과로 같은 것을 확인할 길** 이 있는지 먼저 살핍니다.

## Test Fixtures — 사전 조건의 재사용

> **Test Fixture** 는 테스트 실행에 필요한 자원(객체·데이터·외부 환경) 을 미리 마련해 두는 절차를 가리킵니다.

JUnit5 기준으로 가장 흔한 형태입니다.

```kotlin
class OrderServiceTest {
    private lateinit var sut: OrderService
    private lateinit var fakeOrderRepository: FakeOrderRepository

    @BeforeEach
    fun setUp() {
        fakeOrderRepository = FakeOrderRepository()
        sut = OrderService(orderRepository = fakeOrderRepository)
    }

    @Test
    fun `주문 저장 후 ID 로 다시 조회할 수 있다`() {
        val saved = sut.place(orderOf(quantity = 1))
        assertThat(fakeOrderRepository.findById(saved.id)).isNotNull()
    }
}
```

- `@BeforeEach` 가 각 테스트 직전에 fixture 를 새로 만들어 **테스트 간 격리** 를 보장합니다.
- 객체 fixture 는 `@BeforeEach` 가, DB fixture 는 `@Sql` 또는 별도 helper 가 흔히 맡습니다.

운영 관점에서 한 가지 더 보태자면, fixture 를 한 곳에 모아 두는 `ObjectMother` 또는 `TestFixture` 객체를 두는 패턴이 5-6년차 코드베이스에서 자주 나타납니다. `orderOf(quantity = 1)` 같은 짧은 헬퍼 한 줄로 테스트의 의도를 살리고, 도메인 객체 생성에 필요한 보일러플레이트를 가립니다.

## Beyoncé Rule — 지키고 싶다면 테스트로 박아라

> "유지하고 싶은 상태나 정책이 있다면, 그에 대한 테스트를 능동적으로 만들어 두어야 한다."

Google 의 "Software Engineering at Google" 에 등장하는 표현입니다. 이름이 강렬해서 기억하기 좋습니다. 학습 노트의 결을 살려 한 줄로 적자면 다음과 같습니다.

- **테스트로 박아둔 것만 보호받는다.** 컨벤션 문서나 PR 리뷰는 시간이 지나면 약해지지만, CI 가 빨갛게 떨어지는 테스트는 매번 강제됩니다.
- 도메인 규칙이나 API 호환성, 성능 SLO 같은 "지키고 싶은 것" 은 가능한 한 테스트 코드로 옮겨야 합니다.

## Test Doubles — 다섯 가지 대역

여기가 이 글의 본론입니다. **Test Double** 은 실제 의존성을 대신해 테스트에서만 쓰이는 가짜 객체의 총칭입니다. Gerard Meszaros 가 정리한 분류가 가장 많이 쓰이며, 다섯 가지로 나뉩니다.

### 1) Dummy — 자리만 채운다

호출되지 않을 의존성을 **단지 컴파일을 통과시키기 위해** 넘기는 객체입니다.

```kotlin
class DummyNotifier : Notifier {
    override fun notify(message: String): Unit =
        throw NotImplementedError("호출되지 않아야 합니다")
}
```

- 동작이 없습니다. 호출되면 오히려 실패를 던지는 편이 의도를 더 분명히 드러냅니다.
- 생성자 파라미터 자리만 채우는 용도에 한정합니다.

### 2) Fake — 진짜처럼 동작하는 가벼운 구현

운영용 의존성과 **같은 인터페이스** 를 두고, 단순화된 동작을 들고 있는 객체입니다. 시범 글 ("레이어드 아키텍처의 문제점과 해결책") 의 `FakeOrderRepository` 가 정확히 이 형태입니다.

```kotlin
class FakeOrderRepository : OrderRepository {
    private val store = mutableMapOf<OrderId, Order>()
    override fun findById(id: OrderId): Order? = store[id]
    override fun save(order: Order): Order = order.also { store[it.id] = it }
}
```

- `HashMap` 기반이지만 운영용 `OrderJpaAdapter` 와 같은 인터페이스를 만족합니다.
- 테스트가 DB 없이 실제 흐름을 검증할 수 있게 합니다.
- 로컬 개발 환경에서도 그대로 쓸 수 있는 경우가 많습니다 (in-memory mode).

### 3) Stub — 미리 정한 값만 돌려준다

호출에 대해 **고정된 반환값** 을 주는 객체입니다. 외부 시스템처럼 결과를 만들기 어려운 의존성에 자주 씁니다.

```kotlin
class StubExchangeRate(private val rate: BigDecimal) : ExchangeRateProvider {
    override fun rateOf(currency: Currency): BigDecimal = rate
}
```

- 행위가 단순합니다. **입력에 무관하게 같은 값** 을 주거나, 입력별 매핑이 미리 정의됩니다.
- 검증은 SUT 의 결과로 합니다. Stub 자체가 호출되었는지를 묻지 않습니다.

`Mockito` 의 `when(...).thenReturn(...)` 한 줄로 만든 객체도 분류상으로는 stub 입니다. 도구가 무엇이든 **반환값만 정해두면 stub** 입니다.

### 4) Mock — 호출을 스스로 검증한다

기대했던 호출이 실제로 일어났는지를 **객체 스스로 확인** 하는 형태입니다.

```kotlin
@Test
fun `결제 성공 시 알림 1회 발송`() {
    val notifier: Notifier = mock()
    val sut = OrderService(notifier = notifier)

    sut.placeOrder(request)

    verify(notifier, times(1)).notify(any())
}
```

- 행위 검증의 주력 도구입니다.
- "어떤 메서드가 몇 번 호출되었는가" 가 검증의 핵심이 됩니다.
- 과용하면 SUT 의 내부 흐름을 베껴 적게 되니, **부수효과가 본질인 경우에 한정** 하는 편이 안전합니다.

### 5) Spy — 호출을 기록한다

실제 객체를 감싸 호출 정보를 **기록** 해 두는 형태입니다. 호출 후 검증은 따로 합니다.

```kotlin
class SpyNotifier : Notifier {
    val sent: MutableList<String> = mutableListOf()
    override fun notify(message: String) { sent += message }
}
```

- mock 과 비슷하지만, 검증 시점이 더 자유롭습니다.
- `Mockito.spy(realObject)` 처럼 실제 객체를 감싸면 일부 메서드는 진짜로, 일부는 stub 으로 쓸 수 있습니다. 다만 이 사용법은 복잡해지기 쉬워 권장 빈도가 낮습니다.

### 한눈에 비교

| 종류 | 동작 유무 | 반환값 | 검증 방식 | 대표 용도 |
|---|---|---|---|---|
| **Dummy** | 없음 | 호출 시 실패 권장 | 검증 안 함 | 파라미터 자리 채우기 |
| **Fake** | 단순화된 진짜 | 입력에 따라 진짜 동작 | 상태 검증 | DB·외부 시스템 대체 |
| **Stub** | 없음 | 고정값 | 상태 검증 | 외부 응답 흉내 |
| **Mock** | 없음 | 미리 정해진 값 또는 기본값 | 행위 검증 (자가) | 부수효과 검증 |
| **Spy** | 있음 (선택적) | 진짜 또는 stub | 행위 검증 (사후) | 호출 기록 추적 |

## 운영에서 자주 빠지는 함정

5-6년차 시각으로 추가하자면, 대역의 종류를 아는 것보다 **어느 자리에 어떤 대역을 쓰는지** 가 더 중요합니다. 자주 보이는 함정 셋입니다.

### 함정 1 — 모든 의존성을 mock 으로 처리

새 테스트를 짤 때 `@MockBean` 또는 `mock()` 으로 협력자를 전부 가짜로 만들면, 결국 테스트가 **SUT 의 호출 시퀀스를 베껴 적은 사본** 이 됩니다. 도메인 협력자는 **Fake** 로, 진짜 외부 시스템(메일·결제·푸시) 만 **Stub/Mock** 으로 처리하는 결이 일반적으로 더 건강합니다.

### 함정 2 — Stub 으로 검증

stub 으로 만든 객체에 `verify(...)` 를 거는 코드가 종종 보입니다. 이 경우 stub 의 정체는 사실 mock 입니다. "반환값 흉내" 와 "호출 검증" 은 다른 책임이라는 점만 분명히 해두면 의도 표현이 깔끔해집니다.

### 함정 3 — Fake 의 무한 확장

`FakeOrderRepository` 가 점점 자라 트랜잭션·인덱스·페이징까지 흉내내기 시작하면, 어느 순간 운영 코드 못지않게 복잡해집니다. Fake 는 "운영 동작의 본질만 옮긴 가벼운 구현" 으로 유지하고, 진짜에 가까운 검증이 필요한 영역은 `@DataJpaTest` 같은 통합 테스트로 옮기는 편이 낫습니다. 이 경계는 다음 글 "레이어별 테스트" 에서 더 다룹니다.

## 신호로 다시 읽기

테스트 대역의 분류는 결국 **"이 협력자를 어떻게 다룰까"** 라는 결정의 어휘입니다. SUT 가 협력자 6개를 `mock()` 으로 둘러싸야만 짜이는 상태라면, 그것은 대역의 문제가 아니라 **SUT 의 의존성이 너무 많다는 신호** 입니다. 다음 글 ("의존성과 Testability") 에서 이 신호를 읽는 법을 더 구체적으로 다룹니다.

## 정리

- **SUT** 는 테스트의 검증 대상이고, **BDD given-when-then** 은 그 검증의 골격입니다.
- 검증은 **상태** 와 **행위** 로 나뉘며, 기본은 상태 검증, 부수효과가 본질인 경우에 한해 행위 검증을 씁니다.
- **Test Double** 은 다섯 가지 — Dummy/Fake/Stub/Mock/Spy — 로 분류되며, 자리에 맞춰 골라 써야 합니다.
- **Beyoncé Rule** 이 알려주는 것은 단순합니다. 지키고 싶다면, 테스트로 박아 두어야 합니다.

다음 글에서는 의존성이 Testability 에 어떤 영향을 미치는지, 그리고 "테스트가 어렵다" 는 감각이 사실은 설계가 보내는 신호임을 더 자세히 짚습니다.
