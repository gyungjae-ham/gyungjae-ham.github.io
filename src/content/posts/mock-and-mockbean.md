---
author: "luca"
pubDatetime: 2023-05-18T13:15:07+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "@Mock, @MockBean"
slug: "mock-and-mockbean"
featured: false
draft: false
tags: ["학습노트", "testing", "mock", "mockbean", "mockito", "spring"]
description: "@Mock 과 @MockBean 의 차이를 Spring ApplicationContext 와 @WebMvcTest 맥락에서 짧게 정리합니다."
---

`@Mock`과 `@MockBean`은 모두 Mockito mock을 사용하지만 객체가 들어가는 곳이 다릅니다. 테스트 대상 객체를 직접 만들 것인지, Spring이 만든 객체의 의존성을 바꿀 것인지부터 구분하면 선택이 쉬워집니다.

| 애너테이션              | 하는 일                                      | Spring 컨텍스트 |
| ----------------------- | -------------------------------------------- | --------------- |
| Mockito `@Mock`         | 테스트 필드에 mock 생성                      | 등록하지 않음   |
| Spring Boot `@MockBean` | 컨텍스트에 mock 빈을 추가하거나 기존 빈 대체 | 필요            |

`@Mock`은 JUnit 5의 `MockitoExtension`이나 `MockitoAnnotations.openMocks` 등으로 초기화합니다. 예를 들어 생성자로 Repository를 받는 Service는 mock을 전달해 직접 생성할 수 있습니다. 이 테스트에는 Spring 부팅이 필요하지 않습니다.

`@MockBean`은 `@WebMvcTest`만의 기능이 아닙니다. Spring 테스트 컨텍스트에서 의존 빈을 교체할 때 사용합니다. `@WebMvcTest`는 웹 계층을 중심으로 구성하는 테스트이며, Controller 한 객체만 만드는 것은 아닙니다. MVC 변환기·검증·필터 등 웹 동작에 필요한 구성이 포함됩니다.

## 사용 중인 Spring 버전도 확인한다

이 글의 원래 예시는 Spring Boot 3.0 시기의 `@MockBean`을 사용합니다. **Spring Boot 3.4부터 `@MockBean`은 deprecated**이며 Spring Framework의 `@MockitoBean`으로 이전하는 방향입니다. 이름만 바꾸기 전에 해당 버전의 빈 선택과 교체 조건을 확인합니다. [Spring Boot MockBean API](https://docs.spring.io/spring-boot/3.4/api/java/org/springframework/boot/test/mock/mockito/MockBean.html)

Service의 계산·분기만 확인할 때는 객체를 직접 만들고, 요청 매핑과 JSON·인증 필터까지 확인할 때는 웹 테스트 컨텍스트를 사용합니다. mock의 종류보다 이번 테스트가 검증할 경계를 먼저 정하는 편이 덜 헷갈립니다.
