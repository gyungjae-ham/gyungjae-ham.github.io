---
author: "luca"
pubDatetime: 2023-06-19T11:30:17+09:00
title: "의존성과 Testability — 테스트가 어렵다면 설계가 보내는 신호"
slug: "dependency-and-testability"
featured: false
draft: false
tags: ["testing", "dependency-injection", "architecture", "spring", "solid"]
description: "DI, DIP, 숨겨진 의존성, 그리고 Testability 의 본질을 5-6년차 시각으로 정리합니다. 테스트하기 어려운 코드는 보통 설계가 보내는 신호입니다."
---

> 2023-06 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 테스트 학습 시리즈의 두 번째 글이며, 이전 글 "개념, 대역" 에서 본 다섯 가지 테스트 대역이 왜 필요한지를 설계 관점에서 되짚는 자리입니다.

테스트를 짜다 보면 같은 회의가 반복됩니다. "이 메서드는 시간을 가지고 비교를 하는데, 테스트에서 시간을 어떻게 고정하죠?" "외부 API 호출이 들어가서 단위 테스트가 불가능합니다." 이런 대화에서 빠지기 쉬운 결론은 **"테스트가 어렵다"** 입니다. 그러나 더 정확한 결론은 다음과 같습니다.

> 테스트가 어렵다면, 그것은 보통 코드의 결함이 아니라 **설계가 보내는 신호** 입니다.

이 글은 그 신호를 읽는 어휘 — 의존성, DI, DIP, 그리고 Testability — 를 정리합니다.

## 의존성

> **의존성** 은 어떤 객체가 다른 객체의 함수나 데이터를 사용하는 상태를 의미합니다.

학습 노트로 더 풀어 적자면 다음 셋이 같은 의미입니다.

- "A 가 B 에 의존한다."
- "A 의 동작이 B 의 동작에 영향을 받는다."
- "B 가 바뀌면 A 의 테스트가 깨질 수 있다."

의존성 자체는 나쁜 것이 아닙니다. 어떤 시스템도 의존성 0 으로 동작하지 않습니다. 문제는 **의존성의 방향과 강도** 입니다. 시범 글 ("레이어드 아키텍처의 문제점과 해결책") 에서 짚은 fat service 의 본질은 결국 "도메인 로직이 인프라(JPA·메일·결제) 에 강하게 의존하고 있다" 였습니다.

### 강한 의존성의 신호

- **`new` 키워드로 협력자를 직접 생성** 하는 코드가 보일 때
- **정적 메서드 호출** 이 비즈니스 분기에 끼어들 때 (`LocalDateTime.now()`, `UUID.randomUUID()`)
- **싱글톤 객체** 의 상태를 직접 읽거나 변경할 때

이 셋이 보이면 그 코드는 **테스트를 쓰기 시작한 순간 막힙니다.** 테스트가 막히는 것은 단지 도구의 한계가 아니라, 협력자를 바꿔 끼울 자리가 없다는 설계상의 신호입니다.

## DI — 의존성 주입

> **DI(Dependency Injection)** 는 의존성을 약화시키는 기술입니다.

핵심은 단순합니다. 협력자를 **클래스 내부에서 만들지 않고 외부에서 받습니다.**

### Before — 협력자를 내부에서 생성

```kotlin
class Chef {
    private val bread = Bread()
    private val meat = Meat()

    fun makeBurger(): Burger = Burger(bread, meat)
}
```

- `Chef` 는 `Bread` 와 `Meat` 의 **구체 타입과 생성 방식** 까지 알고 있습니다.
- 테스트에서 다른 종류의 빵·고기로 바꿔 끼울 자리가 없습니다.
- `Bread` 의 생성자가 바뀌면 `Chef` 도 같이 바뀝니다.

### After — 협력자를 외부에서 주입

```kotlin
class Chef(
    private val bread: Bread,
    private val meat: Meat,
) {
    fun makeBurger(): Burger = Burger(bread, meat)
}
```

- `Chef` 는 협력자가 **어떻게 만들어지는지** 모릅니다.
- 테스트에서 `Chef(FakeBread(), FakeMeat())` 로 자유롭게 바꿔 끼울 수 있습니다.
- 생성 책임은 컨테이너(Spring) 또는 호출자에게 위임됩니다.

### 자주 오해되는 점

