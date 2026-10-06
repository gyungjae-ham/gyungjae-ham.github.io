---
author: "luca"
pubDatetime: 2023-06-22T14:14:32+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "레이어별 테스트 — Repository, Service, Controller 를 어디까지 어떻게"
slug: "layered-testing-strategy"
featured: false
draft: false
tags:
  [
    "학습노트",
    "testing",
    "unit-test",
    "integration-test",
    "spring",
    "controller-test",
  ]
description: "규칙·DB·HTTP·빈 연결에서 찾을 실패를 기준으로 테스트 환경을 고릅니다. 웹 슬라이스의 보안 필터, 테스트 롤백 범위와 컨텍스트 캐시도 함께 다룹니다."
---

주문 기능을 테스트할 때 모든 케이스에서 웹 서버와 DB를 띄울 필요는 없습니다. 반대로 Service 계산만 통과했다고 실제 요청·저장까지 검증된 것도 아닙니다. 어떤 실패를 찾으려는지에 따라 테스트 환경을 고릅니다.

| 확인할 동작                | 시작할 수 있는 구성        | 남는 범위                    |
| -------------------------- | -------------------------- | ---------------------------- |
| 할인·만료 같은 규칙        | 객체를 직접 만든 테스트    | Spring 설정과 저장소         |
| JPA 매핑·조회              | `@DataJpaTest`와 테스트 DB | 웹 요청·외부 연동            |
| 요청 변환·검증·응답        | `@WebMvcTest`와 MockMvc    | 실제 네트워크·대체한 Service |
| 실제 빈의 연결과 주요 흐름 | `@SpringBootTest`          | 환경에 따라 외부 시스템      |

이 글의 애너테이션 설명은 Spring Boot 3.x를 기준으로 합니다. 컨텍스트를 좁히는 것은 테스트가 검증할 범위를 명확히 하는 선택이지, 모든 통합 테스트를 최소 개수로 줄이라는 규칙은 아닙니다.

## Repository는 저장소의 의미를 확인한다

조건 없는 조회보다 상태 필터, 정렬 동률, null, 중복 결과처럼 쿼리의 의도가 드러나는 데이터를 준비합니다. DB에 실제로 쓰였는지 보려면 [flush 후 재조회](/posts/datajpatest-feature/)를 사용합니다.

H2와 MySQL의 SQL·락 동작이 같다고 가정하지 않습니다. 사용하는 DB 엔진과 버전의 테스트 인스턴스를 마련하면 검증 범위를 맞추기 쉽습니다. 기본 테스트 롤백은 해당 테스트 트랜잭션을 정리할 뿐, 별도 스레드·다른 트랜잭션·외부 캐시까지 초기화하지는 않습니다.

## Service는 결과와 실패 정책을 확인한다

협력자는 [mock이나 fake](/posts/test-doubles-concept/)로 대체할 수 있습니다. 이메일의 본문·횟수는 두 방식 모두 검증 가능합니다. 기록 목록을 읽는 검증과 mock의 인자 검증을 본질적으로 다른 수준의 신뢰라고 보지 않습니다.

대역을 쓰는 테스트에서는 실제 DB 제약, 트랜잭션, 메일 프로토콜을 검증하지 않습니다. 이런 조건은 별도 통합 테스트에서 확인합니다. 시간과 생성값의 경계가 중요하면 [Clock 같은 입력](/posts/dependency-and-testability/)을 제어합니다.

## 웹 테스트에도 보안 필터가 들어올 수 있다

`@WebMvcTest`는 MVC 슬라이스와 함께 Spring Security 구성을 포함할 수 있습니다. 서비스 빈을 대체했다고 인증·인가가 없어지는 것은 아닙니다. 프로젝트의 `SecurityFilterChain`을 필요한 범위로 가져오고, 인증 사용자와 권한, CSRF가 필요한 요청을 명시합니다.

예를 들어 인증된 POST의 검증은 `user(...)` 또는 `@WithMockUser`로 사용자를 제공하고, CSRF가 켜져 있다면 `csrf()`를 추가하는 방식입니다. 반대로 미인증 요청과 권한 부족 요청이 의도한 401·403 또는 리다이렉트로 처리되는지도 따로 확인합니다. MVC 단독 설정의 기본 예시는 [Controller 테스트](/posts/writing-controller-tests/)에 있습니다.

## 실행 시간은 컨텍스트 재사용을 고려한다

Spring은 동일한 설정의 테스트 컨텍스트를 캐시합니다. 매 테스트 메서드가 전체 애플리케이션을 다시 부팅하는 것은 아닙니다. 서로 다른 mock 빈 구성이나 `@DirtiesContext` 등이 재사용에 미치는 영향을 살펴봐야 합니다. [Spring TestContext 캐시](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/caching.html)

CI에서는 빠른 규칙 테스트와 필요한 통합 검증을 묶되, 중요한 회귀가 머지 전에 발견되도록 배치합니다. 느리다는 이유만으로 핵심 통합 시나리오를 전부 야간으로 미루기보다 준비 비용과 실제 검증 시간을 먼저 분리해 봅니다.
