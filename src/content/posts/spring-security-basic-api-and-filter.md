---
author: "luca"
pubDatetime: 2023-08-03T17:13:14+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Spring Security 기본 API 및 Filter 이해"
slug: "spring-security-basic-api-and-filter"
featured: false
draft: false
tags:
  ["학습노트", "spring-security", "filter", "authentication", "web-security"]
description: "Spring Security 5.7에서 인증·권한·세션·Remember Me·CSRF가 각각 무엇을 결정하는지 요청별로 구분한 학습 노트입니다."
---

Spring Security 설정은 로그인 화면뿐 아니라 요청별 인증·권한·세션·CSRF 정책을 함께 바꿉니다. 이 글은 **Spring Security 5.7**을 학습한 노트이며, 6.x의 설정 코드로 그대로 사용하지 않습니다. 내부 구성요소는 [아키텍처 글](/posts/spring-security-architecture/)에 따로 정리했습니다.

## 어떤 요청을 허용하는지 먼저 정한다

다음은 5.7에서 SecurityFilterChain 빈으로 공개 경로와 나머지 경로를 나누는 설정 부분입니다. 사용자 저장소·PasswordEncoder 등 인증 구성은 별도로 필요합니다.

```java
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    http
        .authorizeRequests(authorize -> authorize
            .antMatchers("/public/**").permitAll()
            .antMatchers("/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .httpBasic(Customizer.withDefaults());
    return http.build();
}
```

이 구성에서는 공개 GET은 인증 없이 접근할 수 있고, 보호된 GET은 인증이 필요합니다. 인증된 일반 사용자가 관리자 경로에 접근하면 권한 부족입니다. HTTP Basic의 미인증 응답과 폼 로그인의 로그인 페이지 리다이렉트는 서로 다르므로, ‘인증 실패는 항상 같은 상태 코드’라고 가정하지 않습니다.

## 인증 결과와 세션

폼 로그인 필터는 AuthenticationManager에 검증을 요청하고 성공한 인증 결과를 컨텍스트에 반영합니다. 이후 요청에서도 유지할지는 세션·SecurityContextRepository 정책에 달려 있습니다.

`SessionCreationPolicy`의 실제 enum 이름은 다음과 같습니다.

- `ALWAYS`: Spring Security가 항상 세션을 만듭니다.
- `IF_REQUIRED`: 필요할 때 만듭니다.
- `NEVER`: 직접 만들지 않지만 기존 세션은 사용할 수 있습니다.
- `STATELESS`: 인증 컨텍스트를 위해 세션을 만들거나 사용하지 않습니다.

`STATELESS`는 애플리케이션의 다른 코드도 절대 세션을 만들지 못하게 하는 설정이 아닙니다. JWT를 쓴다는 이유만으로 모든 보안 정책이 결정되는 것도 아닙니다.

로그인 시 세션 ID를 변경하는 세션 고정 보호와, 같은 계정의 동시 로그인 수를 제한하는 기능은 목적이 다릅니다. 동시 세션 제한에서는 신규 로그인을 거부할지 기존 세션을 만료시킬지도 선택해야 합니다.

## Remember Me의 두 방식

`TokenBasedRememberMeServices`는 사용자명·만료 시각 등과 서버의 키를 이용한 서명을 검증합니다. 서버 메모리에 저장한 토큰 하나와 비교하는 방식이 아닙니다. `PersistentTokenBasedRememberMeServices`는 저장소에 유지하는 토큰 기록을 사용합니다. [5.7 Remember Me 문서](https://github.com/spring-projects/spring-security/blob/5.7.13/docs/modules/ROOT/pages/servlet/authentication/rememberme.adoc)

쿠키가 있다는 사실만으로 인증되는 것은 아닙니다. 유효 기간과 검증, 사용자 조회 등의 조건을 통과해야 합니다. 인증 정보가 없는 경우에는 AnonymousAuthenticationFilter가 익명 토큰을 둘 수 있지만, 익명 토큰의 존재를 로그인 완료로 해석하지 않습니다.

## CSRF는 모든 요청의 파라미터 검사가 아니다

기본 CSRF 보호는 주로 POST·PUT·PATCH·DELETE처럼 상태를 바꾸는 메서드에 적용됩니다. 토큰은 파라미터뿐 아니라 정해진 헤더로 보낼 수도 있습니다. GET 등 안전한 메서드는 상태를 바꾸지 않게 설계해야 합니다.

쿠키처럼 브라우저가 자동 전송하는 자격 증명을 쓰는지에 따라 CSRF 위험을 판단합니다. `permitAll`은 인가 규칙이며 CSRF 검사를 자동으로 끄지 않습니다. 로그아웃도 CSRF가 활성화된 기본 구성에서는 POST와 토큰이 필요합니다.

설정 후에는 공개 요청, 미인증 보호 요청, 권한 부족 요청, 인증됐지만 CSRF가 없는 변경 요청을 나눠 확인합니다. 성공한 로그인 하나만으로 보안 체인 전체가 의도대로 동작한다고 판단하지 않습니다.
