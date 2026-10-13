---
author: "luca"
title: "Spring MVC에서 JSON이 요청 DTO로 바뀌는 과정"
description: "잘못된 JSON을 보내면 왜 컨트롤러의 catch에 들어오지 않을까요. @RequestBody 인자를 만드는 순서에서 예외 처리 위치를 찾아봅니다."
slug: "objectmapper-where-in-spring-mvc"
tags:
  [
    "학습노트",
    "spring",
    "objectmapper",
    "jackson",
    "http-message-converter",
    "kotlin",
  ]
pubDatetime: 2024-12-25T12:12:47+09:00
modDatetime: 2026-10-13T15:32:55+09:00
featured: false
draft: false
---

컨트롤러에서 `@RequestBody`로 DTO를 받으면 JSON을 직접 파싱하지 않아도 됩니다. 그래서 JSON 변환 오류도 컨트롤러 안에서 처리하면 될 것처럼 보입니다. 하지만 잘못된 JSON을 보냈을 때 메서드 내부의 `try/catch`가 실행되지 않는 경우가 있습니다.

이유는 메서드가 호출되는 순서에 있습니다. Spring MVC는 먼저 요청 본문을 읽어 DTO를 만든 뒤, 그 DTO를 인자로 넘겨 컨트롤러를 호출합니다. 변환에 실패하면 아직 컨트롤러에 들어오지도 못한 상태입니다. 아래 설명은 Spring Framework 6.1과 Jackson 2.x를 기준으로 합니다.

## ObjectMapper 앞에 있는 처리 단계

예를 들어 나이를 숫자로 받는 DTO에 `{"age": "abc"}`를 보냈다고 해보겠습니다. 요청은 대략 다음 순서를 거칩니다.

```text
HTTP 요청 본문
  → @RequestBody 인자 해석
  → Content-Type과 대상 타입에 맞는 HttpMessageConverter 선택
  → Jackson으로 JSON 읽기
  → DTO 생성
  → 컨트롤러 호출
```

`@RequestBody`는 `RequestResponseBodyMethodProcessor` 같은 인자 해석기가 처리합니다. 이 단계에서 요청의 Content-Type과 대상 Java 타입을 보고 본문을 읽을 수 있는 컨버터를 찾습니다. 일반적인 JSON 요청에는 `MappingJackson2HttpMessageConverter`가 사용되고, 내부에서는 Jackson의 `ObjectReader`로 값을 읽습니다.

따라서 컨버터를 고르는 일과 JSON의 필드를 DTO에 맞추는 일은 다른 단계입니다. 앞선 예시는 JSON 문법 자체는 맞지만 숫자로 바꿀 수 없는 값을 보냈으므로 매핑 과정에서 실패할 수 있습니다.

본문을 항상 하나의 문자열로 만든 뒤 읽는 것도 아닙니다. 지원하는 인코딩에서는 InputStream을 직접 읽고, 다른 경로에서는 Reader를 사용할 수 있습니다. 소스를 따라가다 나오는 `StreamUtils.nonClosing`은 원본 스트림이 닫히지 않도록 감싸는 기능입니다. 이름의 `non`을 보고 비차단 I/O로 이해하면 흐름을 잘못 읽게 됩니다. [Spring StreamUtils API](https://docs.spring.io/spring-framework/docs/6.1.21/javadoc-api/org/springframework/util/StreamUtils.html)

## 오류를 처리할 위치도 호출 위치에 따라 달라진다

요청 본문을 읽다 생긴 JSON 문법·매핑 오류는 MVC에서 `HttpMessageNotReadableException` 같은 예외로 전달될 수 있습니다. 아직 컨트롤러 호출 전이므로 `@RestControllerAdvice` 등 MVC의 예외 처리 경로에서 응답을 정해야 합니다.

반면 서비스 코드가 캐시에 저장된 JSON을 `ObjectMapper.readValue()`로 직접 읽는 경우는 다릅니다. 이때 실패한 데이터는 사용자의 현재 요청이 아니라 서버가 보관한 값일 수 있습니다. 무조건 400으로 응답하면 서버 데이터 문제를 클라이언트 탓으로 돌리게 됩니다.

같은 Jackson 예외라도 먼저 호출한 위치를 확인해야 하는 이유입니다. 요청을 DTO로 바꾸다 실패했는지, 애플리케이션이 저장한 데이터를 읽다 실패했는지를 알아야 처리 방식도 정할 수 있습니다. 예외 종류는 [Jackson 예외 계층](/posts/objectmapper-exception-hierarchy/)에서 이어서 다룹니다.
