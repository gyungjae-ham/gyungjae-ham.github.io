---
author: "luca"
pubDatetime: 2023-05-18T12:01:59+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "@DataJpaTest 기능"
slug: "datajpatest-feature"
featured: false
draft: false
tags: ["학습노트", "testing", "data-jpa-test", "jpa", "spring-boot"]
description: "@DataJpaTest 가 어떻게 동작하는지, 그리고 트랜잭션 롤백·saveAndFlush 의 의미를 짧게 정리합니다."
---

`@DataJpaTest`는 엔티티·Repository 등 JPA 계층을 중심으로 Spring 테스트 컨텍스트를 구성합니다. 보통 임베디드 DB를 사용하며, 기본적으로 테스트를 트랜잭션 안에서 실행한 뒤 롤백합니다. 실제 DB를 쓰려면 해당 Spring Boot 버전의 테스트 DB 교체 설정도 확인해야 합니다.

## flush와 commit을 구분한다

`saveAndFlush()`는 변경 SQL을 DB에 보내 현재 트랜잭션에 반영합니다. **DB에 반영되지 않는 것이 아니라, 아직 커밋되지 않은 것**입니다. 테스트가 끝나 기본 롤백이 실행되면 그 변경이 취소됩니다.

반면 managed 엔티티의 필드만 바꾼 뒤 메모리의 값만 검사하면, SQL 실행 없이도 테스트가 통과할 수 있습니다. DB 매핑까지 확인하려면 flush 후 영속성 컨텍스트를 비우고 다시 조회합니다.

아래는 `Article`에 `hashtag` 필드가 있다고 가정한 테스트 메서드 예시입니다. 테스트 클래스는 `@DataJpaTest`를 사용하고 `EntityManager`와 Repository를 주입받습니다. `fixture`는 필수 필드를 채운 새 엔티티를 만드는 프로젝트의 테스트 도우미입니다.

```java
@Test
void hashtagChangeIsStored() {
    Article article = articleRepository.saveAndFlush(fixture());
    Long id = article.getId();

    article.setHashtag("#springboot");
    entityManager.flush();
    entityManager.clear();

    Article reloaded = articleRepository.findById(id).orElseThrow();
    assertThat(reloaded.getHashtag()).isEqualTo("#springboot");
}
```

이 순서에서 재조회는 1차 캐시에 남은 객체의 값만 확인하지 않게 합니다. 테스트 종료 후에는 기본 롤백이 적용됩니다. 다만 다른 스레드나 `REQUIRES_NEW` 트랜잭션에서 커밋한 데이터까지 이 롤백이 모두 지워주지는 않습니다.

flush는 명시적 호출 외에도 커밋이나 필요한 쿼리 실행 전에 발생할 수 있습니다. 자세한 범위는 [영속성 컨텍스트와 flush](/posts/jpa-persistence-context/)에서 다룹니다.
