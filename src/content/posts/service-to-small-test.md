---
author: "luca"
pubDatetime: 2023-07-15T19:43:49+09:00
title: "Service 테스트를 소형 테스트로 전환하기 — Fake 의 진짜 가치"
slug: "service-to-small-test"
featured: false
draft: false
tags: ["testing", "unit-test", "mock", "fake", "spring", "kotlin"]
description: "@SpringBootTest 로 무거워진 Service 테스트를 Fake 기반 소형 테스트로 바꾸는 결과, Mock 과 Fake 의 차이를 5-6년차 시각으로 정리."
---

> 2023-07 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 그때는 "이렇게 하면 빨라진다" 까지만 적었던 내용에, 지금은 Mock 과 Fake 를 가르는 결과 그 트레이드오프를 함께 적었습니다.

테스트 한 번 돌리면 IDE 가 30초간 멈춰 있던 적이 있습니다. `@SpringBootTest` 가 매번 컨텍스트를 띄우고, `h2` 가 스키마를 만들고, `Liquibase` 가 마이그레이션을 돌리는 식이었습니다. 변경 한 줄에 30초씩 들이는 루프는 결국 **"테스트를 안 돌리고 PR 을 올리는 습관"** 으로 굳습니다. 이건 테스트가 느려서가 아니라 **테스트가 자기 영역을 못 가졌다는 신호**입니다.

## 테스트 크기의 분류

Google 의 분류를 짧게 빌려옵니다.

| 크기 | 특징 | 실행 시간 | 신뢰도 |
|---|---|---|---|
| **소형 (Small)** | 단일 프로세스 / 단일 스레드 / IO 없음 | ms 단위 | 좁은 범위, 결정적 |
| **중형 (Medium)** | 단일 머신 / IO 허용 (h2, embedded redis 등) | 초 단위 | 중간 |
| **대형 (Large)** | 다중 머신 / 외부 시스템 | 분 단위 | 넓은 범위, 비결정적 |

`@SpringBootTest` + `h2` 조합은 **중형** 입니다. Service 로직 검증 목적이라면 과합니다. Service 가 검증할 것은 **비즈니스 규칙**이지 **DB driver 의 동작**이 아니기 때문입니다.

## 소형 테스트로 옮기는 조건

옮기려면 Service 가 다음을 만족해야 합니다.

- **Repository 가 인터페이스로 분리되어 있다** — `UserRepository` 가 `JpaRepository` 를 직접 상속하지 않고, 도메인 인터페이스 + JPA 어댑터로 나뉘어 있음.
- **외부 시스템 의존도 인터페이스로 추상화** — `MailSender`, `PaymentGateway` 같이 도메인이 자기 인터페이스를 들고 있음.
- **시간·UUID 같은 비결정적 값은 추상화** — `Clock`, `UuidGenerator` 같은 holder.

이 셋 중 하나라도 빠져 있다면 소형 테스트로 옮길 수 없습니다. 옮기기 전에 도메인 구조를 먼저 정리해야 합니다 (이전 글 [레이어드 아키텍처의 문제점과 해결책](/posts/layered-architecture-problems-and-solutions) 에서 다뤘던 결).

## FakeRepository — Map 기반 인메모리 구현

테스트용 저장소는 `HashMap` (또는 `ConcurrentHashMap`) 기반으로 단순하게 만듭니다.

```kotlin
class FakeUserRepository : UserRepository {
    private val store = mutableMapOf<Long, User>()
    private val autoIncrement = AtomicLong(0)

    override fun findById(id: Long): User? = store[id]

    override fun findByEmail(email: String): User? =
        store.values.firstOrNull { it.email == email }

    override fun save(user: User): User {
        val toSave = if (user.id == 0L) {
            user.copy(id = autoIncrement.incrementAndGet())
        } else {
            user
        }
        store[toSave.id] = toSave
        return toSave
    }
}
```

- **`AtomicLong` 으로 auto-increment** — DB 의 sequence 를 흉내. 테스트는 단일 스레드이지만 추후 병렬 실행 시에도 안전.
- **`save` 가 id == 0 분기로 insert/update 구분** — JPA 의 결과 같게.
- **쿼리 메서드는 `firstOrNull`/`filter` 로 자연스럽게** — 5~10줄이면 충분.

옛 글의 `data.removeIf` + `data.add` 패턴은 list 기반이었는데, **map 기반이 훨씬 단순**합니다. 옮기는 과정에서 정돈된 부분입니다.

## FakeMailSender — 호출 기록 보존

외부 연동 추상화도 같은 결로 만듭니다. 차이는 **호출된 내용을 보존**해서 테스트가 검증하게 한다는 점입니다.

```kotlin
class FakeMailSender : MailSender {
    val sentMails = mutableListOf<SentMail>()

    override fun send(email: String, title: String, content: String) {
        sentMails += SentMail(email, title, content)
    }

    data class SentMail(val email: String, val title: String, val content: String)
}
```

