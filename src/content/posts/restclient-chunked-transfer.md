---
author: "luca"
title: "RestClient 요청이 객체일 때만 실패한다면 본문 전송 방식도 본다"
description: "Spring 6.1·HTTP/1.1에서 버퍼링과 Content-Length가 달라지는 조건을 살펴보고, JSON 내용과 전송 방식의 문제를 구분합니다."
slug: "restclient-chunked-transfer"
tags: ["학습노트", "spring", "restclient", "http", "chunked-transfer", "kotlin"]
pubDatetime: 2024-12-25T12:14:00+09:00
modDatetime: 2026-10-06T18:18:44+09:00
featured: false
draft: false
---

외부 API에 같은 JSON을 보내는데 객체를 본문으로 넘기면 실패하고, 미리 직렬화한 문자열로 넘기면 성공하는 경우가 있었습니다. 이때 JSON 필드만 비교하면 차이를 찾기 어렵습니다. 직렬화 결과와 함께 HTTP 본문 길이를 전달하는 방식도 확인해야 합니다.

이 글은 Spring Framework 6.1의 HTTP 클라이언트와 **HTTP/1.1 전송**을 중심으로 설명합니다. 앞선 [MVC 컨버터 글](/posts/objectmapper-where-in-spring-mvc/)에서 본 `HttpMessageConverter`는 클라이언트가 요청 본문을 만드는 데에도 관여합니다.

## 본문 길이를 미리 아는가

JSON 객체를 스트림에 바로 쓰는 컨버터는 완성된 바이트 길이를 미리 제공하지 않을 수 있습니다. 반면 문자열이나 byte 배열은 선택한 인코딩으로 보낼 길이를 계산할 수 있습니다. HTTP/1.1에서는 길이가 미리 정해지지 않은 본문을 chunked 방식으로 전송할 수 있습니다.

`Content-Length`가 있다고 본문을 한 번의 네트워크 쓰기나 패킷으로 보낸다는 뜻은 아닙니다. 수신자가 본문의 총 바이트 길이를 알 수 있다는 뜻입니다. chunked는 길이가 붙은 조각과 종료 표식으로 경계를 표현합니다. [RFC 9112의 메시지 본문](https://www.rfc-editor.org/rfc/rfc9112.html#section-6)

Spring 6.1에서는 여러 요청 팩토리의 기본 버퍼링 동작이 바뀌었습니다. 그렇다고 모든 RestClient·RestTemplate 요청이 항상 chunked인 것은 아닙니다. `ClientHttpRequestFactory`, 본문 타입, 인터셉터, HTTP 버전에 따라 실제 헤더가 달라집니다. HTTP/2에는 HTTP/1.1의 chunked 코딩을 그대로 적용하지 않습니다. [Spring 6.1 이전 안내](https://github.com/spring-projects/spring-framework/wiki/Upgrading-to-Spring-Framework-6.x#upgrading-to-version-61)

## 비교할 것은 클라이언트 이름보다 실제 요청이다

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

문자 수가 아니라 실제 전송할 바이트 수를 사용하고, 길이를 계산한 바이트와 보내는 바이트를 같게 유지합니다. JSON을 보내면서 Content-Type만 `text/plain`으로 바꾸는 우회는 수신 API의 계약을 바꿀 수 있습니다.

버퍼링 팩토리를 사용하는 방법도 있지만 메모리 비용이 생깁니다. 컨버터에서 길이를 구하려고 한 번 직렬화한 뒤 전송 때 다시 직렬화하면 비용과 결과 일치 문제도 검토해야 합니다. 큰 본문이라면 전체 버퍼링보다 상대 서버의 전송 방식 지원을 고치는 편이 적합할 수 있습니다.

전송 방식 차이는 조사할 가설입니다. 특정 헤더가 없다는 사실 하나만으로 장애 원인을 확정하지 않고, 같은 본문에서 전송 방식만 바꾼 요청이 어떻게 처리되는지 확인해야 합니다.
