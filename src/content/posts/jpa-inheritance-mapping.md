---
author: "luca"
pubDatetime: 2023-05-26T18:17:52+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 상속 매핑: Item 전체 조회가 필요한가부터 묻기"
slug: "jpa-inheritance-mapping"
featured: false
draft: false
tags: ["학습노트", "jpa", "inheritance", "mapped-superclass"]
description: "객체 상속을 DB 슈퍼타입·서브타입 관계로 매핑하는 세 가지 전략과 @MappedSuperclass 의 용도를 정리한 학습 노트입니다."
---

김영한님의 JPA 로드맵을 따라 정리한 학습 노트입니다. 도서와 영화를 모두 `Item`으로 조회하고 싶다면, 객체의 상속 구조를 어떤 테이블 구조로 저장할지 정해야 합니다. JPA의 세 전략은 같은 객체 모델에서도 조회와 저장 비용을 다르게 만듭니다.

아래는 `Item(id, name)`, `Book(author)`, `Movie(director)`라는 설명용 모델입니다.

| 전략            | 테이블 구조                               | Book 한 건을 새로 저장할 때 | Item 전체를 조회할 때          |
| --------------- | ----------------------------------------- | --------------------------- | ------------------------------ |
| SINGLE_TABLE    | item에 공통·하위 필드와 타입 구분 컬럼    | 한 테이블에 INSERT          | 한 테이블에서 읽음             |
| JOINED          | item, book, movie로 나누고 같은 ID로 연결 | item과 book에 각각 INSERT   | 하위 속성을 읽으려면 조인 필요 |
| TABLE_PER_CLASS | book, movie 각각에 공통 필드 포함         | book에 INSERT               | 여러 하위 테이블을 합쳐 조회   |

단일 테이블은 이 예에서 조회 구조가 단순합니다. 대신 도서 행에는 director가, 영화 행에는 author가 필요 없어서 하위 타입 전용 컬럼에 일반적인 NOT NULL 제약을 걸기 어렵습니다. 타입별 조건을 DB 제약으로 표현할 수 있는지는 별도로 검토해야 합니다.

조인 전략은 공통 정보와 하위 정보가 나뉩니다. 위처럼 부모와 자식이 한 단계면 저장할 테이블도 두 개지만, 상속 계층이 더 깊다면 “항상 INSERT 두 번”은 아닙니다. 타입 구분 컬럼의 사용 여부 역시 전략과 구현체 설정에 따라 확인해야 합니다.

구현 클래스별 테이블은 특정 타입만 주로 읽을 때 구조가 단순할 수 있습니다. 반면 `Item` 전체 검색이나 다른 테이블에서 모든 상품을 하나의 외래키로 참조하는 요구가 많다면 불리합니다. 무조건 금지할 전략이라기보다 다형 조회와 참조 무결성 요구를 먼저 따져야 합니다.

## 공통 필드만 재사용한다면

작성일·수정일을 여러 엔티티에 넣되 이들을 하나의 부모 엔티티로 검색할 필요가 없다면 `@MappedSuperclass`를 쓸 수 있습니다.

```java
@MappedSuperclass
abstract class BaseEntity {
    @Id @GeneratedValue
    private Long id;
    private Instant createdAt;
}
```

이 축약 예제의 BaseEntity는 조회 대상 엔티티가 아니며, 자신의 테이블도 없습니다. 상속한 엔티티의 테이블에 필드가 매핑됩니다. 값을 자동으로 채우는 기능은 별도이므로 [Auditing 설정](/posts/jpa-auditing/)이 필요합니다.

전략별 매핑은 [Jakarta Persistence 3.1 명세](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1)를 참고했습니다. 실제 SQL과 성능은 선택한 Hibernate·DB 버전, 조회하는 속성에 맞춰 확인해야 합니다.
