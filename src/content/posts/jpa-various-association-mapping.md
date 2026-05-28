---
author: "luca"
pubDatetime: 2023-05-26T11:40:02+09:00
title: "다양한 연관관계 매핑"
slug: "jpa-various-association-mapping"
featured: false
draft: false
tags: ["jpa", "association", "relationship", "orm"]
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

일대다 매핑에서는 외래키를 가지지 않은 테이블의 객체가 연관관계의 주인이 됩니다. `Team` 엔티티에 `members`를 추가할 때 `MEMBER` 테이블의 외래키를 업데이트하는 추가 쿼리가 발생합니다.

## 일대다 양방향

**다대일 양방향 매핑 사용이 권장됩니다.** 외래키를 가진 엔티티에서는 읽기 전용으로 설정합니다.

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
- **단점**: 지연 로딩이 항상 즉시 로딩으로 작동합니다.

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

**실무에서는 지양해야 합니다.** 연결 테이블에 주문 시간, 수량 등 추가 데이터가 필요한 경우가 대부분입니다.

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