옛 글에는 `public String email; public String title;` 식으로 마지막 호출만 보존했는데, **`List` 로 모든 호출을 기록**하는 것이 결이 좋습니다. "메일이 1번만 발송됐다" 같은 횟수 검증이 가능해집니다.

## 비결정적 값 — Clock 과 UuidGenerator

`Instant.now()` 와 `UUID.randomUUID()` 가 Service 안에 직접 박혀 있으면 테스트가 비결정적이 됩니다. 추상화합니다.

```kotlin
interface ClockHolder {
    fun now(): Instant
}

class SystemClockHolder : ClockHolder {
    override fun now(): Instant = Instant.now()
}

class TestClockHolder(private val fixed: Instant) : ClockHolder {
    override fun now(): Instant = fixed
}
```

```kotlin
interface UuidHolder {
    fun random(): String
}

class SystemUuidHolder : UuidHolder {
    override fun random(): String = UUID.randomUUID().toString()
}

class TestUuidHolder(private val fixed: String) : UuidHolder {
    override fun random(): String = fixed
}
```

Service 는 이 인터페이스만 의존합니다. 테스트에서는 `TestClockHolder("2024-01-01T00:00:00Z")` 처럼 고정 값을 주입.

## 소형 테스트로 옮긴 결과

`@SpringBootTest` 가 들어가던 자리가 다음과 같이 바뀝니다.

**Before — 중형**

```kotlin
@SpringBootTest
@Sql("/test-data.sql")
class UserServiceTest {
    @Autowired private lateinit var userService: UserService
    @MockBean private lateinit var mailSender: JavaMailSender

    @Test fun `회원가입 시 인증 메일이 발송된다`() {
        userService.signUp(SignUpRequest("a@a.com", "pw", "nick"))
        verify(mailSender).send(any())
    }
}
```

- 컨텍스트 로딩 5~20초
- h2 + Liquibase 셋업
- `@MockBean` 은 컨텍스트를 한 번 더 새로 띄우는 비용을 만듦
- 검증이 `verify(...).send(any())` 라 "뭔가 호출됐다" 까지만 알 수 있음

**After — 소형**

```kotlin
class UserServiceTest {
    private lateinit var userRepository: FakeUserRepository
    private lateinit var mailSender: FakeMailSender
    private lateinit var userService: UserService

    @BeforeEach
    fun setUp() {
        userRepository = FakeUserRepository()
        mailSender = FakeMailSender()
        userService = UserService(
            userRepository = userRepository,
            mailSender = mailSender,
            clockHolder = TestClockHolder(Instant.parse("2024-01-01T00:00:00Z")),
            uuidHolder = TestUuidHolder("fixed-uuid"),
        )
    }

    @Test
    fun `회원가입 시 인증 메일이 1번 발송된다`() {
        // when
        userService.signUp(SignUpRequest("a@a.com", "pw", "nick"))

        // then
        assertThat(mailSender.sentMails).hasSize(1)
        assertThat(mailSender.sentMails[0].email).isEqualTo("a@a.com")
        assertThat(mailSender.sentMails[0].content).contains("fixed-uuid")
    }
}
```

- 컨텍스트 로딩 0초
- 실행 시간 ms 단위
- 메일 내용까지 검증 가능 — `fixed-uuid` 가 메일 본문에 박혀 있는지 확인.

테스트당 실행 시간은 보통 **20초 → 0.05초** 정도로 떨어집니다. 200배 빠름. 변경 한 줄에 즉시 피드백이 옵니다.

## Mock vs Fake — 결정적으로 다른 점

여기서 자주 헷갈리는 지점이 있습니다. "그럼 `Mockito` 의 `mock()` 대신 `FakeUserRepository` 같이 쓰는 이유는 무엇인가?"

| 항목 | Mock | Fake |
|---|---|---|
| 동작 | 호출 시 미리 약속한 값 반환 | 진짜 동작을 단순한 구현으로 흉내 |
| 상태 | 없음 (state-less) | 있음 (state-ful, 내부 store) |
| 검증 방식 | "어떤 메서드가 어떤 인자로 호출되었나" | "최종 상태가 어떻게 되었나" |
| 테스트 결과 | 상호작용 검증 | 결과 검증 |
| 변경 비용 | 메서드 시그니처 바뀌면 약속 다 깨짐 | 인터페이스 안 바뀌면 재사용 |

**Mock 의 한계 한 예시**

```kotlin
// Mock 으로 작성한 테스트
val userRepository = mock<UserRepository>()
whenever(userRepository.findByEmail("a@a.com")).thenReturn(null)
whenever(userRepository.save(any())).thenAnswer { it.arguments[0] }

userService.signUp(SignUpRequest("a@a.com", "pw", "nick"))

verify(userRepository).save(argThat { email == "a@a.com" })
```