- **DI 는 의존성을 제거하지 않습니다.** 약화시킬 뿐입니다. `Chef` 는 여전히 `Bread` 와 `Meat` 의 존재를 알아야 합니다.
- **DI 는 프레임워크가 아니라 기법입니다.** Spring 없이도 생성자 파라미터만으로 가능합니다.
- **DI 의 본질은 "하드코딩 회피" 가 아닙니다.** 협력자를 **바꿔 끼울 수 있는 자리** 를 만드는 것입니다. 그 자리가 곧 테스트의 출입구이며, 다음 절의 `Testability` 와 직결됩니다.

## DIP — 의존성 역전 원칙

> **DIP(Dependency Inversion Principle)** 는 다음 두 줄로 요약됩니다.
>
> 1. 상위 모듈과 하위 모듈이 모두 **추상화에 의존** 해야 한다.
> 2. 추상화가 **세부 사항에 의존** 해서는 안 된다.

DI 와 자주 혼동됩니다. 둘은 다른 개념입니다.

| 구분 | DI (의존성 주입) | DIP (의존성 역전 원칙) |
|---|---|---|
| 정의 | 의존성을 외부에서 받는 기법 | 의존 방향에 대한 원칙 |
| 초점 | "누가 객체를 만드는가" | "누가 누구를 알아야 하는가" |
| 도구 | 생성자/세터 주입, DI 컨테이너 | 인터페이스, 추상 클래스 |
| 결과 | 협력자 교체 가능 | 도메인이 인프라를 모름 |

### 같이 적용되었을 때

DI 만 적용하면 다음 형태가 됩니다.

```kotlin
class OrderService(private val orderJpaRepository: OrderJpaRepository) { ... }
```

- 협력자를 외부에서 받기는 합니다.
- 그러나 `OrderService` 는 여전히 `OrderJpaRepository` 라는 **구체 타입(JPA)** 을 알고 있습니다.
- DIP 는 적용되지 않은 상태입니다.

DIP 까지 적용하면 다음 형태가 됩니다.

```kotlin
// 도메인 레이어
interface OrderRepository {
    fun findById(id: OrderId): Order?
    fun save(order: Order): Order
}

class OrderService(private val orderRepository: OrderRepository) { ... }

// 인프라 레이어
@Repository
class OrderJpaAdapter(
    private val orderJpaRepository: OrderJpaRepository,
) : OrderRepository { ... }
```

- `OrderService` 는 자신의 **도메인 레이어 인터페이스** 만 압니다.
- `OrderJpaAdapter` 가 그 인터페이스를 구현하면서 의존 방향이 **도메인 ← 인프라** 로 뒤집힙니다.
- 테스트에서는 `FakeOrderRepository` (이전 글 "개념, 대역" 에서 다룬 Fake) 로 자연스럽게 교체됩니다.

DI 는 "어떻게 객체를 받느냐" 의 문제이고, DIP 는 "그 받는 객체의 타입이 추상이냐 구체냐" 의 문제입니다. **DI 만으로는 충분하지 않습니다.**

## 숨겨진 의존성 — 가장 까다로운 종류

생성자나 파라미터로 들어오는 의존성은 **눈에 보이는 의존성** 입니다. 적어도 어디에 있는지는 보입니다. 더 까다로운 것은 코드 내부에서 **표면에 드러나지 않는 의존성** 입니다.

### 시간

```kotlin
class CertificationCode {
    fun isExpired(): Boolean = createdAt.plusMinutes(5).isBefore(LocalDateTime.now())
}
```

- `LocalDateTime.now()` 는 매 실행마다 다른 값을 돌려줍니다.
- 이 메서드를 테스트하려면 "현재 시각" 을 고정할 자리가 없습니다.
- 결국 `Thread.sleep` 같은 흉기를 끌어들이거나, 테스트가 비결정적으로 깨집니다.

**해결** — 시간을 의존성으로 외부에 노출시킵니다.

```kotlin
class CertificationCode(
    private val createdAt: LocalDateTime,
    private val clock: Clock,
) {
    fun isExpired(): Boolean =
        createdAt.plusMinutes(5).isBefore(LocalDateTime.now(clock))
}
```

- 테스트에서는 `Clock.fixed(...)` 로 시각을 원하는 값에 박아 둘 수 있습니다.
- 운영에서는 `Clock.systemDefaultZone()` 을 컨테이너가 주입합니다.

### 랜덤·UUID

```kotlin
val code = UUID.randomUUID().toString()
```

- 매번 다른 값입니다. 어떤 값을 기대해야 하는지 정할 수 없습니다.
- 테스트는 "값이 null 이 아니다" 정도밖에 검증할 수 없습니다.

**해결** — 코드 생성 책임을 인터페이스로 외부화합니다.

