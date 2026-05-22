---
author: "luca"
pubDatetime: 2023-06-22T14:14:32+09:00
title: "레이어별 테스트 — Repository, Service, Controller 를 어디까지 어떻게"
slug: "layered-testing-strategy"
featured: false
draft: false
tags: ["testing", "unit-test", "integration-test", "spring", "controller-test"]
description: "Repository·Service·Controller 각 레이어를 어디까지 어떻게 테스트할지, JUnit5·Spring Test·MockMvc 의 도구들을 5-6년차 시각으로 정렬합니다."
---

> 2023-06 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 테스트 학습 시리즈의 세 번째 글이며, 이전 글들 ("개념, 대역", "의존성과 Testability") 에서 다룬 도구·원칙을 실제 레이어에 적용하는 자리입니다. 시리즈의 마무리 격인 "레이어드 아키텍처의 문제점과 해결책" 글이 이 다음을 잇습니다.

테스트를 막 시작할 때 가장 자주 던지게 되는 질문은 단순합니다. **"이 레이어는 어디까지 어떻게 테스트해야 하나요?"** Repository 는 DB 까지 띄워야 하는지, Service 는 mock 으로 둘러싸야 하는지, Controller 는 정말 HTTP 까지 검증해야 하는지. 같은 답이 모든 프로젝트에 들어맞지는 않지만, 레이어마다 **권장 도구와 흔한 함정** 의 기본 결은 정렬되어 있습니다. 이 글은 그 결을 정리합니다.

## 사전 정리 — JUnit5 의 확장 지점

본론 전에 어휘 정리부터 합니다. 레이어별 테스트 코드에 거의 항상 등장하는 어노테이션 둘입니다.

### `@ExtendWith`

> JUnit5 의 lifecycle 에 외부 기능을 끼워 넣는 확장 지점입니다.

자주 쓰이는 형태 둘입니다.

- **`@ExtendWith(SpringExtension::class)`** — Spring TestContext Framework 를 JUnit5 와 연결합니다. `@SpringBootTest`, `@DataJpaTest`, `@WebMvcTest` 같은 어노테이션은 내부에서 이미 이 확장을 끌고 옵니다.
- **`@ExtendWith(MockitoExtension::class)`** — Mockito 의 mock 컨텍스트를 JUnit5 와 연결합니다. `@Mock`, `@InjectMocks` 같은 어노테이션을 활성화시킵니다.

5-6년차 코드베이스에서는 보통 어느 한 쪽만 명시적으로 적습니다. Spring 컨텍스트가 필요 없는 순수 단위 테스트라면 Mockito 만, Spring 컨텍스트가 필요하면 Spring 확장이 자동으로 들어옵니다.

### 테스트 슬라이스 어노테이션 한눈에

Spring Boot 가 제공하는 "테스트 슬라이스" 어노테이션을 한 표로 정리합니다.

| 어노테이션 | 띄우는 범위 | 주 용도 | 속도 |
|---|---|---|---|
| `@SpringBootTest` | 전체 ApplicationContext | E2E 또는 무거운 통합 테스트 | 가장 느림 |
| `@DataJpaTest` | JPA + DataSource + 트랜잭션 | Repository 통합 테스트 | 중간 |
| `@WebMvcTest` | MVC 레이어 (Controller + Filter + Advice) | Controller 단위·통합 | 빠름 |
| `@JsonTest` | Jackson 직렬화 영역 | DTO 변환 검증 | 빠름 |
| 슬라이스 없음 | 컨텍스트 미사용 | 도메인 단위 테스트 | 가장 빠름 |

원칙은 단순합니다. **필요한 만큼만 띄웁니다.** `@SpringBootTest` 가 모든 곳에 깔리면, 이전 글 "의존성과 Testability" 에서 짚은 설계 신호 — "시스템이 RDB 와 외부 인프라에 강결합되어 있다" — 가 켜진 상태입니다.

## Repository 테스트

### 권장 도구

