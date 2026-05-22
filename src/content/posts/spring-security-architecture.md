---
author: "luca"
pubDatetime: 2023-08-08T11:40:25+09:00
title: "스프링 시큐리티 주요 아키텍처"
slug: "spring-security-architecture"
featured: false
draft: false
tags: ["spring-security", "architecture", "authentication", "authorization"]
description: "FilterChainProxy부터 Authentication, SecurityContext, AccessDecisionManager까지 스프링 시큐리티 내부 구조의 흐름을 정리합니다."
---

> 이 시리즈는 Spring Security 학습 후 기록하는 시리즈입니다. Spring Security 5.7 기준으로 작성했으며, 현재 6.x 버전과 설정 방법은 다르지만 개념적 이해는 동일하므로 5.7로 진행했습니다.

## FilterChainProxy

1. `springSecurityFilterChain` 이라는 이름으로 생성되는 필터 빈입니다.
2. `DelegatingFilterProxy` 로부터 요청을 위임받아 실제 보안 처리를 수행합니다.
3. 스프링 시큐리티 초기화 시 생성되는 필터들을 관리하고 제어합니다.
    - 스프링 시큐리티가 기본적으로 생성하는 필터
    - 설정 클래스에서 API 추가 시 생성되는 필터
4. 사용자의 요청을 필터 순서대로 호출하여 전달합니다.
5. 사용자 정의 필터를 만들어 기존 필터의 전·후로 추가할 수 있습니다.
    - 이때 필터의 순서를 잘 정의해야 합니다.
6. 마지막 필터까지 인증·인가 예외가 발생하지 않으면 보안이 통과됩니다.

## 필터 초기화와 다중 설정 클래스

- 설정 클래스 별로 보안 기능이 각각 작동합니다.
- 설정 클래스 별로 `RequestMatcher` 를 설정합니다.
    - 예: `http.antMatcher("/admin/**")`
- 설정 클래스 별로 필터가 생성됩니다.
- `FilterChainProxy` 가 각 필터들을 가지고 있습니다.
- 요청에 따라 `RequestMatcher` 와 매칭되는 필터가 작동합니다.

## Authentication

- 접근하려는 사람이 누구인지 증명하는 것입니다.
- 사용자의 인증 정보를 저장하는 토큰 개념입니다.
- 인증 시 id와 password를 담아 인증 검증을 위해 전달됩니다.
- 인증 후 최종 인증 결과(**user 객체, 권한 정보**)를 담고 **`SecurityContext` 에 저장되어 전역적으로 참조 가능**합니다.

```java
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
```

구조는 다음과 같습니다.

1. **principal** — 사용자 아이디 혹은 `User` 객체를 저장
2. **credentials** — 사용자 비밀번호
3. **authorities** — 인증된 사용자의 권한 목록
4. **details** — 인증 부가 정보
5. **Authenticated** — 인증 여부

## SecurityContextHolder, SecurityContext

### SecurityContext

- `Authentication` 객체가 저장되는 보관소로, 필요할 때 언제든 `Authentication` 객체를 꺼내 쓸 수 있도록 제공되는 클래스입니다.
- `ThreadLocal` 에 저장되어 아무 곳에서나 참조가 가능하도록 설계되어 있습니다.
- 인증이 완료되면 `HttpSession` 에 저장되어 어플리케이션 전반에 걸쳐 전역적인 참조가 가능합니다.

### SecurityContextHolder

`SecurityContext` 객체 저장 방식은 세 가지가 있습니다.

- `MODE_THREADLOCAL` — 스레드 당 `SecurityContext` 객체를 할당 (기본값)
- `MODE_INHERITABLETHREADLOCAL` — 메인 스레드와 자식 스레드가 동일한 `SecurityContext` 를 유지
- `MODE_GLOBAL` — 응용 프로그램에서 단 하나의 `SecurityContext` 를 저장

`SecurityContextHolder.clearContext()` 를 호출하면 기존 `SecurityContext` 정보가 초기화됩니다.

```java
Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
```

## SecurityContextPersistenceFilter

**`SecurityContext` 객체의 생성·저장·조회를 담당하는 필터**입니다.

- **익명 사용자**
    - 새로운 `SecurityContext` 객체를 생성하여 `SecurityContextHolder` 에 저장합니다.
    - `AnonymousAuthenticationFilter` 에서 `AnonymousAuthenticationToken` 객체를 `SecurityContext` 에 저장합니다.
- **인증 시**
    - 새로운 `SecurityContext` 객체를 생성하여 `SecurityContextHolder` 에 저장합니다.
    - `UsernamePasswordAuthenticationFilter` 에서 인증 성공 후 `UsernamePasswordAuthentication` 객체를 `SecurityContext` 에 저장합니다.
    - 인증이 최종 완료되면 `Session` 에 `SecurityContext` 를 저장합니다.
