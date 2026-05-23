---
author: "luca"
title: "RestClient 청크 전송이 외부 협력사를 만났을 때 — Spring 6.1 의 메모리 최적화가 만든 사이드 이펙트"
description: "Spring 의 RestClient · RestTemplate 이 객체를 직렬화하면 Transfer-Encoding: chunked 로 전송하는데, 청크 전송을 지원하지 않는 외부 협력사에서 본문이 비어 보이는 사건. 6.1 의 메모리 최적화 한 줄이 어디서 어떻게 빠졌는지 따라가봅니다."
slug: "restclient-chunked-transfer"
tags: ["spring", "restclient", "http", "chunked-transfer", "kotlin"]
pubDatetime: 2024-12-25T12:14:00+09:00
modDatetime: 2026-05-23T00:00:00+09:00
featured: false
draft: false
---

> 이 글은 ObjectMapper 시리즈 3편 중 3편 입니다. 1편은 ObjectMapper 의 자리(slug: objectmapper-where-in-spring-mvc), 2편은 예외 계층의 오해(slug: objectmapper-exception-hierarchy)를 다뤘습니다.

Spring 6.1 릴리즈 노트 한 줄("Content-Length 헤더 미세팅") 이 외부 협력사 통신을 끊었습니다. 프레임워크의 메모리 최적화는 항상 *프로토콜의 어느 헤더가 사라진다는 의미* 와 함께 본다 가 그 사건 후의 교훈입니다. 같은 요청을 객체로 보내면 본문이 비어 도착하고, `String` 으로 감싸 보내면 정상 도착하는 결이었습니다. 처음에는 직렬화 결과를 의심했지만, 한 번 더 들여다보니 본문의 *내용* 이 아니라 본문이 *어떻게 실려 가는가* 의 문제였고, 그러고는 라이브러리보다 헤더부터 봤어야 했다는 사실이 분명해졌습니다.

## 사건 — 같은 페이로드, 다른 결과

상황은 단순했습니다. 같은 페이로드를 같은 외부 협력사 엔드포인트로 보내는데 클라이언트별로 결과가 달랐습니다.

- **`WebClient` · `RestClient` · `RestTemplate`**: 외부 협력사가 "본문이 비어 있다" 는 에러 응답을 돌려줌
- **`OkHttp` · `HttpURLConnection` · `OpenFeign`**: 정상 처리됨
- **같은 Spring 클라이언트로도, 객체 대신 `String` 직렬화 결과를 본문으로 넣으면 정상**

이 세 줄이 동시에 성립한다는 게 핵심이었습니다. 한쪽 클라이언트가 통째로 망가졌다면 라이브러리 버그를 의심했겠지만, 같은 클라이언트라도 본문을 `String` 으로 감싸면 멀쩡했습니다. 그 자리에서 멈춰 생각하면 **직렬화 결과 자체는 깨지지 않았다** 는 신호고, 본문이 어떻게 패킹되어 송신되는가의 차이가 남는 후보였습니다.

## 원인 — Transfer-Encoding: chunked

패킷을 뜯어보면 차이는 한 자리에서 명확해졌습니다. 객체를 그대로 보내면 `Transfer-Encoding: chunked` 로 청크 단위로 끊어 보내고, `String` 을 그대로 보내면 `Content-Length` 와 함께 한 번에 본문 전체가 실립니다. 이 차이는 어떤 `HttpMessageConverter` 가 본문을 만드는지에서 갈리는 결이었습니다.

- **객체 → JSON**: `MappingJackson2HttpMessageConverter` 가 처리. `getContentLength()` 가 `null` 반환.
- **String → 본문**: `StringHttpMessageConverter` 가 처리. `getContentLength()` 가 바이트 길이 반환.

`StringHttpMessageConverter` 의 구현은 짧고 분명합니다. 본문의 바이트 길이를 그 자리에서 돌려주는 모양입니다.

```java
public class StringHttpMessageConverter extends AbstractHttpMessageConverter<String> {
    protected Long getContentLength(String str, MediaType contentType) {
        Charset charset = this.getContentTypeCharset(contentType);
        return (long) str.getBytes(charset).length;
    }
}
```

반면 `MappingJackson2HttpMessageConverter` 는 `AbstractJackson2HttpMessageConverter` 를 통해 부모의 `getContentLength()` 를 그대로 받습니다. 그 부모는 한 줄짜리입니다.

```java
public abstract class AbstractHttpMessageConverter<T> implements HttpMessageConverter<T> {
    protected Long getContentLength(T t, MediaType contentType) throws IOException {
        return null;
    }
}
```

