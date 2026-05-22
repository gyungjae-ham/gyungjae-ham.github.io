---
author: "luca"
pubDatetime: 2023-08-16T17:11:38+09:00
title: "CORS"
slug: "cors"
featured: false
draft: false
tags: ["cors", "spring", "security", "web"]
description: "SOP·CORS·Preflight Request의 정의와 브라우저가 사전 요청을 보내는 이유, 단순 요청 조건까지 정리한 학습 노트입니다."
---

> CORS 설정과 관련해 정리하는 글이며, 이후에 내용이 추가될 수 있습니다.

## WebConfig CORS 설정

- **SOP(Same Origin Policy)** — 어떤 출처에서 다른 출처의 리소스를 사용하는 것을 제한하는 보안 방식입니다. 브라우저는 기본적으로 다른 출처에서 오는 요청을 공격 시도로 간주하기 때문에 적용된 정책입니다.
- Origin 예시 — `http://localhost:8082` (프로토콜 + 호스트 + 포트).

  > `http://localhost:8082` 에서 `http://localhost:8080/api/health` 를 호출하는 경우 Origin이 다르므로 브라우저 단에서 에러가 발생합니다.

- **CORS(Cross-Origin Resource Sharing)** — 다른 출처에 리소스를 공유하는 것을 의미합니다.

## Preflight Request (사전 요청)

- 웹 브라우저는 기본적으로 `cross origin` 요청에 대해, 실제 `HTTP` 요청을 보내기 전 서버 측에서 해당 요청을 허용하는지 확인하는 **Preflight Request(사전 요청)** 를 보냅니다.
- **Preflight Request** 는 `HTTP OPTIONS` 메서드를 사용합니다.
- CORS 오류는 웹 브라우저 단에서 발생하기 때문에 서버는 정상적으로 요청을 처리했지만 클라이언트에서는 오류가 난 것처럼 보이는 상황이 발생할 수 있습니다. **Preflight Request** 는 이런 상황을 사전에 차단하기 위한 확인 절차입니다.

### Preflight Request 생략

모든 요청이 `Preflight` 를 발생시키는 것은 아닙니다. 아래 조건을 모두 만족하는 요청은 **단순 요청(Simple Request)** 으로 분류되어 `Preflight` 가 생략됩니다.

- **HTTP Method** — `GET`, `HEAD`, `POST`
- 수동으로 설정한 헤더가 `Accept`, `Accept-Language`, `Content-Language`, `Content-Type` 중 하나일 것
- 단, `Content-Type` 헤더의 값은 `application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain` 중 하나일 때에만 `Preflight` 가 발생하지 않습니다.

이 조건에서 하나라도 벗어나면 브라우저는 어김없이 `OPTIONS` 사전 요청을 먼저 보냅니다.
