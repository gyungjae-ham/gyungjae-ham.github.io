---
author: "luca"
pubDatetime: 2023-06-22T15:08:19+09:00
title: "레이어드 아키텍처의 문제점과 해결책"
slug: "layered-architecture-problems-and-solutions"
featured: false
draft: false
tags: ["architecture", "clean-architecture", "hexagonal", "spring", "testing"]
description: "테스트가 무거워지고 fat service 가 늘어나는 진짜 원인을 레이어드 아키텍처의 결함에서 짚고, 의존성 역전과 도메인-영속성 분리로 푸는 길을 정리합니다."
---

> 2023-06 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 원본의 짧은 메모를 그대로 옮기지 않고, 그때는 어렴풋했던 트레이드오프와 함정을 함께 적었습니다.

테스트가 점점 무거워지고 `@SpringBootTest` 가 빠질 자리가 없어지는 순간이 옵니다. 그때 `h2` 를 더 빠르게 만들거나 `Mockito` 를 더 정교하게 쓰는 길로 가기 쉬운데, 사실 이건 **코드의 문제가 아니라 아키텍처가 보내는 신호**입니다.

## 진단 — 테스트가 무거워지는 진짜 원인

운영 중인 프로젝트에서 다음 증상이 함께 나타난다면 신호가 명확합니다.

- **`h2` 가 빠진 테스트가 사실상 없다** — 모든 테스트가 `@SpringBootTest` 또는 `@DataJpaTest` 부터 시작합니다.
- **`Mockito` 없이는 단위 테스트가 불가능하다** — Service 가 너무 많은 협력자와 결합되어 있어 `Mockito` 가 없으면 isolation 자체가 안 됩니다.
- **`ElasticSearch`·`Kafka` 같이 임베디드 모드가 없는 의존성은 통합 테스트에서 mocking 으로만 가능** — 진짜 동작을 검증하지 못하고 mock 의 약속만 검증합니다.

이건 단지 도구의 한계가 아니라 **시스템이 RDB 와 외부 인프라에 강결합되어 있다는 신호**입니다. 정작 검증해야 할 도메인 로직이 인프라에 묶여 있어 분리된 검증이 불가능한 상태입니다.

## 레이어드 아키텍처의 진면목

### 장점 — 아직도 가장 많이 쓰이는 이유

- **시각적으로 명확합니다.** `controller / service / repository / entity` 폴더 구조만 봐도 누구나 흐름을 안다는 점은 큰 자산입니다.
- **유사 기능이 모여 있어 파악이 빠릅니다.** "이 도메인의 Service 가 어디 있지?" 가 0초 만에 풀립니다.
- **JPA + Spring 의 default 와 정확히 결이 맞습니다.** 프레임워크와 싸우지 않습니다.

이 셋이 합쳐져서 대다수 한국 백엔드 프로젝트의 출발점이 됩니다. 처음 잡기에는 합리적입니다.

### 단점 — 규모가 커지면 드러나는 결

**1) DB 주도 설계**

처음 도메인을 잡을 때 Entity 부터 그리게 됩니다. "User 테이블에 컬럼이 뭐가 있지?" 가 첫 질문이 되고, 정작 "이 도메인이 어떤 use case 를 풀어야 하는가" 는 뒤로 밀립니다. 결과적으로 코드가 **데이터의 모양** 에 맞춰지고, 비즈니스 규칙은 Service 한 메서드 안에 끼어 들어가게 됩니다.

**2) 동시 작업 제약**

- Entity 가 확정되어야 Repository 를 만들 수 있고
- Repository 가 있어야 Service 를 짤 수 있고
- Service 가 있어야 Controller 를 짤 수 있습니다.

결국 한 기능 = 한 사람 작업이 되기 쉽고, 위에서 아래로 직렬 흐름이 강제됩니다. 페어 작업이나 분담이 어려워집니다.

**3) 도메인 퇴화 (fat service)**

이게 가장 큰 함정입니다. 다음과 같은 코드를 자주 보게 됩니다.

```kotlin
@Service
class OrderService(
    private val orderRepository: OrderRepository,
    private val productRepository: ProductRepository,
    private val userRepository: UserRepository,
    private val mailSender: JavaMailSender,
    private val notificationClient: SlackClient,
    private val paymentClient: TossPaymentClient,
    // ...
) {
    @Transactional
    fun placeOrder(request: PlaceOrderRequest): OrderId {
        val user = userRepository.findById(request.userId) ?: throw UserNotFound()
        val product = productRepository.findById(request.productId) ?: throw ProductNotFound()
        if (product.stock < request.quantity) throw OutOfStock()
        if (user.balance < product.price * request.quantity) throw InsufficientBalance()
        product.stock -= request.quantity
        user.balance -= product.price * request.quantity
        val order = Order(userId = user.id, productId = product.id, quantity = request.quantity)
        orderRepository.save(order)
        mailSender.send(OrderConfirmationMail(user.email, order))
        notificationClient.notify("주문 발생: ${order.id}")
        paymentClient.charge(user.paymentMethod, product.price * request.quantity)
        return order.id
    }
}
```

