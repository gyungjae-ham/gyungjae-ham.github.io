---
author: "luca"
pubDatetime: 2023-05-18T13:13:03+09:00
modDatetime: 2026-10-13T15:42:49+09:00
title: "MockMvc로 정상 요청과 잘못된 요청 테스트하기"
slug: "writing-controller-tests"
featured: false
draft: false
tags: ["학습노트", "testing", "controller-test", "mockmvc", "spring"]
description: "이름을 받는 간단한 API로 파라미터 바인딩과 400 응답을 확인합니다. 컨트롤러 메서드 직접 호출과 MockMvc 테스트가 다른 점도 살펴봅니다."
---

`greet("Luca")`를 직접 호출하면 인사말을 만드는 로직은 확인할 수 있습니다. 하지만 `/greeting?name=Luca`가 이 메서드로 연결되는지, 필수 파라미터를 빠뜨렸을 때 400으로 응답하는지는 알 수 없습니다. 이 부분을 확인하려면 Spring MVC의 요청 처리도 함께 거쳐야 합니다.

MockMvc로 작은 인사 API의 정상 요청과 잘못된 요청을 각각 테스트해 보겠습니다.

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

첫 테스트는 경로와 name 파라미터가 연결돼 `Hello, Luca`를 반환하는지 봅니다. 두 번째는 name을 생략한 요청이 거절되는지 확인합니다. 메서드를 직접 호출했다면 지나가지 않았을 바인딩 과정까지 확인하는 것입니다.

이 구성은 작은 Controller의 MVC 동작을 확인합니다. 애플리케이션의 실제 SecurityFilterChain이나 Advice를 자동으로 모두 가져오지는 않습니다. 전역 MVC 설정까지 검증하려면 `@WebMvcTest`를 사용하고 필요한 설정과 의존성을 명시합니다. [MockMvc 설정 방식](https://docs.spring.io/spring-framework/reference/testing/mockmvc/hamcrest/setup.html)

`@WebMvcTest`에는 보안 필터도 포함될 수 있으므로 인증·권한·CSRF 조건을 의도에 맞게 준비해야 합니다. 자세한 범위는 [레이어별 테스트 전략](/posts/layered-testing-strategy/)에서 다룹니다.

필터가 포함된 테스트에서 401이나 403이 나왔다면 컨트롤러 코드만 볼 일이 아닐 수 있습니다. 의도한 인증 정보를 준비했는지 먼저 확인해야 합니다. 실패한 테스트를 `@Disabled`로 끄면 이런 연결도 더는 검사하지 못하므로, 일시 중단이 필요할 때는 이유와 복구 조건을 남겨야 합니다.