Repository 의 검증 대상은 거의 항상 **쿼리** 입니다. JPQL · QueryDSL · Native Query 가 의도한 결과를 돌려주는지가 핵심이며, 이는 진짜 DB(또는 그에 준하는 환경) 가 있어야만 검증됩니다.

```kotlin
@ExtendWith(SpringExtension::class)
@DataJpaTest(showSql = true)
@TestPropertySource("classpath:test-application.properties")
@Sql("/sql/user-repository-test-data.sql")
class UserRepositoryTest {

    @Autowired
    private lateinit var userRepository: UserRepository

    @Test
    fun `findByIdAndStatus 로 ACTIVE 상태인 유저를 조회한다`() {
        val result = userRepository.findByIdAndStatus(1L, UserStatus.ACTIVE)
        assertThat(result.isPresent).isTrue()
    }
}
```

- **`@DataJpaTest`** — JPA 관련 빈만 띄웁니다. 전체 컨텍스트의 일부분만 로딩되어 `@SpringBootTest` 보다 훨씬 빠릅니다.
- **`@TestPropertySource`** — 테스트 전용 `application.properties` 를 지정합니다. 운영 설정을 건드리지 않기 위함입니다.
- **`@Sql`** — fixture 데이터를 SQL 파일로 미리 주입합니다. 클래스 단위·메서드 단위로 부착할 수 있습니다.

기본 동작 중 한 가지는 의식해 둘 만합니다. `@DataJpaTest` 는 **각 테스트가 끝나면 트랜잭션을 롤백** 합니다. 테스트 간 격리는 자동으로 보장되지만, "테스트가 끝나면 데이터가 남지 않는다" 는 점을 fixture 설계에 반영해야 합니다.

### 운영 DB 와 테스트 DB

원본 노트에는 `H2` 가 자주 등장했습니다만, 5-6년차 시각으로 한 가지 보태자면 **운영 DB 와 다른 DB 로 테스트를 돌리는 결정은 점점 줄어드는 추세** 입니다.

| 옵션 | 장점 | 단점 |
|---|---|---|
| **H2 (in-memory)** | 빠름, 외부 의존 없음 | 운영(MySQL/PG) 과 SQL 방언 차이 |
| **Testcontainers + 운영과 같은 DB** | 운영과 동일한 SQL 동작 | 컨테이너 부팅 비용, Docker 필요 |
| **공용 테스트 DB** | 운영 동일 환경 | 동시성 충돌, 격리 어려움 |

규모가 작거나 SQL 이 표준에 가깝다면 `H2` 도 합리적입니다. 그러나 JSON 컬럼·윈도우 함수·DB 별 락 동작이 검증 대상에 들어오기 시작하면 **Testcontainers** 로 옮기는 비용이 빠르게 회수됩니다. 이 결정은 시리즈 마지막 글 "레이어드 아키텍처의 문제점과 해결책" 에서 짚은 "외부 시스템 의존이 3개 이상" 인 프로젝트에서 특히 두드러집니다.

### 함정 — Repository 만 테스트하다 Service 를 잊는다

Repository 테스트가 늘면 한 가지 함정이 따라옵니다. **"쿼리가 통과했으니 Service 도 잘 동작할 것" 이라는 착각** 입니다. Repository 가 돌려준 결과를 Service 가 어떻게 다루는지는 별개 영역입니다. 다음 절에서 이어집니다.

## Service 테스트

### 두 갈래의 결정

Service 테스트는 보통 두 갈래로 나뉩니다.

- **단위 테스트** — Repository · 외부 클라이언트를 **Fake/Mock** 으로 치환하고 도메인 로직만 검증합니다.
- **통합 테스트** — `@SpringBootTest` 또는 슬라이스로 진짜 빈을 띄워 협력자 간 흐름까지 검증합니다.

