---
author: "luca"
pubDatetime: 2023-08-03T17:13:14+09:00
title: "Spring Security 기본 API 및 Filter 이해"
slug: "spring-security-basic-api-and-filter"
featured: false
draft: false
tags: ["spring-security", "filter", "authentication", "web-security"]
description: "Form Login·Logout·Remember Me·세션 제어·CSRF까지 Spring Security 5.7의 주요 API와 Filter 흐름을 정리한 학습 노트입니다."
---

> 이 시리즈는 Spring Security 학습 후 기록하는 시리즈입니다. Spring Security 5.7 기준으로 작성했으며, 현재 6.x 버전과 설정 방법은 다르지만 개념적 이해는 동일하므로 5.7로 진행했습니다.

## 시리즈에서 다루는 내용

1. 스프링 시큐리티의 보안 설정 API와 이와 연계된 각 `Filter` 학습
    - 각 API의 개념과 사용법, 처리 과정, 동작 방식
    - API 설정 시 생성·초기화되어 사용자의 요청을 처리하는 `Filter`
2. 스프링 시큐리티 내부 아키텍처와 각 객체의 역할 및 처리 과정 학습
    - 초기화 과정, 인증 과정, 인가 과정 등
3. 인증 기능 구현 — Form 방식, Ajax 인증 처리
4. 인가 기능 구현 — DB와 연동한 권한 제어 시스템 (URL 방식, Method 방식)

## 스프링 시큐리티 의존성 추가

### 의존성 추가 시 일어나는 일들

- **서버가 기동되면 스프링 시큐리티의 초기화 작업과 보안 설정이 이루어집니다.**
- **별도의 설정이나 구현 없이도 기본적인 웹 보안 기능이 현재 시스템에 연동되어 작동합니다.**
    1. 모든 요청은 인증되어야 자원에 접근 가능합니다.
    2. 인증 방식은 폼 로그인 방식과 `httpBasic` 로그인 방식을 제공합니다.
    3. 기본 로그인 페이지를 제공합니다.
    4. 기본 계정 한 개를 제공합니다 — `user`, 랜덤 문자열 비밀번호.

## 인증 API

### Form Login

- `http.formLogin()` — Form 로그인 인증 기능이 작동합니다.
- `.loginPage("/login.html")` — 사용자 정의 로그인 페이지
- `.defaultSuccessUrl("/home")` — 로그인 성공 후 이동 페이지
- `.failureUrl("/login.html?error=true")` — 로그인 실패 후 이동 페이지
- `.usernameParameter("username")` — 아이디 파라미터명 설정
- `.passwordParameter("password")` — 패스워드 파라미터명 설정
- `.loginProcessingUrl("/login")` — 로그인 Form Action URL
- `.successHandler(loginSuccessHandler())` — 로그인 성공 후 핸들러
- `.failureHandler(loginFailureHandler())` — 로그인 실패 후 핸들러

### 인증 처리 흐름

1. `UsernamePasswordAuthenticationFilter` 를 시작으로 인증 처리가 시작됩니다.
2. `AntPathRequestMatcher(/login)` 에서 요청 정보가 매칭되는지 확인합니다. `/login` 부분은 `loginProcessingUrl` 설정으로 변경 가능합니다.
3. 요청 정보가 매칭되지 않으면 `chain.doFilter` 로 다음 필터가 수행되고, 매칭되면 `Authentication` 으로 넘어갑니다.
4. `Authentication` 단계에서는 유저가 입력한 `username` 과 `password` 로 `Authentication` 객체를 생성하고, 이를 `AuthenticationManager` 에 인증 요청합니다.
5. `AuthenticationManager` 는 인증을 `AuthenticationProvider` 에 위임하며, 여기서 인증에 실패하면 `AuthenticationException` 이 반환됩니다. 이 예외에 대한 후처리는 별도로 진행합니다.
6. 인증에 성공하면 `AuthenticationProvider` 는 user 객체 정보와 `authority` 권한 정보를 담은 `Authentication` 객체를 생성해 `AuthenticationManager` 에 다시 반환합니다.
7. `AuthenticationManager` 는 `AuthenticationProvider` 에게 받은 최종 인증 객체를 다시 `UsernamePasswordAuthenticationFilter` 에 반환합니다.
8. `UsernamePasswordAuthenticationFilter` 는 `User` 객체 정보와 `Authorities` 정보를 담은 최종 `Authentication` 객체를 만들어 `SecurityContext` 에 저장합니다.
    - `SecurityContext` 는 인증 객체를 저장하는 보관소입니다.
    - 이후 `SecurityContext` 는 `Session` 에 저장되어 전역적으로 사용 가능합니다.
