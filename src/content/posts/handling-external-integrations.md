---
author: "luca"
pubDatetime: 2023-06-28T14:47:45+09:00
title: "외부 연동을 다루는 방법 — 의존성 역전으로 테스트 가능한 구조 만들기"
slug: "handling-external-integrations"
featured: false
draft: false
tags: ["architecture", "external-api", "testing", "dependency-injection", "spring", "kotlin"]
description: "Service 가 JavaMailSender 에 직접 의존할 때 생기는 문제와, 도메인 포트 / 인프라 어댑터로 뒤집은 뒤 얻는 테스트 용이성·운영 이득을 정리."
---

> 2023-06 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 그때는 "이렇게 분리하면 깔끔하다" 정도로 적었으나, 지금은 운영에서 보이는 진짜 이득과 적용 비용을 함께 적습니다.

**TL;DR.** SMTP 가 흔들려 회원가입이 통째 롤백된 사건이 있었습니다. `@Transactional` 안에서 `mailSender.send()` 를 직접 부르는 코드를, **도메인 포트 + 인프라 어댑터 + 트랜잭션 이벤트 리스너** 의 세 단계로 끌어냈습니다. 테스트 속도 · 운영 안정성 · 변경 비용 세 가지가 같이 떨어집니다.

이메일 발송이 실패해서 회원가입 자체가 롤백된 적이 있습니다. SMTP 서버가 잠시 흔들렸을 뿐인데, 사용자 입장에서는 회원가입이 안 됩니다. 코드를 보니 회원가입 `@Transactional` 안에서 `mailSender.send()` 를 직접 부르고 있었습니다. 이 결합이 사고의 근본 원인이었습니다.

## 무엇이 문제인가 — 외부 연동이 비즈니스 안에 박힐 때

다음 코드는 흔하게 마주칩니다.

```kotlin
@Service
class UserService(
    private val userRepository: UserRepository,
    private val mailSender: JavaMailSender,   // 문제의 자리
) {
    @Transactional
    fun create(request: UserCreateRequest): User {
        val user = User(
            email = request.email,
            nickname = request.nickname,
            status = UserStatus.PENDING,
            certificationCode = UUID.randomUUID().toString(),
        )
        val saved = userRepository.save(user)
        val url = "http://localhost:8080/api/users/${saved.id}/verify?code=${saved.certificationCode}"
        sendCertificationEmail(saved.email, url)
        return saved
    }

    private fun sendCertificationEmail(email: String, url: String) {
        val message = SimpleMailMessage().apply {
            setTo(email)
            subject = "Please certify your email address"
            text = "Please click: $url"
        }
        mailSender.send(message)
    }
}
```

이 코드의 진짜 문제는 네 가지입니다.

- **Service 가 `JavaMailSender` 라는 인프라 클래스를 직접 압니다** — Spring 의존이 도메인에 박힙니다.
- **테스트가 무거워집니다** — `JavaMailSender` 를 mock 하거나 SMTP 서버를 띄워야 합니다.
- **트랜잭션 안에서 외부 호출이 일어납니다** — SMTP 가 느리면 DB 커넥션이 그만큼 묶입니다. 실패하면 회원가입까지 롤백됩니다.
- **메일 발송 정책 변경이 Service 코드를 건드립니다** — SMS·푸시 추가 시 Service 가 또 바뀝니다.

이 네 가지를 한 번에 푸는 길이 **의존성 역전 (Dependency Inversion Principle)** 입니다.

## 의존성 역전 — 도메인이 자기 인터페이스를 가진다

핵심 한 줄.

> **도메인은 자기에게 필요한 외부 인터페이스의 모양을 정의하고, 인프라는 그 모양을 구현한다.**

이 글에서는 두 단계로 나눠 적용합니다.

1. **`MailSender` 포트 추출** — 메일 발송의 도메인 인터페이스.
2. **`CertificationService` 분리** — 인증 메일 정책의 도메인 객체.