5-6년차 시각의 권장은 **단위 테스트가 주력, 통합 테스트는 핵심 시나리오 한정** 입니다. 시범 글에서 다룬 fat service 예시처럼 협력자가 5~6개로 늘어나면, 단위 테스트가 짜기 어려워집니다. 그것이 곧 설계가 보내는 신호이며, Service 테스트의 첫 번째 관문입니다.

### 외부 의존성을 다루는 방식

원본 노트에 등장했던 패턴 — `@SpringBootTest` + `@MockBean` 으로 `JavaMailSender` 를 치환 — 을 그대로 가져와 비교합니다.

**Before — `@MockBean` 으로 외부 의존성 치환**

```kotlin
@SpringBootTest
class UserServiceTest {

    @Autowired
    private lateinit var userService: UserService

    @MockBean
    private lateinit var javaMailSender: JavaMailSender

    @Test
    fun `사용자 생성 시 이메일 인증 코드가 전송된다`() {
        userService.create(CreateUserRequest(...))
        verify(javaMailSender).send(any<MimeMessage>())
    }
}
```

- 전체 컨텍스트를 띄웁니다. 한 테스트당 부팅 비용이 큽니다.
- `JavaMailSender` 를 빈으로 치환하므로 `UserService` 가 **`JavaMailSender` 라는 구체 타입을 그대로 알고 있는 상태** 입니다.

**After — 인터페이스 + Fake 로 단위 테스트**

```kotlin
// 도메인 인터페이스
interface MailGateway {
    fun send(to: Email, content: MailContent)
}

// 테스트용 Fake
class FakeMailGateway : MailGateway {
    val sent: MutableList<Pair<Email, MailContent>> = mutableListOf()
    override fun send(to: Email, content: MailContent) { sent += to to content }
}

class UserServiceTest {

    @Test
    fun `사용자 생성 시 이메일 인증 코드가 전송된다`() {
        // given
        val mailGateway = FakeMailGateway()
        val sut = UserService(
            userRepository = FakeUserRepository(),
            mailGateway = mailGateway,
            codeGenerator = FixedCodeGenerator("ABCD"),
        )

        // when
        sut.create(CreateUserRequest(email = Email("test@example.com")))

        // then
        assertThat(mailGateway.sent).hasSize(1)
        assertThat(mailGateway.sent.first().second.text).contains("ABCD")
    }
}
```

- Spring 컨텍스트 부팅이 없습니다. 실행 속도는 **밀리초 단위** 입니다.
- 검증이 행위(`verify`) 가 아니라 상태(`sent` 목록) 로 이루어집니다. 이전 글 "개념, 대역" 에서 짚은 **상태 검증 우선** 원칙 그대로입니다.
- `FakeMailGateway` 는 `MailGateway` 의 진짜 인스턴스이므로, 호출되었는지·어떤 내용으로 호출되었는지를 모두 검증할 수 있습니다.

### 테스트가 보내는 설계 신호

원본 노트에 두 가지 사례가 있었습니다. 둘 다 "테스트가 설계 문제를 알려주는 신호" 의 표본입니다.

**사례 1 — UUID 로 생성된 인증 코드를 검증할 길이 없다.**

```kotlin
class UserService(...) {
    fun create(request: CreateUserRequest) {
        val code = UUID.randomUUID().toString()  // 매번 다른 값
        mailGateway.send(request.email, MailContent("코드: $code"))
    }
}
```

- 테스트가 `code` 의 값을 알 길이 없으므로, "메일이 보내졌다" 정도까지만 검증됩니다.
- 이전 글 "의존성과 Testability" 에서 다룬 **숨겨진 의존성** 의 전형입니다.
- 해법은 `CodeGenerator` 를 인터페이스로 외부화하고, 테스트에서는 `FixedCodeGenerator` 를 주입하는 것입니다.

**사례 2 — `Clock.systemUTC()` 로 찍은 timestamp 를 비교할 길이 없다.**

```kotlin
class CertificationCode(...) {
    val createdAt: LocalDateTime = LocalDateTime.now(Clock.systemUTC())
}
```

