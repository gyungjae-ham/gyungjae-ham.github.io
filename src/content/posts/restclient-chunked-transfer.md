---
author: "luca"
title: "RestClient의 Content-Length와 chunked 전송"
description: "같은 JSON도 객체로 보낼 때와 문자열로 보낼 때 전송 방식이 달라질 수 있습니다. 요청 본문과 헤더를 함께 비교하는 방법을 정리했습니다."
slug: "restclient-chunked-transfer"
tags: ["학습노트", "spring", "restclient", "http", "chunked-transfer", "kotlin"]
pubDatetime: 2024-12-25T12:14:00+09:00
modDatetime: 2026-10-13T15:42:49+09:00
featured: false
draft: false
---

외부 API에 같은 JSON을 보내는데 객체를 본문으로 넘기면 실패하고, 미리 직렬화한 문자열로 넘기면 성공하는 경우가 있었습니다. 이때 JSON 필드만 비교하면 차이를 찾기 어렵습니다. 직렬화 결과와 함께 HTTP 본문 길이를 전달하는 방식도 확인해야 합니다.

이 글은 Spring Framework 6.1의 HTTP 클라이언트와 **HTTP/1.1 전송**을 중심으로 설명합니다. 앞선 [MVC 컨버터 글](/posts/objectmapper-where-in-spring-mvc/)에서 본 `HttpMessageConverter`는 클라이언트가 요청 본문을 만드는 데에도 관여합니다.

## JSON 내용이 같아도 길이 전달 방식은 다를 수 있다

JSON 객체를 스트림에 바로 쓰는 컨버터는 완성된 바이트 길이를 미리 제공하지 않을 수 있습니다. 반면 문자열이나 byte 배열은 선택한 인코딩으로 보낼 길이를 계산할 수 있습니다. HTTP/1.1에서는 길이가 미리 정해지지 않은 본문을 chunked 방식으로 전송할 수 있습니다.

`Content-Length`가 있다고 본문을 한 번의 네트워크 쓰기나 패킷으로 보낸다는 뜻은 아닙니다. 수신자가 본문의 총 바이트 길이를 알 수 있다는 뜻입니다. chunked는 길이가 붙은 조각과 종료 표식으로 경계를 표현합니다. [RFC 9112의 메시지 본문](https://www.rfc-editor.org/rfc/rfc9112.html#section-6)

Spring 6.1에서는 여러 요청 팩토리의 기본 버퍼링 동작이 바뀌었습니다. 그렇다고 모든 RestClient·RestTemplate 요청이 항상 chunked인 것은 아닙니다. `ClientHttpRequestFactory`, 본문 타입, 인터셉터, HTTP 버전에 따라 실제 헤더가 달라집니다. HTTP/2에는 HTTP/1.1의 chunked 코딩을 그대로 적용하지 않습니다. [Spring 6.1 이전 안내](https://github.com/spring-projects/spring-framework/wiki/Upgrading-to-Spring-Framework-6.x#upgrading-to-version-61)

## 성공한 요청과 실패한 요청을 같은 조건으로 비교하기

이런 호환성 문제를 확인할 때는 성공·실패 요청의 메서드, URL, Content-Type, Content-Length, Transfer-Encoding과 최종 바이트 내용을 같은 조건에서 비교합니다. 서버 앞의 프록시가 본문을 어떻게 처리하는지도 범위에 포함합니다.

상대 서버가 길이를 미리 알아야 하는 경우에는 작은 JSON을 한 번 직렬화한 byte 배열로 보내는 방법이 있습니다. 아래는 Spring 6.1·Jackson 2.x에서 핵심 호출만 남긴 예시입니다.

```kotlin
val body = objectMapper.writeValueAsBytes(payload)
restClient.post()
    .uri(endpoint)
    .contentType(MediaType.APPLICATION_JSON)
    .contentLength(body.size.toLong())
    .body(body)
    .retrieve()
    .toBodilessEntity()
```

예를 들어 본문에 한글이 들어 있으면 문자열의 글자 수와 UTF-8 바이트 수는 다릅니다. 그래서 `payload.toString().length` 같은 값 대신 실제 전송할 byte 배열의 길이를 사용합니다. 길이를 계산한 바이트와 보내는 바이트가 같아야 합니다. JSON을 보내면서 Content-Type만 `text/plain`으로 바꾸면 수신 서버가 본문을 해석하는 방식까지 달라질 수 있습니다.

버퍼링 팩토리를 사용하는 방법도 있지만 메모리 비용이 생깁니다. 컨버터에서 길이를 구하려고 한 번 직렬화한 뒤 전송 때 다시 직렬화하면 비용과 결과 일치 문제도 검토해야 합니다. 큰 본문이라면 전체 버퍼링보다 상대 서버의 전송 방식 지원을 고치는 편이 적합할 수 있습니다.

객체 요청이 실패하고 문자열 요청이 성공한다는 현상만으로 chunked가 원인이라고 확정할 수는 없습니다. 우선 실제 전송 바이트가 같은지 확인하고, 그다음 길이 전달 방식만 바꿔 비교해야 합니다. 그래야 직렬화 문제를 전송 문제로 잘못 판단하는 일을 줄일 수 있습니다.
