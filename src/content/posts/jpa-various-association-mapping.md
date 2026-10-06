---
author: "luca"
pubDatetime: 2023-05-26T11:40:02+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "다양한 연관관계 매핑"
slug: "jpa-various-association-mapping"
featured: false
draft: false
tags: ["학습노트", "jpa", "association", "relationship", "orm"]
description: "다중성·방향·연관관계 주인 세 축으로 일대다·일대일·다대다 매핑을 정리하고, 다대다의 한계와 극복법까지 짚은 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 연관관계 매핑 시 고려 사항

- 다중성
- 단방향, 양방향
- 연관관계의 주인

### 다중성

- 다대일: `@ManyToOne`
- 일대다: `@OneToMany`
- 일대일: `@OneToOne`
- 다대다: `@ManyToMany`

## 일대다 단방향

일대다 단방향에서 `@JoinColumn`으로 자식 테이블의 FK를 관리하면 Team이 관계의 주인이 됩니다. 이 방식에서는 자식 INSERT 외에 FK 갱신 SQL이 추가될 수 있습니다. 기본 조인 테이블 방식과 구분해 실제 매핑을 확인해야 합니다.

## 일대다 양방향

보통은 FK가 있는 `Member.team`을 주인으로 하고 `Team.members`에 `mappedBy`를 두는 다대일 양방향 매핑이 단순합니다. 아래는 그 권장 형태와 달리, 일대다를 주인으로 유지하며 반대편 FK 쓰기를 막은 특수한 구성입니다. 엔티티의 ID와 생성자는 생략했습니다.

```java
@Entity
public class Team {
    @OneToMany
    @JoinColumn(name = "TEAM_ID")
    List<Member> members = new ArrayList<>();
}

@Entity
public class Member {
    @ManyToOne
    @JoinColumn(name = "TEAM_ID", insertable = false, updatable = false)
    private Team team;
}
```

## 일대일 매핑

외래키가 있는 곳이 연관관계의 주인입니다. 반대편은 `mappedBy`를 설정합니다.

### 주 테이블에 외래키

- **장점**: 주 테이블만 조회해도 데이터 존재 여부를 확인할 수 있습니다.
- **단점**: `null` 값이 외래키에 들어갈 수 있습니다.

### 대상 테이블에 외래키

- **장점**: 일대일에서 일대다로 관계가 변경될 때 테이블 구조를 유지할 수 있습니다.
- **주의**: FK가 없는 반대편에서는 연관 객체의 존재를 확인할 추가 조회가 필요할 수 있습니다. 지연 로딩 가능 여부는 소유 방향, optional 조건, Hibernate 버전과 bytecode enhancement 설정에 따라 달라집니다. `LAZY` 선언만 보고 SQL을 단정하지 않습니다.

## 다대다

관계형 데이터베이스는 2개의 테이블로 다대다를 표현할 수 없어 연결 테이블이 필요합니다.

```java
@Entity
public class Member {
    @ManyToMany
    @JoinTable(name = "MEMBER_PRODUCT")
    private List<Product> products = new ArrayList<>();
}
```

연결 자체만 필요한 관계에는 사용할 수 있습니다. 다만 주문 시간·수량처럼 연결에 속한 데이터가 생기거나 연결을 개별적으로 관리해야 하면 별도 엔티티가 더 적합합니다. 아래 코드도 ID와 생성자 등을 생략한 관계 매핑 예입니다.

### 다대다 한계 극복

연결 테이블을 엔티티로 승격시킵니다. `@ManyToMany`를 `@OneToMany`와 `@ManyToOne`으로 변환합니다.

```java
@Entity
public class MemberProduct {
    @ManyToOne
    @JoinColumn(name = "MEMBER_ID")
    private Member member;

    @ManyToOne
    @JoinColumn(name = "PRODUCT_ID")
    private Product product;
}

@Entity
public class Member {
    @OneToMany(mappedBy = "member")
    private List<MemberProduct> memberProducts = new ArrayList<>();
}

@Entity
public class Product {
    @OneToMany(mappedBy = "product")
    private List<MemberProduct> memberProducts = new ArrayList<>();
}
```