9. 마지막으로 `SuccessHandler` 가 성공 후처리를 수행합니다.

### FilterChainProxy

- 여러 필터를 가지고 있는 클래스입니다.
- 우리가 설정한 값에 맞게 필터를 구성해 순서대로 실행합니다.
- 예를 들어 `formLogin()` 을 설정한 경우 다음 순서로 필터가 실행됩니다.
    1. `WebAsyncManagerIntegrationFilter`
    2. `SecurityContextPersistenceFilter`
    3. `HeaderWriterFilter`
    4. `CsrfFilter`
    5. `LogoutFilter`
    6. `UsernamePasswordAuthenticationFilter`
    7. `DefaultLoginPageGeneratingFilter`
    8. `DefaultLogoutPageGeneratingFilter`
    9. `SecurityContextHolderAwareRequestFilter`
    10. `AnonymousAuthenticationFilter`
    11. `SessionManagementFilter`
    12. `ExceptionTranslationFilter`
    13. `FilterSecurityInterceptor`

### Logout

유저로부터 로그아웃 요청을 받으면 Spring Security는 **세션을 무효화**하고, 사용자가 로그인할 때 생성한 인증 객체 토큰을 삭제하며, 인증 객체가 저장되어 있는 `SecurityContext` 객체도 삭제합니다. 쿠키가 설정되어 있다면 쿠키 정보 또한 삭제한 후 로그인 페이지로 리다이렉트합니다.

#### Logout API

- `http.logout()` — 로그아웃 기능이 작동합니다.
- `.logoutUrl("/logout")` — 로그아웃 처리 URL
- `.logoutSuccessUrl("/login")` — 로그아웃 성공 후 이동할 페이지
- `.deleteCookies("JSESSIONID", "remember-me")` — 로그아웃 후 쿠키 삭제
- `.addLogoutHandler(logoutHandler())` — 로그아웃 핸들러
- `.logoutSuccessHandler(logoutSuccessHandler())` — 로그아웃 성공 후 핸들러

> **Spring Security 는 원칙적으로 로그아웃을 POST 방식으로 구현합니다.**

#### LogoutFilter 동작 흐름

1. `POST` 방식 요청을 `LogoutFilter` 가 받습니다.
2. 현재 요청 정보가 매칭되는지 확인하고, 매칭되지 않으면 다음 필터가 실행됩니다.
3. 요청 정보가 매칭되면 `SecurityContext` 로부터 현재 인증된 인증 객체를 꺼내옵니다.
4. 꺼내온 객체를 `SecurityContextLogoutHandler` 에게 전달합니다.
5. `SecurityContextLogoutHandler` 가 세션 무효화, 쿠키 삭제, `SecurityContextHolder.clearContext()` 로 `SecurityContext` 삭제, 인증 객체 `null` 처리를 수행합니다.
6. 로그아웃 처리가 성공적으로 완료되면 `LogoutFilter` 는 `SimpleUrlLogoutSuccessHandler` 를 호출해 로그인 페이지로 이동합니다.

### Remember Me 인증

- 세션이 만료되고 웹 브라우저가 종료된 후에도 어플리케이션이 사용자를 기억하는 기능입니다.
- `Remember-Me` 쿠키에 대한 HTTP 요청을 확인한 후 토큰 기반 인증을 사용해 유효성을 검사하고, 토큰이 검증되면 사용자가 로그인됩니다.
- 사용자 라이프 사이클
    - 인증 성공 — `Remember-Me` 쿠키 설정
    - 인증 실패 — 쿠키가 존재하면 쿠키 무효화
    - 로그아웃 — 쿠키가 존재하면 쿠키 무효화

