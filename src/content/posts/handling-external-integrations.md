---
author: "luca"
pubDatetime: 2023-06-28T14:47:45+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "외부 연동을 다루는 방법 — 의존성 역전으로 테스트 가능한 구조 만들기"
slug: "handling-external-integrations"
featured: false
draft: false
tags:
  [
    "학습노트",
    "architecture",
    "external-api",
    "testing",
    "dependency-injection",
    "spring",
    "kotlin",
  ]
description: "회원가입과 인증 메일 예시로 테스트 의존성 분리, 커밋 후 실행, 발송 누락 복구를 구분합니다. AFTER_COMMIT만으로 해결되지 않는 자원 수명과 내구성도 다룹니다."
---

회원가입에서 인증 메일을 보낸다고 해보겠습니다. 사용자를 저장한 다음 SMTP를 호출하면 코드의 순서는 간단합니다. 하지만 DB 트랜잭션 안에서 메일 서버를 기다리면 응답이 느려지고, 발송 예외가 전파되면 사용자 저장도 롤백될 수 있습니다. 반대로 메일은 전송됐는데 DB 커밋이 실패하는 경우도 가능합니다.

여기에는 서로 다른 두 문제가 있습니다. 메일 내용을 외부 서버 없이 테스트하는 문제와, 저장·발송의 성공을 어떻게 연결할지 정하는 문제입니다. 인터페이스를 추출하면 첫 문제를 풀기 쉬워지지만 두 번째 문제까지 자동으로 해결되지는 않습니다.

## 메일 내용은 네트워크 없이 확인할 수 있다

설명용 코드에서는 회원가입 쪽이 필요한 기능을 작은 인터페이스로 표현합니다.

```kotlin
data class Mail(val to: String, val subject: String, val body: String)

fun interface MailSender {
    fun send(mail: Mail)
}

class CertificationService(private val sender: MailSender) {
    fun send(email: String, verificationUrl: String) {
        sender.send(Mail(email, "이메일 인증", "인증 링크: $verificationUrl"))
    }
}
```

운영 어댑터는 이 값을 `JavaMailSender`에 전달합니다. 테스트에서는 보낸 값을 목록에 기록하는 대역이나 Mockito의 argument captor로 수신자·제목·본문을 검증할 수 있습니다. `JavaMailSender`를 직접 mock하는 것도 가능하므로, 인터페이스를 반드시 만들어야 테스트할 수 있는 것은 아닙니다. 추출의 이점은 애플리케이션이 메일 라이브러리의 구체적인 타입을 덜 알게 된다는 데 있습니다.

실제 인증 URL의 생성·만료·일회성 사용 정책은 별도 책임입니다. 메일 내용 검증이 SMTP 연결이나 인증 토큰의 안전성까지 검증하는 것은 아닙니다.

## AFTER_COMMIT이 보장하는 범위

`@TransactionalEventListener(phase = AFTER_COMMIT)`은 트랜잭션 커밋이 성공한 뒤 리스너를 실행합니다. 이미 커밋된 회원가입을 메일 발송 실패가 되돌리지는 않습니다.

하지만 **이 애너테이션만으로 실행이 비동기가 되거나 DB 커넥션이 먼저 반환되지는 않습니다.** 기본 동기 리스너는 호출 스레드에서 실행되고, 커밋 후 콜백 시점에도 트랜잭션 자원이 접근 가능한 상태일 수 있습니다. [Spring 6.1 TransactionalEventListener](https://docs.spring.io/spring-framework/docs/6.1.21/javadoc-api/org/springframework/transaction/event/TransactionalEventListener.html)

또한 인메모리 이벤트에는 내구성이 없습니다. DB 커밋 직후 프로세스가 종료되면 발송을 놓칠 수 있습니다. 단순히 `@Async`를 더해도 큐에 작업을 넘기기 전의 장애나 재시도·중복 처리 문제는 남습니다.

## 발송 누락을 복구해야 한다면

사용자 저장과 함께 ‘발송할 메일’ 레코드를 같은 DB 트랜잭션에 쓰고, 별도 워커가 이를 읽어 보내는 outbox 방식을 검토할 수 있습니다. 워커는 전송 상태와 재시도 횟수를 기록합니다. 전송 성공 직후 상태 기록 전에 죽을 수 있으므로 중복 전송 가능성도 다뤄야 합니다. 제공자가 멱등 키를 지원하는지, 동일 인증 링크의 재발송을 허용할지 같은 정책이 필요합니다.

이 방식은 테이블·워커·복구 절차가 추가되는 비용이 있습니다. 일회성 알림인지, 누락을 반드시 복구해야 하는 통지인지에 따라 선택합니다. 테스트에서도 메일 내용, DB 커밋 여부, 발송 실패 후 재처리를 각각 확인해야 책임이 섞이지 않습니다.

대역을 선택하는 기준은 [테스트 대역의 역할](/posts/test-doubles-concept/)에서 이어서 정리합니다.