### 1) MailSender — 포트와 어댑터

먼저 도메인 쪽에 포트 (`port`) 패키지로 인터페이스를 둡니다.

```kotlin
// domain/user/port/MailSender.kt
interface MailSender {
    fun send(email: String, title: String, content: String)
}
```

- 인자는 **원시 타입과 문자열만** — `SimpleMailMessage` 같은 Spring 타입이 빠집니다.
- 메서드는 의도를 드러내는 이름 — 인프라의 메서드 이름을 그대로 따라가지 않습니다.

다음으로 인프라 쪽에 구현체를 둡니다.

```kotlin
// infrastructure/mail/SmtpMailSender.kt
@Component
class SmtpMailSender(
    private val javaMailSender: JavaMailSender,
) : MailSender {
    override fun send(email: String, title: String, content: String) {
        val message = SimpleMailMessage().apply {
            setTo(email)
            subject = title
            text = content
        }
        javaMailSender.send(message)
    }
}
```

- `@Component` 가 인프라 어댑터에만 붙습니다 — 도메인 인터페이스에는 안 붙습니다.
- `JavaMailSender` 라는 Spring 의존은 **이 한 클래스에만** 갇힙니다.

### 2) CertificationService — 메일 정책을 도메인으로

`UserService` 가 인증 URL 을 만들고 메일 본문을 짜는 일까지 직접 한다면, 그 자체로 책임이 너무 큽니다. 인증 메일의 정책을 별도 도메인 서비스로 뽑습니다.

```kotlin
// domain/user/CertificationService.kt
@Service
class CertificationService(
    private val mailSender: MailSender,
) {
    fun send(email: String, userId: Long, code: String) {
        val url = generateUrl(userId, code)
        mailSender.send(
            email = email,
            title = "Please certify your email address",
            content = "Please click: $url",
        )
    }

    private fun generateUrl(userId: Long, code: String): String =
        "http://localhost:8080/api/users/$userId/verify?code=$code"
}
```

`UserService` 는 이제 다음과 같이 단순해집니다.

```kotlin
@Service
class UserService(
    private val userRepository: UserRepository,
    private val certificationService: CertificationService,
) {
    @Transactional
    fun create(request: UserCreateRequest): User {
        val user = User(
            email = request.email,
            nickname = request.nickname,
            status = UserStatus.PENDING,
            certificationCode = UUID.randomUUID().toString(),
        )
        val saved = userRepository.save(user)
        certificationService.send(saved.email, saved.id, saved.certificationCode)
        return saved
    }
}
```

- `UserService` 가 더 이상 메일 본문을 모릅니다.
- `JavaMailSender` 라는 단어가 사라졌습니다.
- 인증 메일 정책이 바뀌면 `CertificationService` 만 건드립니다.

## 테스트가 따라오는 모양

의존성을 인터페이스로 뒤집은 직접적인 효과는 테스트에서 옵니다.

### FakeMailSender

```kotlin
class FakeMailSender : MailSender {
    data class SentMail(val email: String, val title: String, val content: String)
    val sentMails = mutableListOf<SentMail>()

    override fun send(email: String, title: String, content: String) {
        sentMails += SentMail(email, title, content)
    }
}
```

5줄짜리 fake 가 SMTP 서버를 대체합니다.

### CertificationServiceTest

```kotlin
class CertificationServiceTest {

    @Test
    fun `메일 제목과 본문이 정확한 형식으로 발송된다`() {
        // given
        val fakeMailSender = FakeMailSender()
        val sut = CertificationService(fakeMailSender)

        // when
        sut.send(
            email = "luca@example.com",
            userId = 1,
            code = "aaaa-bbbb-cccc",
        )

        // then
        assertThat(fakeMailSender.sentMails).hasSize(1)
        val mail = fakeMailSender.sentMails[0]
        assertThat(mail.email).isEqualTo("luca@example.com")
        assertThat(mail.title).isEqualTo("Please certify your email address")
        assertThat(mail.content).isEqualTo(
            "Please click: http://localhost:8080/api/users/1/verify?code=aaaa-bbbb-cccc",
        )
    }
}
```

