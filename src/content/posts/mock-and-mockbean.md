---
author: "luca"
pubDatetime: 2023-05-18T13:15:07+09:00
title: "@Mock, @MockBean"
slug: "mock-and-mockbean"
featured: false
draft: false
tags: ["testing", "mock", "mockbean", "mockito", "spring"]
description: "@Mock 과 @MockBean 의 차이를 Spring ApplicationContext 와 @WebMvcTest 맥락에서 짧게 정리합니다."
---

> 테스트에서 Mock 객체를 선언할 때 자주 헷갈리는 두 어노테이션을 정리하는 글입니다.

`@Mock` 과 `@MockBean` 은 Mock 객체를 선언할 때 사용되는 어노테이션이며, Spring 의 `ApplicationContext` 에 Mock 객체들을 넣어줍니다.

**핵심 구분:**

> "Spring Boot Container 가 테스트 시에 필요하고, Bean 이 Container 에 존재한다면 `@MockBean` 을 사용하고 아닌 경우에는 `@Mock` 을 사용합니다."

## @Mock

필드에 선언하여 해당 필드가 Mock 객체임을 명확히 표시합니다. **Service 레이어를 테스트할 때 Repository 를 가짜 객체로 만드는 용도** 로 사용될 수 있습니다.

## @MockBean

`@WebMvcTest` 를 이용한 테스트에서 사용합니다. `@WebMvcTest` 는 Controller 를 테스트할 때 주로 이용되며, "Controller 객체까지만 생성되고 Service 객체는 생성하지 않습니다." 단일 클래스의 테스트를 진행하므로 `@MockBean` 을 통해 가짜 객체를 만들어 줍니다.
