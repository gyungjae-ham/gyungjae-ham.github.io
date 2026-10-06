---
author: "luca"
pubDatetime: 2023-08-16T17:11:38+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "CORS"
slug: "cors"
featured: false
draft: false
tags: ["학습노트", "cors", "spring", "security", "web"]
description: "SOP·CORS·Preflight Request의 정의와 브라우저가 사전 요청을 보내는 이유, 단순 요청 조건까지 정리한 학습 노트입니다."
---

프런트엔드를 `http://localhost:8082`, API를 `http://localhost:8080`에서 실행하면 포트가 달라 서로 다른 출처입니다. 브라우저에서 API 호출이 실패하는데 서버 로그에는 요청이 보일 수 있습니다. CORS를 이해할 때는 **요청이 전송되는 것과 JavaScript가 응답을 읽는 것**을 구분해야 합니다.

동일 출처 정책(SOP)은 다른 출처의 데이터에 스크립트가 자유롭게 접근하지 못하도록 제한합니다. 다른 출처의 모든 요청을 공격으로 간주해 전송 자체를 막는 규칙은 아닙니다. 이미지 로드나 폼 제출처럼 교차 출처 전송이 가능한 경우도 있습니다.

## 사전 요청이 있는 경우와 없는 경우

CORS 프로토콜은 서버가 특정 출처에 응답 접근을 허용하는 방법입니다. 예를 들어 브라우저에서 `Content-Type: application/json`인 POST를 보내면 보통 실제 요청 전에 `OPTIONS` 사전 요청을 보냅니다. 서버가 출처·메서드·헤더를 허용하는지 확인하는 단계입니다.

반면 CORS의 safelist 조건에 맞는 GET·HEAD·POST 등은 사전 요청 없이 전송될 수 있습니다. 이때 CORS 응답 헤더가 없으면 서버가 처리를 끝냈어도 JavaScript는 응답을 읽지 못합니다. 따라서 CORS를 부작용 있는 요청의 인증이나 CSRF 방어로 대신할 수 없습니다.

일반적인 safelist 조건에는 메서드 외에 헤더 이름·값·길이 제한도 있습니다. `Content-Type`은 `application/x-www-form-urlencoded`, `multipart/form-data`, `text/plain` 등이 해당하며, 모든 GET이 무조건 사전 요청을 생략하는 것도 아닙니다. 자세한 조건은 [Fetch 표준의 CORS 프로토콜](https://fetch.spec.whatwg.org/#http-cors-protocol)을 기준으로 확인합니다.

## 실패 지점을 나눠서 본다

브라우저 개발자 도구에서 `OPTIONS`만 보이면 사전 요청의 상태 코드와 허용 헤더부터 봅니다. 실제 요청까지 보이면 응답의 `Access-Control-Allow-Origin` 등을 확인합니다. 쿠키를 포함하는 요청은 클라이언트의 credentials 설정과 서버의 credentials 허용이 맞아야 하며, 이 경우 허용 출처에 `*`를 사용할 수 없습니다.

`curl`에서 성공한다는 사실은 API가 응답한다는 증거입니다. 브라우저의 CORS 정책까지 통과했다는 증거는 아니므로 실제 프런트엔드 출처에서도 확인해야 합니다.