#### Remember Me API

- `http.rememberMe()` — rememberMe 기능이 작동합니다.
- `.rememberMeParameter("remember")` — rememberMe 를 활성화할 때 사용할 파라미터명
- `.tokenValiditySeconds(3600)` — 토큰 유효 기간 (기본값 14일)
- `.alwaysRemember(true)` — rememberMe 기능이 활성화되지 않아도 항상 실행
- `.userDetailsService(userDetailsService)` — rememberMe 를 인증할 때 사용자 계정을 조회하는 설정

#### RememberMeAuthenticationFilter 동작 흐름

`RememberMeAuthenticationFilter` 가 동작하는 첫 번째 조건은 `Authentication` 객체의 값이 **`null`** 인 경우입니다. 이미 `Authentication` 이 값을 가지고 있다면 인증되어 있다는 뜻이므로 굳이 `RememberMeAuthenticationFilter` 가 동작할 이유가 없습니다.

- `RememberMeAuthenticationFilter` 는 사용자의 세션이 만료되었거나 브라우저 종료로 세션이 끊겨 인증 객체를 `SecurityContext` 안에서 찾지 못하는 경우, 사용자의 인증을 유지하기 위해 동작하여 인증을 시도합니다.
- 두 번째 조건은 사용자가 로그인 시 Remember Me 기능을 켠 채로 로그인하여 `Remember-Me` 토큰이 발급된 상태여야 한다는 점입니다.

1. 조건이 충족되어 `RememberMeAuthenticationFilter` 가 동작하면 `RememberMeServices` 가 동작합니다.
2. `RememberMeServices` 는 인터페이스로 구현체가 두 가지 있습니다.
    - `TokenBasedRememberMeServices` — 사용자의 요청 토큰과 메모리상 토큰을 비교하는 구현체
    - `PersistentTokenBasedRememberMeServices` — DB에 토큰 내용을 저장해서 사용자 값과 비교하는 구현체
3. `RememberMeServices` 가 토큰을 추출해 사용자가 가지고 있는 토큰이 `Remember-Me` 이름의 토큰인지 확인합니다. 해당 토큰이 없다면 다음 필터로 넘어갑니다.
4. 토큰을 가지고 있다면 `Decode Token` 에서 해당 토큰이 규칙을 지키고 있는지 확인합니다 (정상 유무 판단).
5. 정상적인 토큰이라면 사용자의 토큰과 가지고 있는 토큰이 일치하는지 확인합니다.
6. 토큰이 일치하면, 토큰에 있는 User 정보가 DB에 존재하는지 확인합니다.
7. 존재하면 새 `Authentication` 을 생성해 `AuthenticationManager` 에게 전달해서 인증을 처리합니다.

### AnonymousAuthenticationFilter

- 사용자가 인증을 받게 되면 세션에 User 객체를 저장한 후, 사용자가 자원에 접근하려고 할 때 세션에서 해당 User가 `null` 인지 여부를 판단해 `null` 이면 자원에 접근하지 못하게 합니다.
- `AnonymousAuthenticationFilter` 는 인증을 받지 않은 사용자를 `null` 로 처리하는 것이 아닌 **익명 사용자**로 처리합니다.

1. 사용자의 요청이 들어왔을 때 `AnonymousAuthenticationFilter` 는 사용자의 `Authentication` 이 존재하는지 확인합니다 (`SecurityContext` 에서 확인).
2. 인증 객체가 존재한다면 다음 필터로 넘어갑니다.
3. 인증 객체가 존재하지 않는다면 `null` 이 아닌 `AnonymousAuthenticationToken` 을 생성합니다.
4. 그 후 `SecurityContextHolder` 안의 `SecurityContext` 에 해당 토큰을 저장합니다.
5. **해당 인증 객체는 세션에 저장하지 않습니다.**

### 동시 세션 제어 / 세션 고정 보호 / 세션 정책

#### 동시 세션 제어

동일한 계정으로 인증받을 때 생성되는 세션의 허용 개수가 초과되었을 경우, 어떻게 세션을 초과하지 않고 유지하는지에 대한 제어입니다. 스프링 시큐리티는 두 가지 방법을 제공합니다.

