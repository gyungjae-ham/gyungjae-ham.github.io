---
author: "luca"
pubDatetime: 2023-05-18T13:13:03+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Controller 테스트 작성"
slug: "writing-controller-tests"
featured: false
draft: false
tags: ["학습노트", "testing", "controller-test", "mockmvc", "spring"]
description: "MockMvc로 정상 요청과 필수 파라미터 누락을 검사하는 Java 예시입니다. 단독 설정과 @WebMvcTest가 각각 검증하는 범위도 구분합니다."
---

Controller 테스트에서는 경로와 파라미터를 어떻게 읽고, 어떤 상태 코드와 본문을 돌려주는지 확인합니다. 성공 응답 하나만 보는 대신 잘못된 요청도 함께 두면 요청 계약을 더 분명하게 표현할 수 있습니다.

다음은 **Java 17·Spring Framework 6.x·JUnit 5**에서 사용하는 MockMvc 단독 설정 예시입니다. Spring Boot 3 프로젝트에서는 `spring-boot-starter-web`과 `spring-boot-starter-test`로 MVC·Servlet·테스트 의존성을 준비할 수 있습니다. 실제 서버 포트를 열지 않습니다.

```java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class GreetingControllerTest {
    private MockMvc mvc;

    @BeforeEach
    void setUp() {
        mvc = MockMvcBuilders.standaloneSetup(new GreetingController()).build();
    }

    @Test
    void returnsGreetingWhenNameIsPresent() throws Exception {
        mvc.perform(get("/greeting").param("name", "Luca"))
            .andExpect(status().isOk())
            .andExpect(content().string("Hello, Luca"));
    }

    @Test
    void rejectsMissingName() throws Exception {
        mvc.perform(get("/greeting"))
            .andExpect(status().isBadRequest());
    }

    @RestController
    static class GreetingController {
        @GetMapping("/greeting")
        String greet(@RequestParam("name") String name) {
            return "Hello, " + name;
        }
    }
}
```

이 구성은 작은 Controller의 MVC 동작을 확인합니다. 애플리케이션의 실제 SecurityFilterChain이나 Advice를 자동으로 모두 가져오지는 않습니다. 전역 MVC 설정까지 검증하려면 `@WebMvcTest`를 사용하고 필요한 설정과 의존성을 명시합니다. [MockMvc 설정 방식](https://docs.spring.io/spring-framework/reference/testing/mockmvc/hamcrest/setup.html)

`@WebMvcTest`에는 보안 필터도 포함될 수 있으므로 인증·권한·CSRF 조건을 의도에 맞게 준비해야 합니다. 자세한 범위는 [레이어별 테스트 전략](/posts/layered-testing-strategy/)에서 다룹니다.

테스트를 `@Disabled`로 끄면 그 계약은 검사되지 않습니다. 일시 중단이 필요할 때는 이유와 복구 조건을 관리하고, 빌드를 통과시키기 위한 기본 방법으로 사용하지 않습니다.
