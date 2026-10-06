---
author: "luca"
pubDatetime: 2023-08-16T22:18:56+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Spring 에서 Error 응답을 일관되게 다루는 방법"
slug: "error-handling-in-spring"
featured: false
draft: false
tags: ["학습노트", "error-handling", "spring", "dto", "rest-api", "kotlin"]
description: "Spring MVC와 보안 필터의 오류 처리 범위를 구분하고, 예상 4xx와 서버 오류를 일관되게 응답합니다. 민감한 입력값 노출과 API 호환성도 함께 다룹니다."
---

API마다 오류 응답의 필드가 다르면 클라이언트가 같은 실패를 여러 방식으로 처리해야 합니다. 응답 형식을 맞추되, 잘못된 입력과 서버의 예기치 않은 실패를 같은 500으로 묶지 않는 것이 출발점입니다.

이 글은 Spring Framework 6.x·Spring Boot 3.x 기준입니다. 자체 DTO를 유지할 수도 있고, Spring의 `ProblemDetail`을 바탕으로 HTTP 오류를 표현할 수도 있습니다. 이미 공개된 응답 계약이 있다면 먼저 클라이언트의 사용 방식을 확인합니다.

## Advice가 처리하는 범위부터 정한다

`@RestControllerAdvice`는 Spring MVC의 예외 처리 경로에서 동작합니다. 필터나 Spring Security에서 발생하는 모든 예외를 자동으로 받는 것은 아닙니다. 인증 진입점·접근 거부 핸들러와 MVC 처리에서 공통 응답 생성 규칙을 공유할 수는 있습니다.

MVC에는 JSON 파싱 실패, 필수 파라미터 누락, 타입 변환 실패, validation 실패처럼 예상 가능한 4xx가 있습니다. catch-all을 추가하기 전에 이 예외들의 기본 HTTP 의미를 보존해야 합니다. `ResponseEntityExceptionHandler`는 이런 MVC 예외를 일관되게 다루는 기반으로 사용할 수 있습니다. [Spring MVC 오류 응답](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)

## 클라이언트에 돌려줄 정보만 선택한다

설명용 오류 DTO는 다음처럼 최소한으로 시작할 수 있습니다.

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

validation 오류를 변환할 때 `rejectedValue`를 그대로 넣지 않습니다. 비밀번호나 토큰을 검증하던 요청이라면 응답에 그 값이 노출될 수 있습니다. 필드명과 공개 가능한 이유만으로 화면 표시가 가능한지 먼저 봅니다. 예외 메시지나 요청 본문을 로그에 남길 때도 같은 기준을 적용합니다.

예기치 않은 서버 오류에는 고정된 안내와 요청을 추적할 ID를 제공할 수 있습니다. 상세 원인과 stack trace는 적절히 통제된 서버 로그에 남깁니다. 반면 비즈니스 오류는 발생 빈도와 운영 대응 필요에 따라 로그·알림 수준을 정합니다. 모든 4xx가 무시할 오류이거나 모든 비즈니스 예외가 warn이어야 하는 것은 아닙니다.

## 응답 변경과 롤백 정책은 별도로 본다

새 선택 필드를 추가하는 것은 많은 클라이언트에서 호환 가능하지만, 엄격한 스키마나 enum 처리에서는 깨질 수 있습니다. 모든 필드 추가가 반드시 v2를 요구하는 것도, 항상 안전한 것도 아닙니다. 계약 테스트와 실제 소비자를 확인합니다.

Spring 트랜잭션의 기본 롤백은 RuntimeException과 Error에 적용되며 설정으로 바꿀 수 있습니다. HTTP 응답 코드를 정하는 것과 DB 변경을 롤백할지 정하는 것은 서로 다른 정책입니다.

최소 확인 사례로는 잘못된 JSON의 400, validation 실패의 필드 정보, 미인증·권한 부족의 의도한 응답, 알 수 없는 오류의 500을 둘 수 있습니다. 이때 입력값과 내부 예외 메시지가 응답에 섞이지 않는지도 함께 검사합니다.
