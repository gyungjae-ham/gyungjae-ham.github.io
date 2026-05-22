---
author: "luca"
pubDatetime: 2023-05-18T13:13:03+09:00
title: "Controller 테스트 작성"
slug: "writing-controller-tests"
featured: false
draft: false
tags: ["testing", "controller-test", "mockmvc", "spring"]
description: "@WebMvcTest 와 MockMvc 로 Controller 레이어 테스트를 작성하는 방법, 그리고 테스트 이름 정하기까지 짧게 정리합니다."
---

> Spring MVC 컨트롤러 레이어를 테스트할 때 자주 쓰이는 도구들을 정리하는 글입니다.

## @WebMvcTest

`@WebMvcTest` 는 전체 애플리케이션을 시작하지 않고 **웹 레이어만** 테스트할 때 사용합니다.

## MockMvc

서버를 배포하지 않고도 MVC 동작을 테스트할 수 있는 라이브러리로, 주로 **Controller 레이어 테스트** 에 사용됩니다.

## 테스트 이름 정하기

- 테스트마다 조건을 이름에 포함시킵니다.
- `@DisplayName` 을 활용하여 더욱 명확하게 구분할 수 있습니다.
- 팀 규칙을 정해 일관성 있게 관리하는 것이 좋습니다.

예시:

```
@DisplayName("[view][GET] 게시글 리스트 (게시판) 페이지 - 정상 호출")
```

## Controller View Test 예시

```java
@Disabled("구현 중")
@DisplayName("[view][GET] 게시글 리스트 (게시판) 페이지 - 정상 호출")
@Test
public void givenNothing_whenRequestingArticlesView_thenReturnsArticlesView() throws Exception {
    mvc.perform(get("/articles"))
            .andExpect(status().isOk())
            .andExpect(content().contentType(MediaType.TEXT_HTML))
            .andExpect(model().attributeExists("articles"));
}
```

개발 중인 기능은 `@Disabled` 로 테스트를 비활성화하여 빌드 실패를 방지할 수 있습니다.