이 메서드 하나에 **재고 차감 / 잔액 차감 / 주문 저장 / 메일 / 슬랙 / 결제** 가 모두 들어가 있습니다. 절차지향 코드이며, 도메인이 사라졌습니다. `placeOrder` 라는 비즈니스 행위는 어디에도 응집되어 있지 않고, Service 가 모든 협력자를 직접 부르며 흐름만 풀어내고 있을 뿐입니다.

이 코드를 단위 테스트하려면 6개 협력자를 모두 mocking 해야 하고, 통합 테스트하려면 모든 외부 시스템의 임베디드/스텁 환경이 필요해집니다. **테스트가 무거워지는 직접적 원인**이 여기에 있습니다.

## 개선의 결 — 의존성 역전과 도메인 분리

원본 글에서 "개선된 아키텍처" 라고만 적었던 길은 사실 이름이 있습니다. **Hexagonal Architecture (Ports and Adapters)** 또는 **Clean Architecture** 의 핵심 원리이며, 한 줄로 요약하면 다음과 같습니다.

> **도메인 로직이 인프라(DB·메시지큐·외부 API) 를 모르도록, 인프라가 도메인 인터페이스를 구현하도록 의존 방향을 뒤집는다.**

### 1) Repository 인터페이스를 비즈니스 레이어에 둔다

비즈니스 레이어가 자기에게 필요한 저장소 모양을 **선언**하고, 영속성 레이어가 그 모양을 **구현**합니다.

**Before — 비즈니스가 JPA 를 직접 안다**

```kotlin
// domain/order/OrderService.kt
@Service
class OrderService(private val orderRepository: OrderJpaRepository) { ... }

// domain/order/OrderJpaRepository.kt
interface OrderJpaRepository : JpaRepository<OrderEntity, Long>
```

- `OrderService` 가 `JpaRepository` 의 모양을 알게 됩니다.
- 테스트에서 JPA / 영속성 컨텍스트를 띄우지 않으면 isolation 불가능합니다.

**After — 비즈니스가 자기 인터페이스를 가진다**

```kotlin
// domain/order/OrderRepository.kt
interface OrderRepository {
    fun findById(id: OrderId): Order?
    fun save(order: Order): Order
}

// infrastructure/order/OrderJpaAdapter.kt
@Repository
class OrderJpaAdapter(
    private val orderJpaRepository: OrderJpaRepository,
) : OrderRepository {
    override fun findById(id: OrderId): Order? =
        orderJpaRepository.findById(id.value).orElse(null)?.toDomain()

    override fun save(order: Order): Order =
        orderJpaRepository.save(order.toEntity()).toDomain()
}
```

- `OrderService` 는 `OrderRepository` 인터페이스만 압니다. JPA 의 존재를 모릅니다.
- 테스트에서는 `FakeOrderRepository` (`HashMap` 기반) 로 충분합니다.

```kotlin
class FakeOrderRepository : OrderRepository {
    private val store = mutableMapOf<OrderId, Order>()
    override fun findById(id: OrderId): Order? = store[id]
    override fun save(order: Order): Order = order.also { store[it.id] = it }
}
```

이 한 단계로 **`@SpringBootTest` 가 필요했던 자리의 절반이 사라집니다.**

### 2) 외부 연동도 같은 원리로 뒤집는다

`JavaMailSender`·`SlackClient`·`TossPaymentClient` 같이 외부 시스템을 부르는 모든 의존성도 도메인 인터페이스 + 인프라 구현으로 분리합니다.

```kotlin
// domain/order/PaymentGateway.kt
interface PaymentGateway {
    fun charge(method: PaymentMethod, amount: Money): PaymentResult
}

// infrastructure/payment/TossPaymentAdapter.kt
@Component
class TossPaymentAdapter(private val tossClient: TossPaymentClient) : PaymentGateway { ... }
```

테스트에서는 `FakePaymentGateway` 가 항상 성공·실패·타임아웃 시나리오를 즉시 흉내 낼 수 있습니다.

### 3) JPA Entity 와 도메인 모델을 분리한다

