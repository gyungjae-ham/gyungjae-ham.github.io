---
author: "luca"
title: "Jackson 예외를 나눠 잡기 전에 확인할 계층과 책임"
description: "DatabindException의 버전과 catch 순서를 바로잡고, 입력 오류·I/O 실패·서버 직렬화 오류를 어떤 기준으로 나눌지 설명합니다."
slug: "objectmapper-exception-hierarchy"
tags:
  [
    "학습노트",
    "spring",
    "objectmapper",
    "jackson",
    "exception-handling",
    "error-handling",
    "kotlin",
  ]
pubDatetime: 2024-12-25T12:13:00+09:00
modDatetime: 2026-10-06T18:18:44+09:00
featured: false
draft: false
---

Jackson에서 JSON 문법 오류와 객체 매핑 오류를 다르게 처리하려면 예외 계층부터 확인해야 합니다. `JsonMappingException`보다 부모인 `JsonProcessingException`을 먼저 catch하면 매핑 오류도 앞에서 잡힙니다. Java에서는 뒤 catch가 도달 불가능한 코드로 컴파일 오류가 됩니다.

[Spring MVC의 변환 경로](/posts/objectmapper-where-in-spring-mvc/)에 이어, 여기서는 Jackson 2.x를 직접 사용하는 경우를 다룹니다.

## 같은 계층이어도 처리 이유는 다를 수 있다

Jackson **2.13부터** `DatabindException`이 추가됐으며 계층은 다음과 같습니다. [DatabindException 2.13 API](https://fasterxml.github.io/jackson-databind/javadoc/2.13/com/fasterxml/jackson/databind/DatabindException.html)

```text
JsonProcessingException
  └─ DatabindException
       └─ JsonMappingException
```

두 종류를 같은 오류로 처리할 계약이라면 부모 하나를 잡을 수 있습니다. 반대로 문법 오류와 타입·필드 매핑 오류의 처리 방법이 다르면 자식을 먼저 catch하는 것이 타당합니다. catch의 개수가 설계 품질을 결정하지는 않습니다.

InputStream이나 파일에서 읽을 때의 일반 I/O 오류까지 모두 `JsonProcessingException`인 것은 아닙니다. 사용하는 `readValue` 오버로드와 입력 매체에 따라 `IOException`의 범위를 함께 봐야 합니다.

## HTTP 상태 코드는 발생 맥락으로 정한다

클라이언트가 보낸 JSON의 형식이 잘못됐다면 400 응답으로 처리할 수 있습니다. 그러나 서버의 응답 객체 직렬화가 실패하거나, 서버에 저장한 JSON과 현재 모델이 맞지 않는 문제까지 클라이언트 탓으로 돌리면 안 됩니다.

예를 들어 요청에 `age: "abc"`가 온 경우와 서버 코드의 날짜 직렬화 설정이 빠진 경우는 같은 변환 실패여도 책임이 다릅니다. 로그에는 원인을 추적할 정보를 남기되 요청 원문이나 예외 메시지의 민감한 값을 그대로 응답하지 않습니다.

## 관대한 설정도 API 계약이다

`FAIL_ON_UNKNOWN_PROPERTIES`를 끄면 알 수 없는 필드를 허용합니다. `ACCEPT_SINGLE_VALUE_AS_ARRAY`는 배열 자리에 단일 값을 받게 합니다. 이런 선택은 입력 계약을 넓히는 것이므로 예외를 줄이기 위해 일괄 적용하지 않습니다.

반복 호출을 wrapper로 모을 때도 실패를 모두 `Optional.empty()`로 바꾸면 유효한 JSON `null`과 파싱 실패를 구별하기 어려워집니다. 호출자가 복구해야 하는 이유를 예외나 명시적인 결과 타입으로 보존할지 정해야 합니다. 본문 형식과 전송 방식의 차이는 [RestClient 사례](/posts/restclient-chunked-transfer/)에서 이어집니다.
