---
author: "luca"
title: "@RequestBody는 언제 ObjectMapper를 호출할까"
description: "Spring MVC의 인자 해석기와 HttpMessageConverter를 따라 JSON이 DTO가 되는 과정을 살펴보고, 변환 예외를 처리할 위치를 구분합니다."
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
modDatetime: 2026-10-06T18:18:44+09:00
featured: false
draft: false
---

컨트롤러의 `@RequestBody`에는 JSON 문자열 대신 DTO가 들어옵니다. 변환에 실패하면 컨트롤러 메서드의 `try/catch`까지 도달하지 않을 수도 있습니다. Spring MVC가 메서드를 호출하기 전에 인자를 만들기 때문입니다.

이 글은 Spring Framework 6.1·Jackson 2.x의 JSON 요청 경로를 기준으로 합니다. 이어지는 글은 [Jackson 예외 계층](/posts/objectmapper-exception-hierarchy/)과 [RestClient의 본문 전송 방식](/posts/restclient-chunked-transfer/)입니다.

## 컨트롤러 호출 전에 일어나는 일

`RequestResponseBodyMethodProcessor` 같은 인자 해석기가 `@RequestBody`를 처리합니다. 요청의 Content-Type과 대상 Java 타입을 바탕으로 읽을 수 있는 `HttpMessageConverter`를 찾습니다. JSON이면 보통 `MappingJackson2HttpMessageConverter`가 선택되고, 이 컨버터가 Jackson의 `ObjectReader`를 사용해 본문을 객체로 읽습니다.

```text
HTTP 요청 본문
  → @RequestBody 인자 해석
  → 타입·Content-Type에 맞는 HttpMessageConverter
  → Jackson ObjectReader
  → DTO 생성
  → 컨트롤러 메서드 호출
```

항상 바이트 전체를 JSON 문자열로 만든 뒤 읽는 것은 아닙니다. UTF-8 등 지원 인코딩에서는 InputStream을 직접 읽는 경로가 있고, 다른 인코딩에서는 Reader를 사용할 수 있습니다. 컨버터 선택과 JSON 해석을 구분해야 흐름을 정확히 볼 수 있습니다.

`StreamUtils.nonClosing`도 이름을 잘 읽어야 합니다. 이는 `close()`를 호출해도 원래 스트림을 닫지 않는 래퍼입니다. 블로킹 I/O를 비차단 방식으로 바꾸는 기능이 아닙니다. [Spring StreamUtils API](https://docs.spring.io/spring-framework/docs/6.1.21/javadoc-api/org/springframework/util/StreamUtils.html)

## 어느 위치에서 예외를 처리할까

JSON 문법·매핑 오류는 Spring MVC에서 `HttpMessageNotReadableException` 같은 예외로 변환될 수 있습니다. 아직 컨트롤러 인자를 만드는 중이므로 메서드 내부의 catch로 잡으려 하지 않고 MVC 예외 처리 경로에서 응답 정책을 정합니다.

반대로 서비스가 파일·캐시·메시지 큐의 JSON을 직접 `ObjectMapper.readValue()`로 읽는다면 그 호출의 계약에 맞게 예외를 처리해야 합니다. ObjectMapper는 HTTP 전용 도구가 아닙니다. 일반적인 JPA 컬럼 매핑은 JDBC와 ORM이 담당하지만, JSON 컬럼용 사용자 변환기에서 ObjectMapper를 쓸 수도 있습니다.

따라서 먼저 확인할 것은 예외를 던진 실제 호출 위치입니다. 프레임워크가 요청 본문을 읽다 실패한 것인지, 애플리케이션이 보관된 JSON을 직접 읽다 실패한 것인지에 따라 클라이언트 오류와 서버 데이터 문제의 구분도 달라집니다.