- `createdAt` 이 매 실행마다 다릅니다. assertion 으로 박을 값이 없습니다.
- 같은 종류의 신호이며, 같은 종류의 해법(`Clock` 주입) 이 적용됩니다.

원본의 단호한 한 줄을 그대로 살리자면, **"테스트가 못 짠다고 느껴지는 순간은 거의 항상 설계가 보내는 신호"** 입니다.

### 함정 — 모든 협력자를 `@MockBean` 으로

`@MockBean` 은 강력하지만, **모든 협력자를 `@MockBean` 으로 둘러싸기 시작하면** 테스트는 점점 SUT 의 내부 호출 시퀀스를 베껴 적은 사본이 됩니다. 권장 결은 다음과 같습니다.

- **도메인 협력자** — Fake 로 치환합니다 (`FakeUserRepository`, `FakeMailGateway`).
- **외부 시스템 자체의 응답** — Stub/Mock 으로 흉내냅니다 (외부 API 의 HTTP 응답 등).

이 분리는 시리즈 마지막 글 ("레이어드 아키텍처의 문제점과 해결책") 의 게이트웨이 인터페이스 분리와 정확히 한 결입니다.

## Controller 테스트

### MockMvc — HTTP 를 흉내내는 도구

> `MockMvc` 는 서버를 띄우지 않고 **HTTP 요청/응답 흐름을 메모리에서 흉내내는** 도구입니다.

핵심은 "진짜 HTTP 가 아니지만, Spring MVC 의 거의 모든 처리(필터·인터셉터·예외 처리·검증) 가 그대로 동작" 한다는 점입니다.

```kotlin
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @Test
    fun `특정 유저 조회 시 개인정보가 소거되어 반환된다`() {
        mockMvc.perform(get("/api/users/1"))
            .andExpect(status().isOk)
            .andExpect(jsonPath("$.email").value("k***@naver.com"))
    }
}
```

- `mockMvc.perform(...)` 으로 HTTP 메서드·경로·헤더·바디를 흉내냅니다.
- `andExpect(...)` 로 상태 코드·헤더·바디(`jsonPath` 또는 `content`) 를 검증합니다.

### `@WebMvcTest` vs `@SpringBootTest + @AutoConfigureMockMvc`

자주 헷갈리는 두 슬라이스를 비교합니다.

| 항목 | `@WebMvcTest` | `@SpringBootTest + @AutoConfigureMockMvc` |
|---|---|---|
| 띄우는 범위 | MVC 레이어만 | 전체 컨텍스트 |
| Service·Repository 빈 | **포함되지 않음** (별도 `@MockBean` 필요) | 모두 포함 |
| 속도 | 빠름 | 느림 |
| 주 용도 | Controller 단위 테스트 | Controller 통합 테스트 |
| Spring Security 적용 | 컨트롤러 슬라이스만 적용 | 운영과 동일하게 적용 |

**`@WebMvcTest` 가 적합한 자리**

```kotlin
@WebMvcTest(controllers = [UserController::class])
class UserControllerSliceTest {

    @Autowired
    private lateinit var mockMvc: MockMvc

    @MockBean
    private lateinit var userService: UserService

    @Test
    fun `존재하지 않는 유저 조회 시 404`() {
        whenever(userService.findById(any())).thenReturn(null)

        mockMvc.perform(get("/api/users/999"))
            .andExpect(status().isNotFound)
    }
}
```

- Service 빈은 컨텍스트에 없으므로 `@MockBean` 으로 주입합니다.
- **Controller 자체의 책임** — 경로 매핑, 요청 검증, 응답 직렬화, 예외 처리 — 만 검증합니다.

**`@SpringBootTest + @AutoConfigureMockMvc` 가 적합한 자리**

- E2E 에 가까운 시나리오를 한 번에 묶어 검증할 때
- Security 설정·CORS·Filter 의 운영 동작까지 확인이 필요할 때
- 핵심 비즈니스 플로우의 회귀 방지 (개수는 최소화)