- **인증 후**
    - `Session` 에서 `SecurityContext` 를 꺼내 `SecurityContextHolder` 에 저장합니다.
    - `SecurityContext` 안에 `Authentication` 객체가 존재하면 계속 인증을 유지합니다.
- **최종 응답 시 공통**
    - `SecurityContextHolder.clearContext()` 가 호출됩니다.

## Authentication Flow

### AuthenticationManager

- `AuthenticationProvider` 목록 중에서 인증 처리 요건에 맞는 `AuthenticationProvider` 를 찾아 인증 처리를 위임합니다.
- 부모 `ProviderManager` 를 설정하여 `AuthenticationProvider` 를 계속 탐색할 수 있습니다.

### AuthenticationProvider

- `AuthenticationProvider` 는 인터페이스이고, 어플리케이션에 맞게 커스텀하게 구현해서 사용하는 경우가 많습니다.
- 두 가지 메서드를 가지고 있습니다.
    - `authenticate` — 인증을 위해 검증하는 메서드
    - `supports` — 인증을 처리할 수 있는 기준이 되는지 확인하는 메서드

### Authorization

- 사용자에게 어떤 것이 허가되었는지 증명하는 것을 의미합니다.

#### 스프링 시큐리티가 지원하는 권한 계층

- **웹 계층** — URL 요청에 따른 메뉴 혹은 화면 단위의 레벨 보안
- **서비스 계층** — 화면 단위가 아닌 메서드 같은 기능 단위의 레벨 보안
- **도메인 계층 (Access Control List, 접근 제어 목록)** — 객체 단위의 레벨 보안

### FilterSecurityInterceptor

- 마지막에 위치한 필터로, 인증된 사용자에 대해 특정 요청의 승인/거부 여부를 최종적으로 결정합니다.
- 인증 객체 없이 보호 자원에 접근을 시도할 경우 `AuthenticationException` 을 발생시킵니다.
- 인증 후 자원에 접근 가능한 권한이 존재하지 않을 경우 `AccessDeniedException` 을 발생시킵니다.
- 권한 제어 방식 중 HTTP 자원의 보안을 처리하는 필터입니다.
- 권한 처리를 `AccessDecisionManager` 에게 위임합니다.

### AccessDecisionManager

- 인증 정보, 요청 정보, 권한 정보를 이용해 사용자의 자원 접근을 허용할 것인지 거부할 것인지를 최종 결정하는 주체입니다.
- 여러 개의 `Voter` 를 가질 수 있으며, `Voter` 들로부터 접근 허용·거부·보류 값을 리턴받아 판단·결정합니다.
- 최종 접근 거부 시 예외가 발생합니다.

#### 접근 결정의 세 가지 유형

- **AffirmativeBased** — 여러 `Voter` 중 하나라도 접근 허가로 결론을 내면 접근 허가로 판단합니다.
- **ConsensusBased** — 다수표(승인 및 거부)에 의해 최종 결정을 판단합니다. 동수일 경우 기본은 접근 허가이지만, `allowIfEqualGrantedDeniedDecisions` 를 `false` 로 설정하면 접근 거부로 결정됩니다.
- **UnanimousBased** — 모든 `Voter` 가 만장일치로 접근을 승인해야 하며, 그렇지 않은 경우 접근을 거부합니다.

### AccessDecisionVoter

- 판단을 심사하는 위원의 역할을 수행합니다.
- `Voter` 가 권한 부여 과정에서 판단하는 자료는 다음과 같습니다.
    - `Authentication` — 인증 정보 (user)
    - `FilterInvocation` — 요청 정보 (`antMatcher("/user")`)
    - `ConfigAttributes` — 권한 정보 (`hasRole("USER")`)
- 결정 방식
    - `ACCESS_GRANTED` — 접근 허용 (1)
    - `ACCESS_DENIED` — 접근 거부 (0)
    - `ACCESS_ABSTAIN` — 접근 보류 (-1). `Voter` 가 해당 타입의 요청에 대해 결정을 내릴 수 없는 경우입니다.

## 스프링 시큐리티 필터 및 아키텍처 정리

### 초기화 과정

1. `Config` 에 설정한 내용을 토대로 사용할 `HttpSecurity` 가 `Filter` 들을 구성합니다 (**Security 초기화**).
2. `WebSecurity` 가 `HttpSecurity` 에서 설정한 `filter` 들의 정보를 전달받은 후, `FilterChainProxy` 의 빈 객체(`springSecurityFilterChain`)를 생성할 때 해당 `filter` 들을 인자로 넘겨서 생성합니다.
3. `DelegatingFilterProxy` 는 `springSecurityFilterChain` 이라는 특정 이름의 빈을 찾고, 사용자의 요청을 해당 빈에 위임합니다.

### 인증을 시도하는 경우 (Form 로그인 예시)

