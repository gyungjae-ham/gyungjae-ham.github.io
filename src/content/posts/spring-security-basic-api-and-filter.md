---
author: "luca"
pubDatetime: 2023-08-03T17:13:14+09:00
modDatetime: 2026-10-13T15:36:23+09:00
title: "Spring Security 요청별 인증과 권한 설정"
slug: "spring-security-basic-api-and-filter"
featured: false
draft: false
tags:
  ["학습노트", "spring-security", "filter", "authentication", "web-security"]
description: "공개 페이지는 열리는데 같은 경로의 POST는 왜 거절될까요. 인증, 권한, 세션, CSRF가 각각 검사하는 내용을 요청 예제로 구분합니다."
---

공개 페이지를 `permitAll`로 설정했는데 같은 경로의 POST 요청이 403으로 거절될 수 있습니다. “누구나 접근할 수 있다”는 설정이 있는데 왜 막힐까요. 접근 권한 검사와 CSRF 검사는 서로 다른 일을 하기 때문입니다.

Spring Security를 이해하려면 로그인 성공 여부 하나보다 요청이 어떤 검사를 통과하는지 보는 편이 좋습니다. 아래는 **Spring Security 5.7**을 학습한 기록으로, 6.x에 그대로 붙여 넣을 설정 코드는 아닙니다. 필터 내부의 연결은 [Spring Security의 인증 처리 구조](/posts/spring-security-architecture/)에서 따로 다룹니다.

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

## 로그인 다음 요청에도 인증을 유지하려면

폼 로그인 필터는 AuthenticationManager에 검증을 요청하고 성공한 인증 결과를 컨텍스트에 반영합니다. 이후 요청에서도 유지할지는 세션·SecurityContextRepository 정책에 달려 있습니다.

`SessionCreationPolicy`의 실제 enum 이름은 다음과 같습니다.

- `ALWAYS`: Spring Security가 항상 세션을 만듭니다.
- `IF_REQUIRED`: 필요할 때 만듭니다.
- `NEVER`: 직접 만들지 않지만 기존 세션은 사용할 수 있습니다.
- `STATELESS`: 인증 컨텍스트를 위해 세션을 만들거나 사용하지 않습니다.

예를 들어 세션 기반 로그인에서는 다음 요청에 세션 쿠키가 오면 저장된 인증 정보를 이어서 사용합니다. 반면 `STATELESS`를 선택한 인증 구성은 각 요청에서 인증을 확인할 수 있어야 합니다. 이 설정이 애플리케이션의 다른 코드까지 세션을 만들지 못하게 막는 것은 아닙니다.

로그인 시 세션 ID를 변경하는 세션 고정 보호와, 같은 계정의 동시 로그인 수를 제한하는 기능은 목적이 다릅니다. 동시 세션 제한에서는 신규 로그인을 거부할지 기존 세션을 만료시킬지도 선택해야 합니다.

## Remember Me의 두 방식

`TokenBasedRememberMeServices`는 사용자명·만료 시각 등과 서버의 키를 이용한 서명을 검증합니다. 서버 메모리에 저장한 토큰 하나와 비교하는 방식이 아닙니다. `PersistentTokenBasedRememberMeServices`는 저장소에 유지하는 토큰 기록을 사용합니다. [5.7 Remember Me 문서](https://github.com/spring-projects/spring-security/blob/5.7.13/docs/modules/ROOT/pages/servlet/authentication/rememberme.adoc)

쿠키가 있다는 사실만으로 인증되는 것은 아닙니다. 유효 기간과 검증, 사용자 조회 등의 조건을 통과해야 합니다. 인증 정보가 없는 경우에는 AnonymousAuthenticationFilter가 익명 토큰을 둘 수 있지만, 익명 토큰의 존재를 로그인 완료로 해석하지 않습니다.

## CSRF는 모든 요청의 파라미터 검사가 아니다

기본 CSRF 보호는 주로 POST·PUT·PATCH·DELETE처럼 상태를 바꾸는 메서드에 적용됩니다. 토큰은 파라미터뿐 아니라 정해진 헤더로 보낼 수도 있습니다. GET 등 안전한 메서드는 상태를 바꾸지 않게 설계해야 합니다.

쿠키처럼 브라우저가 자동 전송하는 자격 증명을 쓰는지에 따라 CSRF 위험을 판단합니다. `permitAll`은 인가 규칙이며 CSRF 검사를 자동으로 끄지 않습니다. 로그아웃도 CSRF가 활성화된 기본 구성에서는 POST와 토큰이 필요합니다.

처음의 공개 POST 요청으로 돌아가면, `permitAll`을 더 추가해도 CSRF 검사가 사라지지는 않습니다. 상태를 바꾸는 요청이라면 사용하는 인증 방식에 맞춰 토큰 전달을 확인해야 합니다. 설정을 검증할 때도 공개 GET, 미인증 요청, 권한이 부족한 요청, CSRF 토큰 없는 POST를 나눠 보내 보면 어느 검사에서 거절됐는지 확인하기 쉽습니다.