이 테스트가 통과해도 정작 "회원가입 후 다시 같은 이메일로 가입 시도 시 막힌다" 같은 **두 단계 시나리오는 검증할 수 없습니다**. Mock 은 상태를 안 가지기 때문입니다.

**Fake 로 같은 시나리오**

```kotlin
userService.signUp(SignUpRequest("a@a.com", "pw", "nick"))

assertThatThrownBy {
    userService.signUp(SignUpRequest("a@a.com", "pw2", "nick2"))
}.isInstanceOf(DuplicateEmailException::class.java)
```

Fake 는 실제로 저장하므로, 같은 이메일로 두 번째 호출이 막히는지 자연스럽게 검증됩니다. **테스트 코드가 "실제 사용 시나리오" 에 더 가깝습니다.**

## 어떤 자리에 무엇을 쓰는가

Mock 도 쓸 자리가 있습니다. Fake 도 만능은 아닙니다.

- **Fake 가 유리한 자리**: Repository, 외부 연동 (메일·결제·SMS), 캐시
- **Mock 이 유리한 자리**: 한 번만 호출되고 검증할 게 그 호출 사실 자체인 경우 (예: 이벤트 발행 카운트), 또는 인터페이스 자체가 호출 횟수·순서가 중요한 경우

기준은 단순합니다 — **"이 의존이 상태를 가지는가?"** 가집니다 → Fake. 안 가집니다 → Mock.

## 함정 — Fake 가 진짜와 어긋날 때

Fake 의 약점은 **진짜 구현과 결이 다를 위험**입니다.

- 진짜 JPA Repository 는 `save` 후 `findById` 가 같은 트랜잭션이면 1차 캐시에서 가져옵니다.
- 진짜 RDB 는 unique 제약을 violation 으로 던집니다. Fake 가 그걸 흉내내지 않으면 production 에서만 깨집니다.
- Soft delete · cascade · 영속성 컨텍스트의 dirty checking — 모두 Fake 가 흉내내기 어려운 영역입니다.

대응은 둘입니다.

1. **Fake 에 핵심 제약을 흉내냄** — 예: `FakeUserRepository.save` 에서 같은 email 이 이미 있으면 `DataIntegrityViolationException` 던지기.
2. **Repository 인터페이스 자체에 대한 통합 테스트 한 벌은 따로 둠** — `UserRepositoryIntegrationTest` 가 JPA 어댑터·Fake 양쪽에서 같은 시나리오를 돌도록.

두 번째 방법은 **계약 테스트 (contract test)** 라고 부르며, Fake 가 진짜의 결을 안 잃도록 잡아주는 안전망입니다.

## 트레이드오프 — 소형 테스트로 다 옮기는 게 정답인가

아닙니다. 다음 한 벌은 여전히 중형 (`@SpringBootTest` 또는 `@DataJpaTest`) 으로 가야 합니다.

- **Repository 의 쿼리 자체 검증** — `@Query` JPQL 이 의도대로 동작하는지는 진짜 DB 가 필요합니다.
- **트랜잭션 경계 · 격리수준 · lock 동작** — Fake 가 흉내 못 합니다.
- **마이그레이션 스크립트 검증** — Liquibase / Flyway 의 결과는 진짜 DB 에서.
- **end-to-end 통합 시나리오 1~2벌** — "회원가입 → 로그인 → 주문" 같은 핵심 행복 경로.

대신 이 자리는 **수십 개가 아니라 핵심 몇 개**만 둡니다. 나머지 비즈니스 로직 검증은 소형 테스트가 담당합니다.

## 그래서 어떻게 시작하는가

기존 프로젝트에 적용한다면 다음 순서가 현실적입니다.

1. **Repository 인터페이스 분리** — 가장 자주 쓰는 도메인 1~2개부터.
2. **`FakeRepository` 작성** — 인터페이스가 분리되어 있으면 30분 작업.
3. **`Clock` · `Uuid` 추상화** — 처음 보면 과해 보이지만, 시간 의존 버그를 1번이라도 잡으면 가치가 보입니다.
4. **Service 테스트 1개를 소형으로 옮겨봄** — 실행 시간 차이를 팀에 보여주는 것이 가장 큰 설득.
5. **신규 Service 부터 소형 테스트 default 로** — 기존 테스트는 자연스럽게 갱신.

## 정리

소형 테스트는 단지 빠른 테스트가 아닙니다. **테스트가 외부 인프라에 의존하지 않을 수 있다는 것은 도메인이 인프라에서 분리되어 있다는 신호** 입니다. Fake 가 등장한 순간 우리는 "이 Service 가 정말 자기 책임만 가지고 있는가" 를 한 번 더 묻게 됩니다. 그 질문이 코드를 깔끔하게 만듭니다.

다음 글에서는 이 소형 테스트 위에서 **테스트 더블의 분류 (Dummy / Stub / Spy / Mock / Fake)** 를 코드로 구분하고, 자주 헷갈리는 자리들을 정리합니다.
