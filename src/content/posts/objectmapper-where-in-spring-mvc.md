---
author: "luca"
title: "ObjectMapper 는 Spring MVC 어디에 살고 있는가 — HttpMessageConverter 의 자리"
description: "@RequestBody 가 바이트 스트림을 객체로 만들 때 ObjectMapper 만 일하는 게 아닙니다. HttpMessageConverter 가 어디서 바이트 스트림을 받고, 어디서 ObjectMapper 를 호출하는지 정리합니다."
slug: "objectmapper-where-in-spring-mvc"
tags: ["spring", "objectmapper", "jackson", "http-message-converter", "kotlin"]
pubDatetime: 2024-12-25T12:12:47+09:00
modDatetime: 2026-05-23T00:00:00+09:00
featured: false
draft: false
---

> 이 글은 ObjectMapper 시리즈 3편의 1편입니다. ObjectMapper 가 Spring MVC 의 어느 자리에 살고 있는지부터 짚고, 2편에서는 예외 계층의 오해를, 3편에서는 RestClient 의 청크 전송 사이드 이펙트를 다룹니다.

그때는 "ObjectMapper 는 try-catch 로 감싸야 안전하다" 고 믿었습니다. 지금 보면 "Spring MVC 가 이미 ObjectMapper 를 컨버터로 감싸서 글로벌 예외 핸들러로 흘려보내고 있다" 는 사실을 먼저 확인하는 게 순서였습니다. 매번 `objectMapper.readValue()` 를 try-catch 로 두르고 있었던 이유는 단순했습니다. 라이브러리가 어디서 호출되는지 보지 않은 채로 코드를 짰기 때문입니다.

## Controller 의 @RequestBody — 누가 무엇을 하나

`@RequestBody` 가 붙은 컨트롤러 메서드에 요청이 도착하면 흐름은 네 단계로 나뉩니다.

- **1단계 — Content-Type 확인**: `DispatcherServlet` 이 요청 헤더의 `Content-Type` 을 읽고, 어느 컨버터가 이 요청을 받을 수 있는지 결정합니다.
- **2단계 — HttpMessageConverter 선택**: `application/json` 이라면 `MappingJackson2HttpMessageConverter` 가 후보로 선택됩니다.
- **3단계 — 바이트 스트림을 JSON 문자열로**: 컨버터가 `ServletInputStream` 에서 바이트를 읽고, `InputStreamReader` 로 JSON 문자열을 만듭니다.
- **4단계 — JSON 문자열을 객체로**: 컨버터 내부에서 `ObjectMapper.readValue()` 가 호출되어 역직렬화가 일어납니다.

여기서 핵심은 **ObjectMapper 가 직접 컨트롤러 메서드에서 호출되는 게 아니라, 컨버터 안쪽 깊은 곳에서 호출된다** 는 사실입니다. 컨트롤러 메서드가 호출되는 시점에는 이미 객체가 완성되어 있고, 그 과정에서 발생한 예외는 컨트롤러 메서드 바깥에서 던져집니다.

## HttpMessageConverter 의 자리

바이트 스트림을 JSON 으로 바꾸는 책임의 진짜 주인은 `HttpMessageConverter` 입니다. `MappingJackson2HttpMessageConverter` 는 그 구현체 중 하나이고, 내부적으로 `ObjectMapper` 를 가지고 있습니다.

`AbstractJackson2HttpMessageConverter.readJavaType()` 의 일부를 보면 역할이 명확해집니다.

```java
private Object readJavaType(JavaType javaType, HttpInputMessage inputMessage) throws IOException {
    MediaType contentType = inputMessage.getHeaders().getContentType();
    Charset charset = this.getCharset(contentType);
    ObjectMapper objectMapper = this.selectObjectMapper(javaType.getRawClass(), contentType);
    Assert.state(objectMapper != null, () -> "No ObjectMapper for " + javaType);

    try {
        InputStream inputStream = StreamUtils.nonClosing(inputMessage.getBody());
        // ObjectMapper 가 inputStream 을 읽어 객체를 만듭니다
    }
}
```

- 컨버터가 `Content-Type` 으로 `ObjectMapper` 를 고르고,
- `InputStream` 을 비차단으로 감싸고,
- 그 위에서 `ObjectMapper` 를 호출합니다.

즉 **ObjectMapper 는 컨버터의 도구일 뿐, 컨버터가 모든 입출력 책임을 진다** 가 정확한 표현입니다. 여기서 발생한 `JsonProcessingException` 은 컨트롤러 메서드에 닿기 전에 Spring MVC 의 `HttpMessageNotReadableException` 으로 감싸지거나 그대로 전파됩니다. `@RestControllerAdvice` 가 받아내는 자리가 바로 그곳입니다.

## DB 통신에는 ObjectMapper 가 동작하지 않습니다

직렬화·역직렬화라는 단어만 보고 "그럼 DB 와 통신할 때도 ObjectMapper 가 끼는 건가?" 라고 생각하기 쉽지만, 그렇지 않습니다. 짧게 정리하면 다음과 같습니다.

- **HTTP JSON**: `HttpMessageConverter` 의 `MappingJackson2HttpMessageConverter` 가 받고, 내부에서 `ObjectMapper` 가 변환합니다.
- **JPA**: `EntityManager` 와 Hibernate 가 JDBC 결과를 엔티티로 매핑합니다. `ObjectMapper` 는 관여하지 않습니다.
- **MyBatis**: SQL 결과를 `ResultMap` 으로 객체에 바인딩합니다. 이쪽도 `ObjectMapper` 는 빠져 있습니다.

요약: `ObjectMapper` 의 직무는 **HTTP 본문과 객체 사이의 JSON 변환** 으로 한정됩니다.

## 그래서 어떻게 시작하는가

Jackson 예외를 매번 직접 잡고 싶어진다면, 그건 Spring MVC 가 이미 같은 일을 하고 있다는 신호일 가능성이 높습니다. `objectMapper.readValue()` 한 줄을 try-catch 로 감싸기 전에, 그 코드가 컨버터의 내부에서 호출되고 있는지 컨트롤러 진입점에서 직접 호출되고 있는지부터 봅니다.

옛 글에는 "ObjectMapper 는 try-catch 가 안전하다" 고 적었는데, 실제로는 "ObjectMapper 가 호출되는 자리에 따라 try-catch 의 필요성 자체가 달라진다" 가 더 정확합니다. 컨트롤러 진입점이라면 글로벌 예외 핸들러가 받습니다. 직접 주입받아 쓰는 자리라면 그때 비로소 try-catch 가 의미를 가집니다.

한 줄 조언: ObjectMapper 의 try-catch 를 쓰기 전에, 그 ObjectMapper 가 호출되는 자리부터 본다.

다음 글에서는 그 try-catch 안에서 잡고 있던 예외 두 개가 실제로는 부모-자식 관계였다는 사실을 정리합니다 (slug: objectmapper-exception-hierarchy).