### 함정 — Controller 가 너무 많은 일을 한다

Controller 테스트를 짜다 보면 한 가지 신호가 자주 켜집니다. **"이 Controller 메서드를 테스트하려고 보니, 요청 변환·도메인 로직·응답 변환이 모두 들어가 있다."** 이 경우 답은 더 정교한 MockMvc 사용법이 아니라, Controller 의 책임을 Service 로 넘기는 일입니다. Controller 는 결국 **HTTP <-> Application 계층의 변환기** 에 가까울 때 가장 테스트하기 쉽습니다.

## 한눈에 — 레이어별 권장 매트릭스

| 레이어 | 1순위 도구 | 2순위 도구 | 검증 초점 | 흔한 함정 |
|---|---|---|---|---|
| **Repository** | `@DataJpaTest` + 진짜 DB | Testcontainers | 쿼리 결과·매핑 | H2/운영 DB 방언 차이 |
| **Service** | 단위 테스트 + Fake | `@SpringBootTest` | 도메인 로직·상태 변화 | 모든 협력자 `@MockBean` |
| **Controller** | `@WebMvcTest` + MockMvc | `@SpringBootTest` + MockMvc | HTTP 변환·예외 처리 | 비즈니스 로직 침투 |

이 표는 절대 규칙이 아니라 출발점입니다. 프로젝트의 **외부 의존성 수, 도메인 복잡도, 팀 인원, CI 시간 예산** 에 따라 결이 달라집니다.

## 운영 관점 — CI 에서의 테스트 분할

5-6년차 시각으로 한 가지만 보태자면, 레이어별 테스트를 잘 짜는 것만큼이나 **CI 에서 어떻게 돌리느냐** 가 중요합니다.

- **단위 테스트 (Service · 도메인)** — PR 단위로 매번. 수 초 ~ 수십 초 안에 끝나야 PR 흐름이 막히지 않습니다.
- **슬라이스 통합 테스트 (`@DataJpaTest`, `@WebMvcTest`)** — PR 단위로. 보통 수십 초 ~ 수 분.
- **풀 `@SpringBootTest`** — main 머지·nightly 로 분리. 핵심 시나리오만.

이 분할이 안 되어 있으면 PR 한 번에 5~10 분씩 기다리게 되고, 결국 테스트를 안 짜는 결로 흘러갑니다. CI 의 빨강·초록이 빨리 돌아오는 것은 도구의 문제처럼 보이지만, 사실 **테스트 설계가 보내는 신호** 의 또 다른 측면입니다.

## 정리

- 레이어별 테스트의 첫 단추는 **필요한 만큼만 컨텍스트를 띄우는 것** 입니다. `@DataJpaTest`, `@WebMvcTest`, 슬라이스 없음을 의식적으로 골라 씁니다.
- **Repository** 는 진짜 DB(또는 그에 준하는 환경) 가 있어야 의미 있는 검증이 됩니다. H2 와 Testcontainers 사이의 선택은 외부 의존성과 SQL 복잡도에 달려 있습니다.
- **Service** 는 Fake 기반 단위 테스트가 주력입니다. `@MockBean` 의 남용은 신호이고, "테스트가 어렵다" 는 감각은 보통 SUT 의 의존성 모양에 대한 신호입니다.
- **Controller** 는 `@WebMvcTest` + MockMvc 로 변환·예외 처리만 검증하는 결이 가장 깔끔합니다. 비즈니스 로직이 Controller 에 흘러 들어오기 시작하면, 그것 또한 책임 분배가 보내는 신호입니다.

다음 글에서는 이 레이어별 결을 한 단계 더 끌어올려, **레이어드 아키텍처 자체의 한계와 그 대안 (헥사고날·클린 아키텍처)** 으로 시리즈를 닫습니다. 지금까지 다룬 도구·원칙이 왜 같은 방향을 가리켰는지가 그 자리에서 한 번에 정리됩니다.