- `@SpringBootTest` 없음
- SMTP 서버 없음
- 실행 시간 ms 단위
- 메일 본문까지 정확한 형식으로 검증

이것이 의존성 역전의 직접적인 보상입니다. 테스트가 도메인 결정을 그대로 검증합니다. 운영 코드와 테스트 코드 사이의 거리가 가장 짧아지는 자리입니다.

## 운영 관점 — 트랜잭션 밖으로 빼는 패턴

의존성 역전만으로 끝이 아닙니다. 더 큰 운영 문제는 **트랜잭션 안에서 외부 호출** 이 일어난다는 점입니다. 위 코드도 여전히 `UserService.create` 의 `@Transactional` 안에서 `certificationService.send` 를 부릅니다. SMTP 가 흔들리면 회원가입까지 같이 흔들립니다.

해결은 외부 호출을 **트랜잭션 커밋 이후** 로 미루는 것입니다. Spring 의 `@TransactionalEventListener` 를 활용합니다.

```kotlin
// 도메인 이벤트
data class UserRegisteredEvent(val userId: Long, val email: String, val code: String)

@Service
class UserService(
    private val userRepository: UserRepository,
    private val publisher: ApplicationEventPublisher,
) {
    @Transactional
    fun create(request: UserCreateRequest): User {
        val saved = userRepository.save(User(...))
        publisher.publishEvent(UserRegisteredEvent(saved.id, saved.email, saved.certificationCode))
        return saved
    }
}

@Component
class CertificationEventListener(
    private val certificationService: CertificationService,
) {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    fun on(event: UserRegisteredEvent) {
        certificationService.send(event.email, event.userId, event.code)
    }
}
```

- 회원가입 트랜잭션이 **커밋된 뒤에만** 메일을 발송합니다.
- 메일 발송이 실패해도 회원가입은 유지됩니다.
- DB 커넥션이 외부 호출 동안 묶이지 않습니다.

이 패턴까지 가야 의존성 역전의 의미가 운영에서 완성됩니다. 처음 SMTP 사고가 났을 때 저는 `@Transactional(noRollbackFor = MailException::class)` 같은 우회를 먼저 떠올렸습니다. 그 우회가 늦은 판단이었습니다. 트랜잭션 안에서 외부 호출을 부르는 코드 자체를 옮겼어야 했습니다.

## 함정과 트레이드오프

운영을 해보며 부딪힌 함정 몇 가지를 짚습니다.

### 1) 인터페이스가 너무 잘게 쪼개진다

처음 의존성 역전을 적용하면 인터페이스를 너무 많이 만들고 싶어집니다. 메일·SMS·푸시·슬랙·디스코드 전부 별도 포트로. 이 정도로 잘게 쪼개면 다음이 일어납니다.

- 어댑터 클래스 수가 폭증.
- 새 외부 시스템 추가 시 인터페이스 + 어댑터 + 테스트 fake 가 한 세트로 늘어남.
- "이 인터페이스가 왜 있지?" 가 PR 리뷰에서 매번 등장.

**기준** — 도메인의 의도가 다르면 다른 포트, 같으면 같은 포트. "알림 발송" 이라는 도메인 의도가 같다면 `Notifier` 하나로 묶고, 채널은 인자 (`email | sms | push`) 로 두는 것이 결이 맞습니다.

### 2) 어댑터의 예외를 도메인 예외로 번역해야 한다

`SmtpMailSender` 가 `MailException` 을 던지면, `CertificationService` 의 호출자는 그 예외를 그대로 받습니다. 그러면 또 도메인이 `org.springframework.mail.MailException` 을 알게 됩니다.

