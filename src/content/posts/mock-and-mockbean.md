---
author: "luca"
pubDatetime: 2023-05-18T13:15:07+09:00
modDatetime: 2026-10-13T15:51:36+09:00
title: "@Mock과 @MockBean이 적용되는 위치"
slug: "mock-and-mockbean"
featured: false
draft: false
tags: ["학습노트", "testing", "mock", "mockbean", "mockito", "spring"]
description: "Mock을 만들었는데 Spring 서비스에는 실제 Repository가 들어갈 수 있습니다. 직접 만든 객체와 컨텍스트가 만든 객체를 구분하면 이유를 알 수 있습니다."
---

테스트 필드에 `@Mock` Repository를 선언했는데 `@Autowired`로 받은 Service는 실제 DB를 호출할 수 있습니다. Mock 객체를 만드는 것과 Spring이 만든 Service에 그 객체를 넣는 것은 별개이기 때문입니다.

`@Mock`과 `@MockBean`은 모두 Mockito mock을 사용하지만 적용되는 위치가 다릅니다. 테스트 대상을 누가 생성하는지부터 보면 구분하기 쉽습니다.

| 애너테이션              | 하는 일                                      | Spring 컨텍스트 |
| ----------------------- | -------------------------------------------- | --------------- |
| Mockito `@Mock`         | 테스트 필드에 mock 생성                      | 등록하지 않음   |
| Spring Boot `@MockBean` | 컨텍스트에 mock 빈을 추가하거나 기존 빈 대체 | 필요            |

`@Mock`은 JUnit 5의 `MockitoExtension`이나 `MockitoAnnotations.openMocks` 등으로 초기화합니다. 예를 들어 생성자로 Repository를 받는 Service는 mock을 전달해 직접 생성할 수 있습니다. 이 테스트에는 Spring 부팅이 필요하지 않습니다.

예를 들어 직접 만든 `new UserService(mockRepository)`는 전달한 대역을 사용합니다. 하지만 Spring 컨텍스트가 이미 만든 UserService는 테스트 필드에 Mock을 만들었다는 이유만으로 의존성이 바뀌지 않습니다. 컨텍스트의 빈을 바꿔야 하는 경우에 `@MockBean`을 사용했습니다.

`@MockBean`은 `@WebMvcTest`만의 기능이 아닙니다. Spring 테스트 컨텍스트에서 의존 빈을 교체할 때 사용합니다. `@WebMvcTest`는 웹 계층을 중심으로 구성하는 테스트이며, Controller 한 객체만 만드는 것은 아닙니다. MVC 변환기·검증·필터 등 웹 동작에 필요한 구성이 포함됩니다.

## 사용 중인 Spring 버전도 확인한다

이 글의 원래 예시는 Spring Boot 3.0 시기의 `@MockBean`을 사용합니다. **Spring Boot 3.4부터 `@MockBean`은 deprecated**이며 Spring Framework의 `@MockitoBean`으로 이전하는 방향입니다. 이름만 바꾸기 전에 해당 버전의 빈 선택과 교체 조건을 확인합니다. [Spring Boot MockBean API](https://docs.spring.io/spring-boot/3.4/api/java/org/springframework/boot/test/mock/mockito/MockBean.html)

처음의 실제 DB 호출 문제로 돌아가면 Mock이 잘 생성됐는지뿐 아니라 Service가 어떤 Repository를 받았는지도 봐야 합니다. 계산과 분기만 확인할 때는 직접 생성한 객체로 충분할 수 있고, 요청 매핑과 JSON·보안 필터까지 확인하려면 웹 테스트 컨텍스트가 필요합니다. 먼저 확인할 동작을 정한 뒤 그 객체를 만드는 방식에 맞춰 대역을 넣으면 됩니다.