##### 이전 사용자 세션을 만료시키는 방법

- 최대 세션 허용 개수를 초과하는 경우, 이전 사용자 세션을 만료시키는 방법입니다.
- 이 방법으로 최대 세션의 개수를 유지합니다.

##### 현재 사용자 인증을 실패시키는 방법

- 최대 세션 허용 개수만큼 세션이 생성되어 있는 상태에서 로그인을 시도한다면, 인증 예외를 발생시켜 로그인을 차단합니다.

##### 동시 세션 제어 API

- `http.sessionManagement()` — 세션 관리 기능이 작동합니다.
- `.maximumSessions(1)` — 최대 허용 가능 세션 수. `-1` 을 설정하면 무제한 로그인 세션 허용
- `.maxSessionsPreventsLogin(true)` — `true` 로 설정하면 동시 로그인을 차단합니다 (현재 사용자 인증 실패). `false` 라면 기존 세션을 만료시킵니다.
- `.invalidSessionUrl("/invalid")` — 세션이 유효하지 않을 때 이동할 페이지
- `.expiredUrl("/expired")` — 세션이 만료된 경우 이동할 페이지

> `.invalidSessionUrl("/invalid")` 와 `.expiredUrl("/expired")` 를 동시에 설정하면 `invalidSessionUrl` 설정이 우선되어 해당 URL로 이동합니다.

#### 세션 고정 보호

- 공격자가 자신의 세션 아이디를 사용자에게 심어, 사용자가 로그인하면 자신도 인증받도록 유도해 사용자의 정보를 보는 공격을 **세션 고정 공격**이라고 합니다.
- Spring Security 는 해당 공격을 방지하기 위한 보호 기능을 제공합니다.
    - 인증에 성공할 때마다 새 세션을 생성하고 세션 아이디를 발급해, 공격자가 자신의 세션 정보를 활용할 수 없도록 합니다.

##### 세션 고정 보호 API

- `http.sessionManagement()`
- `.sessionFixation().changeSessionId()` — 기본값. 사용자가 인증을 시도하면 세션은 그대로 유지한 채 세션 아이디만 변경합니다.
    - `migrateSession()` — 세션과 세션 아이디 모두 새로 생성합니다. **`changeSessionId` 와 `migrateSession` 은 이전 세션에서 설정한 옵션을 그대로 사용할 수 있습니다.**
    - `newSession()` — 세션과 세션 아이디 모두 새로 생성하지만 이전 세션의 옵션을 사용할 수 없습니다.
    - `none()` — 세션과 세션 아이디 모두 그대로 두는 설정이므로 세션 고정 공격에 노출될 위험이 있습니다.

#### 세션 정책 API

- `.sessionCreationPolicy(...)` — 네 가지 정책 설정이 가능합니다.
    - `SessionCreationPolicy.Always` — Spring Security 가 항상 세션 생성
    - `SessionCreationPolicy.If_Required` — Spring Security 가 필요시 생성 (**기본값**)
    - `SessionCreationPolicy.Never` — Spring Security 가 생성하지 않지만 이미 존재하면 사용
    - `SessionCreationPolicy.Stateless` — Spring Security 가 생성하지 않고 존재해도 사용하지 않음. **세션 자체를 사용하지 않으므로 JWT 토큰 방식을 사용할 때 적용합니다.**

### ConcurrentSessionFilter

- 매 요청마다 현재 사용자의 세션 만료 여부를 체크합니다.
- 세션이 만료되었을 경우 즉시 만료 처리합니다.
- `session.isExpired() == true`
    - 로그아웃 처리
    - 즉시 오류 페이지 응답

### SessionManagementFilter 와 ConcurrentSessionFilter 가 동시 적용된 경우

- `SessionManagementFilter` 에서 확인했을 때 이미 세션 최대 허용 개수가 가득 차 있다면 세션을 만료시키고, 이후 `ConcurrentSessionFilter` 에서 만료 상태를 확인하여 로그아웃 처리와 오류 페이지 응답을 수행합니다.