```kotlin
// infrastructure/mail/SmtpMailSender.kt
override fun send(email: String, title: String, content: String) {
    try {
        javaMailSender.send(message)
    } catch (e: MailException) {
        throw MailSendFailedException(email, cause = e)  // 도메인 예외로 번역
    }
}
```

`MailSendFailedException` 은 도메인 쪽에 정의된 예외입니다. **어댑터는 인프라 예외를 받아 도메인 예외로 번역하는 책임까지** 가져야 추상화가 완성됩니다.

### 3) 멱등성과 재시도

외부 호출은 실패할 수 있으므로 재시도가 필요합니다. 그런데 인증 메일을 두 번 보내면 사용자는 혼란스럽습니다.

- **멱등 키 (idempotency key) 를 인터페이스에 노출** — `send(email, title, content, idempotencyKey)` 로 시그니처 확장.
- 또는 **재시도 정책을 어댑터 내부에 둠** — Retry / CircuitBreaker 는 `Resilience4j` 같은 라이브러리로.

이 부분은 처음부터 깔지 않아도 됩니다. 재시도 요구가 생기는 시점에 인터페이스를 한 번 더 다듬는 것이 자연스럽습니다.

### 4) 어댑터 통합 테스트는 따로

`FakeMailSender` 가 통과한다고 `SmtpMailSender` 가 자동으로 통과하는 것은 아닙니다.

- 어댑터 자체에 대한 통합 테스트 1~2개는 따로 둡니다 (`@SpringBootTest` 또는 GreenMail 같은 embedded SMTP).
- 어댑터 테스트는 **도메인 시나리오가 아니라 어댑터의 책임 (인프라 호출 / 예외 번역) 만** 검증합니다.

## 그래서 어떻게 시작하는가

기존 프로젝트에 적용한다면 다음 순서가 현실적입니다.

1. **가장 자주 호출되는 외부 의존 1개 선정** — 메일·결제·외부 API 중 하나.
2. **도메인 쪽에 포트 인터페이스 추출** — 메서드 시그니처는 도메인 의도만으로.
3. **인프라 쪽에 어댑터 작성** — 기존 코드 그대로 옮기기.
4. **Service 의 직접 의존을 포트로 교체** — DI 만 바꾸면 됨.
5. **`FakeXxx` 작성 후 Service 테스트를 소형으로 옮김** — 가장 큰 이득이 여기서 옵니다.

그 다음 단계로 **트랜잭션 밖으로 빼는 이벤트 패턴**을 적용하면 운영 안정성까지 따라옵니다.

## 회고 — 처음 SMTP 사고에서 비싸게 산 두 가지 교훈

처음 SMTP 사고를 겪었을 때, 저는 두 가지를 잘못 진단했습니다.

1. **"메일 라이브러리를 바꾸자"** — `JavaMailSender` 가 아니라 다른 라이브러리를 쓰면 안정적일 거라고 짐작했습니다. 문제는 라이브러리가 아니라 호출 위치였습니다.
2. **"트랜잭션 전파를 손보자"** — `@Transactional(noRollbackFor = MailException::class)` 같은 우회를 먼저 떠올렸습니다. 본질은 트랜잭션 안에서 외부 호출을 부르고 있다는 점이었고, 그 위치를 옮기는 결정이 옳았습니다.

외부 연동을 Service 가 직접 들고 있는 코드는 처음 짤 때는 가장 빠르지만, 운영에서 비용을 가장 크게 부릅니다. 인터페이스를 통한 의존성 역전은 단지 "테스트가 쉬워진다" 정도가 아니라, 외부 시스템의 흔들림이 도메인까지 번지지 않게 막아줍니다. 그 구조 위에서 이벤트 · 재시도 · 멱등성을 더 얹게 됩니다.

같은 결의 연결로 [Service 소형 테스트로 전환](/posts/service-to-small-test) 글에서는 `FakeMailSender` 가 어떻게 `@SpringBootTest` 를 걷어내는지 정리했습니다.
