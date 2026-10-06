---
author: "luca"
pubDatetime: 2023-06-19T00:00:52+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "개념, 대역 — 테스트가 빌려 쓰는 가짜들"
slug: "test-doubles-concept"
featured: false
draft: false
tags: ["학습노트", "testing", "test-double", "mock", "stub", "fake"]
description: "인증 메일과 회원가입 예시로 기록용 대역, mock, 상태를 가진 fake를 비교합니다. 대역이 확인하는 계약과 실제 인프라 검증의 범위를 구분합니다."
---

회원가입 후 인증 메일을 보낸다고 해보겠습니다. ‘메일이 발송됐는가’라는 테스트 이름 아래에서도 확인하려는 것은 다를 수 있습니다. 본문에 올바른 링크가 들어가는지, 발송 요청이 한 번만 나가는지, SMTP 서버가 실제 메일을 받는지는 각각 다른 검증입니다.

대역의 용어는 [짧은 분류표](/posts/test-double-basics/)에 정리했습니다. 여기서는 무엇을 확인할지에 따라 대역을 고르는 과정을 봅니다.

## 내용을 확인하려면 보낸 값을 잡는다

수신자와 본문을 기록하는 작은 객체를 만들면 테스트가 그 목록을 검사할 수 있습니다. 아래는 기록 역할만 가진 spy 예시입니다.

```kotlin
fun interface MailSender {
    fun send(to: String, body: String)
}

class RecordingMailSender : MailSender {
    val sent = mutableListOf<Pair<String, String>>()
    override fun send(to: String, body: String) {
        sent += to to body
    }
}
```

Mockito의 argument captor나 인자 matcher로도 같은 내용을 확인할 수 있습니다. 기록 객체만 본문을 검증할 수 있는 것은 아닙니다. 두 방식 모두 외부로 보내려던 호출을 확인하는 것이며, 목록을 읽었다고 검증 대상이 실제 SMTP 전송으로 넓어지지는 않습니다.

## 저장 후 조회가 여러 번 이어진다면

회원가입 뒤 동일 이메일로 다시 가입하는 시나리오에서는 저장된 상태를 다음 조회가 읽어야 합니다. Map을 사용하는 fake는 이 흐름을 간단하게 표현합니다. mock의 연속 응답이나 answer로도 가능하지만 여러 테스트에서 반복되면 상태를 가진 구현이 읽기 쉬울 수 있습니다.

대신 fake가 실제 저장소와 얼마나 같은지 관리해야 합니다. Map은 DB의 unique 제약·격리 수준·락을 재현하지 않습니다. fake를 정교한 가짜 DB로 키우기보다 해당 동작은 실제 DB 테스트로 확인하는 편이 낫습니다.

## 테스트 문법과 개발 방식은 구분한다

`given/when/then`은 사전 조건·행동·결과를 읽기 좋게 나누는 표현 방식입니다. 이 주석을 썼다고 BDD 전체를 적용한 것은 아닙니다. BDD는 관계자들이 예시를 통해 기대 동작을 함께 정하는 과정도 포함합니다.

fixture 역시 매 테스트마다 새로 만들면 해당 객체의 상태는 분리되지만, static 값·캐시·DB·외부 파일까지 자동으로 초기화되지는 않습니다. 테스트 간 독립성은 실제로 공유하는 자원의 범위에서 확인합니다.

대역을 고를 때는 만들기 쉬운 도구보다 확인하려는 계약을 먼저 봅니다. 메일 본문을 확인하는 테스트와 실제 메일 어댑터의 연결을 확인하는 테스트를 구분하면 한 테스트에 불필요한 환경을 모두 얹지 않아도 됩니다.