1. `DelegatingFilterProxy` 가 사용자의 인증 요청을 받아 `FilterChainProxy` 에 위임합니다.
2. `FilterChainProxy` 는 초기화 과정에서 관련 `filter` 들의 목록을 가지고 있으므로, 위임을 받으면 해당 필터들을 순서대로 호출합니다.
3. 인증의 경우 가장 먼저 `SecurityContextPersistenceFilter` 가 사용자 요청을 받고, 내부의 `HttpSessionSecurityContextRepository` 가 로직을 수행합니다. 우선 `loadContext` 를 실행해 이전에 생성된 `context` 가 있는지 확인하고, 없으면 새 `context` 를 생성한 뒤 다음 필터로 넘어갑니다.
4. `LogoutFilter` 는 로그아웃 요청이 없다면 별다른 작업 없이 다음 필터로 넘어갑니다.
5. 인증을 담당하는 필터(예시에서는 `UsernamePasswordAuthenticationFilter`)가 사용자에게 입력받은 정보를 담아 인증 객체(`Authentication`)를 생성한 뒤, `AuthenticationManager` 에게 인증을 요청합니다. `AuthenticationManager` 는 `AuthenticationProvider` 에게 실질적인 인증 로직을 위임합니다.
6. `AuthenticationProvider` 는 `UserDetailsService` 를 통해 해당 정보의 유효성을 검사하고, 인증이 완료된 정보일 경우 `SecurityContextHolder` 의 `SecurityContext` 안에 인증된 `Authentication` 객체를 저장합니다.
7. 인증 후처리로 `SessionManagementFilter` 의 내용을 수행합니다. `ConcurrentSession` 을 확인해 세션 최대 허용 개수를 초과하는 경우 두 전략 중 하나를 선택합니다.
    - **현재 사용자 인증 시도 차단** — `SessionAuthenticationException`
    - **이전 사용자 세션 만료 설정** — `session.expireNow`

    그 다음 `SessionFixation` 에서 세션 고정 보호를 위해 새롭게 인증된 사용자에게 새 쿠키를 발급합니다. 마지막으로 `Register SessionInfo` 에서 해당 사용자의 정보가 세션에 등록됩니다.
8. 최종적으로 `SecurityContextPersistenceFilter` 의 `HttpSessionSecurityContextRepository` 가 최종 인증된 사용자 정보를 담은 `SecurityContext` 를 `Session` 에 저장하고, 해당 `SecurityContext` 는 삭제합니다.

### 인가의 경우

1. `DelegatingFilterProxy` 가 사용자의 요청을 받아 `FilterChainProxy` 에 위임합니다.
2. `FilterChainProxy` 는 관련 `filter` 들의 목록을 가지고 있으므로, 위임을 받으면 해당 필터들을 순서대로 호출합니다.
3. `SecurityContextPersistenceFilter` 는 `HttpSessionSecurityContextRepository` 가 `loadContext` 를 실행하도록 합니다. 이전 인증으로 `Session` 에 저장된 `SecurityContext` 가 존재하므로 새로 생성하지 않고 다음 필터로 넘어갑니다.
4. `LogoutFilter` 와 인증 필터는 지나갑니다 (인가 처리이므로).
5. `ConcurrentSessionFilter` 또한 동시 세션을 처리하기 위한 필터이고, 현재는 동시 세션 검증을 통과한 인증된 사용자이므로 지나갑니다.
6. `RememberMeAuthenticationFilter` 는 현재 사용자의 `Session` 이 만료되거나 유실되어 `SecurityContext` 안의 `Authentication` 객체 값이 `null` 인 상태에서 `header` 에 `remember-me` 값을 가지고 있을 때 작동하는 필터이므로 지나갑니다.
7. `AnonymousAuthenticationFilter` 는 현재 사용자가 인증을 시도하지 않고 어떠한 권한도 없는 상태에서 바로 자원을 요청하는 경우에 동작하는 필터이므로 지나갑니다.
8. `SessionManagementFilter` 는 현재 요청의 `Session` 에 `SecurityContext` 가 없거나 `null` 일 경우 동작하는 필터이므로 마찬가지로 지나갑니다.
9. `ExceptionTranslationFilter` 는 인증·인가의 예외 처리를 하는 필터이므로, `doFilter` 메서드를 try-catch 문으로 감싼 후 다음 필터로 이동합니다.
10. `FilterSecurityInterceptor` 는 현재 요청에서 두 가지를 확인합니다.
    1. 먼저 인증 객체를 가지고 있는지 확인하고, 없다면 즉시 `AuthenticationException` 을 발생시킵니다 (예외는 이전 `ExceptionTranslationFilter` 에서 처리합니다).
    2. 인증 객체를 지니고 있다면 `AccessDecisionManager` 가 `AccessDecisionVoter` 의 승인·거부 결과를 받아 거부라면 `AccessDeniedException` 을 발생시킵니다.
11. 권한 검증에 문제가 없다면 자원에 접근하도록 허용합니다.