`null` 이 반환된다는 말은 본문의 바이트 길이를 미리 알 수 없다 라는 신호 입니다. 클라이언트는 이 신호를 받아 `Content-Length` 헤더를 빼고, 대신 `Transfer-Encoding: chunked` 로 전환합니다. JDK 의 `Http1Request` 가 헤더를 만드는 자리를 보면 이 분기가 그대로 박혀 있습니다. `contentLength > 0` 이면 `Content-Length` 를, 아니면 `streaming = true` 와 함께 `Transfer-encoding: chunked` 를 채우는 코드입니다. HTTP/1.1 의 청크 전송이 바로 이 자리에서 시작됩니다. HTTP/2 는 이미 프레임 기반 스트리밍이라 같은 결의 사이드 이펙트가 일어나지 않습니다.

## Spring 6.1 릴리즈 노트의 한 줄

이 동작은 Spring 6.1 의 메모리 최적화에서 비롯됩니다. 릴리즈 노트는 다음 세 줄로 요약됩니다.

- `RestClient` 와 `RestTemplate` 의 구현체는 요청 바디를 더 이상 사전 버퍼에 담지 않는다.
- 따라서 `Content-Length` 헤더가 사전에 세팅되지 않는다.
- 결과적으로 본문은 `chunked` 로 흘러간다.

이전 버전은 본문을 모두 메모리에 모은 다음 길이를 측정해 `Content-Length` 를 박았습니다. 6.1 부터는 그 메모리 비용을 빼고 스트리밍으로 보내는 결입니다. 메모리 사용량은 줄고, HTTP/1.1 의 기본 동작에는 충실합니다. 다만 HTTP/1.0 만 지원하거나 청크 전송을 받지 못하도록 막아둔 협력사가 존재하면 본문이 어디서 끝나는지 알 길이 없으니, 협력사 서버는 본문을 비어 있는 것으로 처리하고 연결을 닫습니다. `OkHttp` · `HttpURLConnection` · `OpenFeign` 이 멀쩡해 보였던 이유는 그쪽이 본문을 일단 버퍼링해서 `Content-Length` 를 채운 뒤 보냈기 때문이고, 상대 서버가 청크 전송을 정말로 막아 두었다면 그쪽 클라이언트들도 똑같이 실패했을 가능성이 큽니다.

## 회피 방법 셋

청크 전송 자체를 피하고 싶을 때 선택지는 세 가지입니다. 셋 모두 본질은 같습니다. "본문 길이를 사전에 알 수 있게 만든다" 입니다. 메모리 최적화를 양보하고 호환성을 얻는 거래이고, 어느 쪽을 고를지는 상대 서버의 제약과 본문 크기 분포에 달려 있습니다.

| 방법 | 어떻게 | 트레이드오프 |
|---|---|---|
| **컨버터 오버라이드** | `MappingJackson2HttpMessageConverter.getContentLength()` 를 직렬화된 바이트 길이로 오버라이드해서 `RestClient` 에 등록 | 한 번 직렬화한 결과를 길이 측정용으로 메모리에 잡아 둠. 가장 일반적인 우회. |
| **`text/plain` + `ObjectToStringHttpMessageConverter`** | 객체를 문자열로 변환하는 컨버터로 받게 `Content-Type` 을 바꿈 | 사실상 클라이언트 측에서 `String` 으로 직렬화하는 것과 같음. JSON 의미를 잃을 수 있음. |
| **`BufferingClientHttpRequestFactory`** | `ClientHttpRequestFactory` 를 버퍼링 팩토리로 감싸 본문을 전부 버퍼에 모은 뒤 길이 계산 | 메모리 사용량 증가. 큰 본문에서는 GC 부담. 6.1 이전 동작으로 되돌리는 셈. |

본문이 항상 수십 KB 이내라면 `BufferingClientHttpRequestFactory` 가 가장 변경이 적어 편하고, 본문이 크고 가변적이라면 컨버터 오버라이드가 메모리 부담을 가장 덜 줍니다. `text/plain` 으로 우회하는 방법은 JSON 의미를 잃기 때문에 협력사 스펙이 단순 텍스트를 받는 자리에서만 의미가 있습니다.

## 정리

한쪽 클라이언트는 되고 다른 쪽은 안 된다면, 그건 메시지 본문이 아니라 프로토콜의 어느 헤더가 누락됐다는 신호 입니다. 직렬화 결과를 다시 살펴보기 전에 패킷의 헤더를 먼저 봐야 합니다. `Content-Length` 가 있는지, `Transfer-Encoding: chunked` 가 박혀 있는지 한 줄이면 진단이 끝나는 자리고, 그러고는 릴리즈 노트의 메모리 최적화 한 줄이 *어느 헤더를 빼앗아 갔는가* 를 함께 보는 습관이 그 사건 후에 남았습니다.
