---
author: "luca"
pubDatetime: 2023-08-16T22:18:56+09:00
modDatetime: 2026-10-13T15:32:55+09:00
title: "Spring API 오류 응답을 일관되게 만들기"
slug: "error-handling-in-spring"
featured: false
draft: false
tags: ["학습노트", "error-handling", "spring", "dto", "rest-api", "kotlin"]
description: "로그인 실패, 입력 오류, 서버 오류를 같은 형식으로 내려주되 HTTP 상태와 공개할 정보는 구분해야 합니다. MVC와 보안 필터의 처리 위치부터 살펴봅니다."
---

어떤 API는 오류를 `message`에 담고, 다른 API는 `error`에 담는다고 가정해 보겠습니다. 클라이언트는 같은 안내창을 띄우기 위해 API마다 다른 코드를 작성해야 합니다. 오류 응답 형식을 맞추려는 이유는 이런 처리를 줄이기 위해서입니다.

다만 형식을 하나로 만드는 것과 모든 예외를 같은 오류로 처리하는 것은 다릅니다. 잘못된 JSON을 보낸 요청과 DB 장애가 모두 500으로 내려오면 클라이언트도 운영자도 다음 행동을 정하기 어렵습니다. 이 글은 Spring Framework 6.x·Spring Boot 3.x에서 두 가지를 나눠 보는 학습 기록입니다.

## 같은 응답을 만드는 곳이 하나뿐이지는 않다

`@RestControllerAdvice`는 Spring MVC의 예외 처리에 사용할 수 있습니다. 잘못된 JSON, 필수 파라미터 누락, 타입 변환 실패, validation 실패처럼 요청을 처리하는 중에 생기는 오류가 대표적입니다. 이런 예외의 HTTP 의미를 유지하면서 공통 형식을 적용하려면 `ResponseEntityExceptionHandler`를 기반으로 삼을 수 있습니다. [Spring MVC 오류 응답 문서](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)

그런데 로그인하지 않은 요청은 컨트롤러에 도착하기 전에 보안 필터에서 거절될 수 있습니다. Advice 하나로 필터의 모든 예외까지 처리할 수 있다고 가정하면 이 경로의 응답만 달라집니다. 인증 진입점과 접근 거부 핸들러에서도 같은 응답 생성 규칙을 사용하도록 연결해야 합니다.

## 화면에 필요한 정보부터 정하기

다음은 설명용 오류 DTO입니다.

```kotlin
data class ApiError(
    val code: String,
    val message: String,
    val fields: List<InvalidField> = emptyList(),
)

data class InvalidField(
    val field: String,
    val reason: String,
)
```

예를 들어 이메일 형식이 틀렸다면 클라이언트는 `email` 필드 옆에 이유를 표시할 수 있습니다. 이때 입력한 값을 그대로 되돌려 줄 필요는 없습니다. 같은 처리 코드를 비밀번호 검증에도 사용한다면 `rejectedValue`에 민감한 값이 들어갈 수 있기 때문입니다. 필드명과 공개 가능한 설명을 골라 내려주는 편이 낫습니다.

알 수 없는 서버 오류에는 내부 예외 메시지나 stack trace 대신 일정한 안내를 내려줍니다. 원인을 찾을 수 있는 요청 ID를 함께 제공하고 상세 내용은 서버 로그에 남길 수 있습니다. 로그에서도 요청 본문과 비밀 값을 무조건 기록하지 않도록 해야 합니다.

새 API라면 Spring의 `ProblemDetail`도 선택지입니다. 이미 앱이 사용하는 오류 DTO가 있다면 먼저 소비자가 어떤 필드를 읽는지 확인해야 합니다. 필드 하나를 더하는 변경도 엄격한 스키마나 enum 처리를 하는 클라이언트에는 영향을 줄 수 있습니다.

## 응답과 데이터 처리는 따로 확인하기

오류를 400으로 변환했다고 DB 변경이 자동으로 롤백되는 것은 아닙니다. Spring 트랜잭션의 기본 롤백 대상은 `RuntimeException`과 `Error`이며 설정으로 바꿀 수 있습니다. HTTP 응답 정책과 트랜잭션 정책을 함께 보되 같은 기능으로 생각하면 안 됩니다.

검증할 때는 잘못된 JSON, 필드 validation 실패, 미인증, 권한 부족, 예상하지 못한 서버 오류를 각각 보내 봅니다. 응답 모양이 같은지에 더해 상태 코드가 맞는지, 내부 메시지나 입력한 비밀번호가 섞이지 않는지도 확인해야 공통 처리의 효과를 판단할 수 있습니다.