```kotlin
interface CodeGenerator {
    fun generate(): String
}

class UuidCodeGenerator : CodeGenerator {
    override fun generate(): String = UUID.randomUUID().toString()
}

class FixedCodeGenerator(private val value: String) : CodeGenerator {
    override fun generate(): String = value
}
```

테스트에서는 `FixedCodeGenerator("test-code")` 를 주입해 정확한 값을 기대값으로 박을 수 있습니다.

### 환경 변수·파일 경로

`System.getenv(...)`, `File("/etc/...")` 같이 코드 안에 박힌 경로도 같은 부류입니다. 인터페이스 + 주입으로 빼는 패턴이 공통적입니다.

원본 노트에 한 줄로 적었던 표현을 그대로 적자면 다음과 같습니다.

- **숨겨진 의존성** — `Clock.systemUTC()` 처럼 표면에 드러나지 않은 의존성
- **하드코딩된 값** — 파일 경로, 외부 시스템 식별자

이 둘이 보이는 곳마다 **테스트가 잡지 못하는 자리** 가 생깁니다.

## Testability — 진짜 정의

> **Testability** 는 얼마나 쉽게 **입력을 변경하고 출력을 검증** 할 수 있는가입니다.

이 한 줄에 본질이 다 담겨 있습니다.

- **입력 변경 용이성** — 협력자를 바꿔 끼울 수 있는가, 시간·랜덤·환경을 제어할 수 있는가.
- **출력 검증 용이성** — 결과가 반환값·상태로 드러나는가, 아니면 부수효과로만 알 수 있는가.

이 두 축이 무너진 코드는 다음 신호를 보냅니다.

- `@SpringBootTest` 없이는 테스트가 불가능합니다.
- 같은 테스트가 어떤 날은 통과하고 어떤 날은 깨집니다 (flaky test).
- 검증 코드가 `assertThat(result).isNotNull()` 수준에서 멈춥니다.

이 신호들이 모이면, 문제를 풀어야 할 곳은 테스트 코드가 아니라 SUT 의 설계입니다.

## 테스트 작성 조언 네 가지

원본 노트에 적었던 짧은 bullet 들을 5-6년차 시각으로 다시 풀어 적습니다.

### 1) Private 메서드는 테스트하지 않는다

```kotlin
class OrderService {
    fun placeOrder(request: PlaceOrderRequest): OrderId { ... }
    private fun validate(request: PlaceOrderRequest) { ... }
}
```

`validate(...)` 만 따로 테스트하고 싶어지는 순간이 있습니다. 그러나 private 메서드를 직접 테스트하려면 리플렉션을 끌어들이거나 접근 제어자를 풀어야 합니다. 둘 다 좋은 길이 아닙니다.

**더 좋은 결론은 다음 둘 중 하나입니다.**

- public 메서드를 통한 행위 검증으로 충분하다 → 그대로 둡니다.
- private 메서드의 책임이 충분히 크다 → 별도 클래스로 분리해 public 으로 노출합니다.

"private 을 테스트하고 싶다" 는 욕구 자체가 **숨겨진 책임을 끌어내라는 신호** 입니다.

### 2) final 메서드 stubbing 피하기

`Mockito` 는 final 메서드도 stubbing 할 수 있지만 (`mockito-inline`), 그 자체로 "이 final 메서드를 가짜로 만들고 싶다" 는 욕구가 **설계 오류** 의 신호입니다. final 은 "이 동작은 바뀌지 않는다" 는 선언인데, 테스트에서 바꿔 끼우려 한다면 그 선언이 거짓이 되거나, SUT 가 그 메서드를 직접 부르지 말아야 한다는 뜻이 됩니다.

### 3) DAMP > DRY (테스트 한정)