레이어드 아키텍처의 가장 큰 함정 중 하나는 **JPA Entity 가 곧 도메인 모델** 인 것입니다. `@Entity` 가 비즈니스 규칙을 들고 있게 되면 JPA 의 lifecycle (`@PrePersist`, dirty checking) 이 도메인 결정에 끼어듭니다.

분리하면 다음과 같습니다.

- `Order` (도메인) — 순수 Kotlin 클래스, `lombok` 외 어노테이션 없음. 비즈니스 규칙이 메서드로 응집.
- `OrderEntity` (영속성) — `@Entity`, getter/setter, JPA 매핑 전용. `toDomain()` / `from(domain)` 으로 변환.

번거롭지만, **도메인 규칙이 JPA 모양에 끌려가지 않게** 됩니다.

### 4) CQRS 로 메서드의 책임 정리

원본 글의 7번 항목인 CQRS 는 큰 패턴이지만, 작은 적용도 가능합니다.

- **Command** — 상태를 변경한다. 반환은 가능한 한 `void` 또는 새로 만든 ID 정도.
- **Query** — 상태를 조회한다. 절대 부수효과 없음. read-only 트랜잭션.

한 메서드가 "조회해서 변경하고 또 조회하고…" 하지 않도록, **command 와 query 를 다른 메서드로 분리**하는 것이 1차 적용입니다. 본격적인 CQRS (read model 따로 두기) 는 이후 단계입니다.

## 그래서 어떻게 시작하는가

처음부터 헥사고날·클린을 풀세트로 깔지 않아도 됩니다. 다음 순서가 현실적입니다.

1. **fat service 한 곳을 골라 도메인 메서드로 옮긴다.** `placeOrder` 의 재고·잔액 검증을 `Order.place(product, quantity, user)` 안으로.
2. **Repository 인터페이스 분리.** 가장 빈번한 도메인 1~2개부터.
3. **Fake 로 단위 테스트 작성.** `@SpringBootTest` 가 줄어드는 것이 즉시 보입니다.
4. **외부 연동을 게이트웨이 인터페이스로 추상화.** 새 외부 시스템 도입 시점부터 적용하는 것이 비용이 가장 적습니다.
5. **JPA Entity 분리.** 이건 비용이 크니, 도메인이 가장 복잡한 곳부터 점진 적용.

## 트레이드오프 — 모든 프로젝트의 답은 아니다

이 길에는 명확한 비용이 있습니다.

- **보일러플레이트가 늘어납니다.** 인터페이스 + 어댑터 + 도메인-영속성 변환이 모두 필요합니다.
- **러닝 커브가 있습니다.** 새 팀원이 "왜 같은 `Order` 가 두 개 있죠?" 를 묻고, 답하는 데 시간이 듭니다.
- **작은 프로젝트에는 오버킬입니다.** CRUD 가 80% 인 어드민 도구는 그냥 레이어드가 빠릅니다.

다음 조건이 두 개 이상 모이면 옮기는 것이 정답에 가깝습니다.

- 외부 시스템 의존이 3개 이상 (DB · 메시지큐 · 외부 API · 검색 인덱스 등)
- 비즈니스 규칙이 한 도메인 안에서 4개 이상 분기
- 테스트 실행이 1분을 넘기 시작
- 팀 인원이 3명 이상이고 같은 도메인에 동시 작업

## 운영 관점 — 마이그레이션 비용

이미 fat service 가 깔린 프로젝트를 옮긴다면 단위는 도메인 1개 + 약 1주 입니다. 가장 큰 비용은 코드 변환이 아니라 **테스트를 새 구조에 맞게 다시 쓰는 시간**입니다. 다만 한 번 옮긴 도메인은 그 다음 도메인의 패턴이 되어 비용이 빠르게 줄어듭니다.

## 정리

레이어드 아키텍처는 시작점으로 훌륭하지만, 규모가 커지면 **DB 주도 설계 · 동시 작업 제약 · fat service** 라는 세 가지 신호를 보냅니다. 이 신호를 코드 문제로 푸려는 시도 (더 정교한 mock, 더 무거운 통합 테스트) 는 잠시 가려놓을 뿐 결국 다시 옵니다. 진짜 해결은 **의존성 방향을 뒤집어 도메인이 인프라를 모르게 만드는 것** 이고, 그 결이 헥사고날 · 클린 아키텍처입니다.

다음 글에서는 이 글에서 짧게 짚은 **도메인 모델과 JPA Entity 분리** 의 구체 변환 패턴 (값 객체·집합근·매퍼) 을 코드로 정리합니다.