전체 흐름은 다음과 같습니다.

1. `user1` 이 로그인을 시도하면 `ConcurrentSessionControlAuthenticationStrategy` 에서 현재 사용자의 세션 개수를 확인합니다.
2. 위 예제에서는 아직 세션이 생성된 적이 없으므로, 세션 고정 보호 처리 후 세션 정보를 등록하고 인증이 성공됩니다.
3. 그 후 `user2` 가 인증을 시도하면 똑같이 `ConcurrentSessionControlAuthenticationStrategy` 에서 세션 개수를 확인하고, 이미 최대 허용 개수인 1개가 생성 중이므로 두 전략 중 선택한 전략대로 움직입니다.
    - 인증 실패 전략일 경우 바로 인증을 실패하고 종료합니다.
    - 세션 만료 전략인 경우 `user2` 의 인증을 똑같이 세션 고정 보호 처리한 뒤 세션 정보에 등록하고, `user1` 의 세션을 만료시킵니다.
4. 이후 `user1` 이 서버에 자원을 요청하면 `ConcurrentSessionFilter` 가 만료된 것을 확인하고, 바로 로그아웃 처리하며 오류 페이지를 응답합니다.

## 인가 API

### 권한 설정

Spring Security 에서 권한 설정은 두 가지 방식으로 할 수 있습니다.

#### 선언적 방식

- **URL**
    - `http.antMatchers("/users/**").hasRole("USER")`
- **Method**

```java
@PreAuthorize("hasRole('USER')")
public void user() {
    System.out.println("user");
}
```

#### 동적 방식 — DB 연동 프로그래밍

- **URL**
- **Method**

### 권한 설정

> **주의 사항**
> 설정 시에 구체적인 경로가 먼저 오고, 그것보다 큰 범위의 경로가 뒤에 오도록 설정해야 합니다.

```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http
       .antMatcher("/shop/**")  // 인가를 하려는 특정 경로. 설정하지 않으면 모든 경로가 해당됩니다.
       .authorizeRequests()
           .antMatchers("/shop/login", "/shop/users/**").permitAll() // 해당 경로의 요청을 허용합니다.
           .antMatchers("/shop/mypage").hasRole("USER") // 이 경로는 USER 권한이 필요합니다.
           .antMatchers("/shop/admin/pay").access("hasRole('ADMIN')")
           .antMatchers("/shop/admin/**").access("hasRole('ADMIN') or hasRole('SYS')")
           .anyRequest().authenticated();
}
```

## 인증/인가 API

### ExceptionTranslationFilter

#### AuthenticationException

인증 예외 처리.

1. `AuthenticationEntryPoint` 호출
    - 로그인 페이지 이동, 401 오류 코드 전달 등
2. 인증 예외가 발생하기 전의 요청 정보를 저장
    - `RequestCache` — 사용자의 이전 요청 정보를 세션에 저장하고 꺼내오는 캐시 메커니즘
    - `SavedRequest` — 사용자가 요청했던 request 파라미터 값들과 그 당시의 헤더 값들 등이 저장됨

#### AccessDeniedException

인가 예외 처리.

- `AccessDeniedHandler` 에서 예외 처리

#### ExceptionTranslationFilter API

- `http.exceptionHandling()` — 예외 처리 기능이 동작합니다.
- `.authenticationEntryPoint(authenticationEntryPoint())` — 인증 실패 시 처리
- `.accessDeniedHandler(accessDeniedHandler())` — 인가 실패 시 처리

## 인증 프로세스

### CSRF, CsrfFilter

#### CsrfFilter

- 모든 요청에 랜덤하게 생성된 토큰을 HTTP 파라미터로 요구합니다.
- 요청 시 전달되는 토큰 값과 서버에 저장된 실제 값을 비교한 후, 일치하지 않으면 요청은 실패합니다.

##### Client

- `<input type="hidden" name="${_csrf.parameterName}" value="${_csrf.token}">`
- HTTP 메서드 — `PATCH`, `POST`, `PUT`, `DELETE`

##### Spring Security

- `http.csrf()` — 기본 활성화되어 있습니다.
- `http.csrf().disable()` — 비활성화
