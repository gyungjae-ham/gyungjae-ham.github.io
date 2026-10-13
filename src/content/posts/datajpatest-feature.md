---
author: "luca"
pubDatetime: 2023-05-18T12:01:59+09:00
modDatetime: 2026-10-13T15:36:23+09:00
title: "@DataJpaTest에서 저장 결과까지 확인하기"
slug: "datajpatest-feature"
featured: false
draft: false
tags: ["학습노트", "testing", "data-jpa-test", "jpa", "spring-boot"]
description: "엔티티 값을 바꾸고 같은 객체를 검사하면 DB 저장이 빠진 테스트도 통과할 수 있습니다. flush와 clear를 거쳐 다시 읽어야 하는 이유를 살펴봅니다."
---

게시글의 해시태그를 수정한 뒤 값이 바뀌었는지 확인하는 테스트를 생각해 보겠습니다. `article.setHashtag(...)` 다음에 같은 객체의 값을 읽으면 테스트는 통과합니다. 하지만 이것만으로 DB에도 변경 내용이 저장되는지 확인한 것은 아닙니다.

`@DataJpaTest`는 엔티티와 Repository 등 JPA 계층을 중심으로 테스트 환경을 만듭니다. 기본적으로 각 테스트를 트랜잭션 안에서 실행하고 끝나면 롤백합니다. 보통 임베디드 DB를 사용하므로 운영 DB의 문법까지 확인하려면 사용하는 Spring Boot 버전의 DB 교체 설정도 살펴봐야 합니다.

## 롤백되는 테스트에서도 SQL은 실행된다

`saveAndFlush()`는 변경 SQL을 DB에 보내 현재 트랜잭션에 반영합니다. **DB에 반영되지 않는 것이 아니라, 아직 커밋되지 않은 것**입니다. 테스트가 끝나 기본 롤백이 실행되면 그 변경이 취소됩니다.

반면 managed 엔티티의 필드만 바꾼 뒤 메모리의 값만 검사하면, SQL 실행 없이도 테스트가 통과할 수 있습니다. DB 매핑까지 확인하려면 flush 후 영속성 컨텍스트를 비우고 다시 조회합니다.

## 저장한 값을 다시 읽는 테스트

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

`clear()`가 없다면 `findById()`가 같은 영속성 컨텍스트에 있는 Article을 돌려줄 수 있습니다. 값을 바꾼 바로 그 객체를 또 확인하는 셈입니다. 컨텍스트를 비운 뒤 조회해야 DB에서 읽은 값과 기대값을 비교할 수 있습니다. 테스트 종료 후에는 기본 롤백이 적용됩니다. 다만 다른 스레드나 `REQUIRES_NEW` 트랜잭션에서 커밋한 데이터까지 이 롤백이 모두 지워주지는 않습니다.

flush는 명시적 호출 외에도 커밋이나 필요한 쿼리 실행 전에 발생할 수 있습니다. 자세한 범위는 [영속성 컨텍스트와 flush](/posts/jpa-persistence-context/)에서 다룹니다.
