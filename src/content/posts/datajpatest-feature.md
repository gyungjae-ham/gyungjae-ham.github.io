---
author: "luca"
pubDatetime: 2023-05-18T12:01:59+09:00
title: "@DataJpaTest 기능"
slug: "datajpatest-feature"
featured: false
draft: false
tags: ["testing", "data-jpa-test", "jpa", "spring-boot"]
description: "@DataJpaTest 가 어떻게 동작하는지, 그리고 트랜잭션 롤백·saveAndFlush 의 의미를 짧게 정리합니다."
---

> Repository 테스트에서 자주 사용하는 `@DataJpaTest` 의 핵심 동작을 정리하는 글입니다.

## 인메모리 DB 를 이용한 Test

`Repository` 를 이용한 테스트를 진행할 때 인메모리 DB 를 많이 사용합니다. 많은 방법 중 크게 두 가지 정도가 자주 사용된다고 생각합니다.

- `@SpringBootTest` + 인메모리 DB 연결
- `@DataJpaTest`

## 두 방법의 차이

`@DataJpaTest` 의 안을 들여다보면 다음과 같습니다.

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@Inherited
@BootstrapWith(DataJpaTestContextBootstrapper.class)
@ExtendWith(SpringExtension.class)
@OverrideAutoConfiguration(enabled = false)
@TypeExcludeFilters(DataJpaTypeExcludeFilter.class)
@Transactional
@AutoConfigureCache
@AutoConfigureDataJpa
@AutoConfigureTestDatabase
@AutoConfigureTestEntityManager
@ImportAutoConfiguration
```

`meta annotation` 중에서 `@Transactional` 이 들어가 있습니다. 따라서 `@DataJpaTest` 가 붙어있는 클래스 밑의 메서드들은 실행 시 트랜잭션이 동작하기 때문에 **기본적으로 롤백** 된다고 보면 됩니다.

```java
@DisplayName("update 테스트")
@Test
void givenTestData_whenUpdating_thenWorksFine() {
    // Given
    Article article = articleRepository.findById(1L).orElseThrow();
    String updatedHashtag = "#springboot";
    article.setHashtag(updatedHashtag);

    // When
    Article savedArticle = articleRepository.save(article);

    // Then
    assertThat(savedArticle).hasFieldOrPropertyWithValue("hashtag", updatedHashtag);
}
```

`@DataJpaTest` 가 붙어있다면 위와 같은 테스트 코드를 실행시키면 **업데이트 쿼리가 보이지 않습니다.** 만약 쿼리문을 확인하고 싶다면 다음과 같이 작성합니다.

```java
@DisplayName("update 테스트")
@Test
void givenTestData_whenUpdating_thenWorksFine() {
    // Given
    Article article = articleRepository.findById(1L).orElseThrow();
    String updatedHashtag = "#springboot";
    article.setHashtag(updatedHashtag);

    // When
    Article savedArticle = articleRepository.saveAndFlush(article);

    // Then
    assertThat(savedArticle).hasFieldOrPropertyWithValue("hashtag", updatedHashtag);
}
```

`save` 부분을 `saveAndFlush` 로 바꾸면 쿼리문을 확인할 수 있습니다. 다만 업데이트 내용이 DB 에 적용되지는 않고 마찬가지로 롤백됩니다.