운영 코드의 원칙은 **DRY(Don't Repeat Yourself)** 입니다. 같은 로직을 두 군데 두지 않습니다.

테스트 코드의 원칙은 다릅니다. **DAMP(Descriptive And Meaningful Phrases)** 가 더 우선합니다.

- 테스트는 **한 번 읽고 의도를 이해할 수 있어야** 합니다.
- 중복 제거를 위해 helper 메서드 5단계 깊이로 추상화하면, 테스트가 깨졌을 때 흐름을 다시 따라가는 데 시간이 두 배로 듭니다.
- 같은 fixture 가 세 번 반복되는 편이, 그것을 한 helper 로 추상화해 의도를 가리는 것보다 낫습니다.

다만 fixture 생성·검증 보조 같은 일부 영역은 helper 로 묶는 것이 가독성에도 좋습니다. **"이 helper 가 의도를 드러내는가, 가리는가"** 가 기준입니다.

### 4) 테스트에 논리 로직을 넣지 않는다

```kotlin
@Test
fun `여러 사용자 즐겨찾기 토글`() {
    val users = (1..5).map { User(id = UserId(it.toLong()), bookmarked = false) }
    for (user in users) {
        user.toggleBookmark()
        assertThat(user.bookmarked).isEqualTo(it % 2 == 1)
    }
}
```

- `for` 와 `if` 가 테스트 안에 들어와 있습니다.
- 테스트가 통과해도 **테스트 코드 자체에 버그가 있을** 가능성이 생깁니다.

`@ParameterizedTest` 또는 같은 케이스를 명시적으로 펼친 별도 테스트로 옮기는 편이 안전합니다.

```kotlin
@ParameterizedTest
@MethodSource("toggleCases")
fun `즐겨찾기 토글 결과`(initial: Boolean, expected: Boolean) {
    val sut = User(id = UserId(1), bookmarked = initial)
    sut.toggleBookmark()
    assertThat(sut.bookmarked).isEqualTo(expected)
}
```

테스트가 검증하는 것은 SUT 의 로직이지, 테스트 코드 자체의 로직이 아닙니다.

## 함정 — DI 가 안티패턴이 되는 순간

DI 와 DIP 가 답이라고 해서, 모든 협력자를 인터페이스로 빼야 한다는 뜻은 아닙니다. 자주 보이는 함정 둘입니다.

### 함정 1 — 1:1 인터페이스 남발

`OrderService` 의 협력자가 `OrderRepository`, `OrderValidator`, `OrderEventPublisher`, `OrderNumberGenerator` 등으로 흩어지고, 각각의 구현체는 **단 하나** 인 상태가 종종 보입니다. 이 경우 인터페이스는 **추상화가 아니라 그냥 한 겹의 껍데기** 가 됩니다.

판단 기준은 단순합니다.

- 구현체가 **둘 이상이 될 가능성** 이 있는가 (테스트 Fake 포함)
- 협력자가 **외부 시스템 경계** 를 넘는가 (DB · API · 메시지큐 등)

이 둘 중 하나라도 해당하지 않으면 인터페이스를 굳이 만들 필요가 없을 수 있습니다.

### 함정 2 — 생성자 파라미터 폭발

DI 를 잘 적용하면 생성자 파라미터가 자연스럽게 늘어납니다. 그런데 6개를 넘기 시작하면, 그것 자체가 **SUT 의 책임이 너무 많다** 는 신호입니다. 시범 글의 `OrderService` 가 정확히 그 예입니다. 답은 더 많은 의존성을 받는 것이 아니라 **도메인 메서드로 책임을 옮기는 것** 입니다.

## 신호를 신호로 읽는 연습

이 글 전체를 한 줄로 압축하자면 다음과 같습니다.

- **"이 코드는 테스트하기 어렵다"** 는 감각은 거의 항상 **설계가 보내는 신호** 입니다.
- 그 신호를 잡는 어휘가 **의존성·DI·DIP·숨겨진 의존성** 입니다.
- 신호를 잡았을 때의 처방은 보통 **"테스트 도구를 더 정교하게 쓰는 것"** 이 아니라 **"의존 방향을 다시 그리는 것"** 입니다.

## 정리

- **의존성** 은 "다른 객체의 함수를 쓰는 상태" 입니다. 강한 의존성의 신호 — `new`, 정적 메서드, 싱글톤 직접 호출 — 를 익혀 둡니다.
- **DI** 는 협력자를 외부에서 받는 기법이며, **DIP** 는 도메인이 인프라가 아니라 추상에 의존하게 하는 원칙입니다. 둘은 다른 개념이고, 함께 가야 효과가 납니다.
- **숨겨진 의존성** (시간·랜덤·환경) 은 가장 까다로운 종류이며, 인터페이스로 외부화하는 것이 일반적인 해법입니다.
- **Testability** 는 "입력 변경 용이성 + 출력 검증 용이성" 입니다.
- 테스트 작성 시에는 **private 직접 테스트 회피, final stubbing 피하기, DAMP > DRY, 논리 로직 제거** 의 네 가지를 기억합니다.

다음 글에서는 이 어휘를 들고 Repository / Service / Controller 각 레이어를 어떻게 테스트하는지, 그리고 시범 글의 fat service 예시를 어디까지 끌어내릴 수 있는지를 코드로 정리합니다.
