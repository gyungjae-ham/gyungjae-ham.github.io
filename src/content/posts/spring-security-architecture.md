---
author: "luca"
pubDatetime: 2023-08-08T11:40:25+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "스프링 시큐리티 주요 아키텍처"
slug: "spring-security-architecture"
featured: false
draft: false
tags:
  [
    "학습노트",
    "spring-security",
    "architecture",
    "authentication",
    "authorization",
  ]
description: "FilterChainProxy부터 Authentication, SecurityContext, AccessDecisionManager까지 스프링 시큐리티 내부 구조의 흐름을 정리합니다."
---

로그인 요청과 이미 로그인한 사용자의 조회 요청은 Spring Security에서 다른 일을 합니다. 전자는 자격 증명을 확인해 인증 결과를 만들고, 후자는 그 인증으로 해당 자원에 접근해도 되는지 판단합니다.

이 글은 **Spring Security 5.7의 Servlet 기반 구성**, 특히 `FilterSecurityInterceptor`와 voter 방식의 인가를 학습한 기록입니다. 6.x에는 AuthorizationManager 기반 구성과 컨텍스트 저장 방식의 차이도 있으므로 클래스 흐름을 그대로 옮기지 않습니다.

## 요청은 어떤 보안 체인을 지나는가

Servlet 컨테이너의 `DelegatingFilterProxy`가 Spring 빈인 `FilterChainProxy`로 요청을 넘깁니다. 여러 SecurityFilterChain이 있으면 요청에 맞는 첫 체인을 선택하고 그 안의 필터를 순서대로 실행합니다. 모든 체인의 필터를 합쳐 실행하는 것은 아닙니다.

폼 로그인에서는 인증 필터가 사용자 입력으로 미인증 `Authentication`을 만들고 `AuthenticationManager`에 전달합니다. 대표 구현인 `ProviderManager`는 지원하는 `AuthenticationProvider`에 검증을 위임합니다. provider가 인증 결과를 반환하면 호출한 인증 필터가 성공 처리를 하며 SecurityContext에 반영합니다. provider 자체가 항상 컨텍스트 저장을 담당하는 것은 아닙니다.

## SecurityContext는 모든 사용자가 공유하는 전역 값이 아니다

SecurityContext는 Authentication을 보관하고, SecurityContextHolder의 기본 전략은 ThreadLocal입니다. 요청 스레드에서 참조할 수 있다는 뜻이지 다른 사용자나 비동기 스레드에 무조건 공유된다는 뜻은 아닙니다.

세션에 저장하는 구성에서는 요청을 시작할 때 컨텍스트를 읽고 끝날 때 저장·정리합니다. stateless 구성은 다르게 동작합니다. 요청 처리가 끝난 뒤 스레드의 컨텍스트를 정리해야 스레드 재사용 시 인증 정보가 남지 않습니다. 세션과 현재 스레드의 보관소를 구분해야 합니다.

## voter의 표를 어떻게 합치는가

5.7의 `AccessDecisionVoter` 상수는 다음과 같습니다. [공식 소스](https://github.com/spring-projects/spring-security/blob/5.7.13/core/src/main/java/org/springframework/security/access/AccessDecisionVoter.java)

| 상수             | 값  | 의미          |
| ---------------- | --- | ------------- |
| `ACCESS_GRANTED` | 1   | 허용          |
| `ACCESS_DENIED`  | -1  | 거부          |
| `ACCESS_ABSTAIN` | 0   | 판단하지 않음 |

`AffirmativeBased`는 하나라도 허용하면 승인합니다. `ConsensusBased`는 허용·거부 표의 다수를 보고, 동수 정책을 별도로 둡니다. `UnanimousBased`는 거부가 있으면 거절하며 모든 voter가 허용해야 하는 방식은 아닙니다. 전원 abstain일 때는 별도 정책이 적용되고 기본은 거부입니다. [UnanimousBased 구현](https://github.com/spring-projects/spring-security/blob/5.7.13/core/src/main/java/org/springframework/security/access/vote/UnanimousBased.java)

마지막으로 `ExceptionTranslationFilter`는 뒤쪽 처리에서 올라오는 인증·접근 거부 예외를 HTTP 응답으로 연결합니다. 로그인 시작을 담당하는 entry point와 권한 부족을 처리하는 handler를 구분합니다. 이 흐름은 모든 애플리케이션 예외를 처리하는 전역 catch가 아닙니다.

실제 요청을 볼 때는 선택된 체인, Authentication이 만들어지는 곳, 컨텍스트 저장 정책, 인가 결과의 순서로 따라가면 됩니다. 설정별 동작은 [기본 보안 API](/posts/spring-security-basic-api-and-filter/)에서 이어집니다.
