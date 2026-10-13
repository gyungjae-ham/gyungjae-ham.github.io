---
author: "luca"
pubDatetime: 2023-05-26T11:40:02+09:00
modDatetime: 2026-10-13T15:50:14+09:00
title: "JPA 일대다·일대일·다대다 매핑 선택하기"
slug: "jpa-various-association-mapping"
featured: false
draft: false
tags: ["학습노트", "jpa", "association", "relationship", "orm"]
description: "회원과 팀, 회원과 사물함, 회원과 상품은 관계를 저장하는 방식이 다릅니다. 외래키의 위치와 관계 자체에 필요한 데이터를 기준으로 매핑을 비교합니다."
---

JPA 연관관계를 설정할 때는 객체 필드에 어떤 어노테이션을 붙일지만 보면 부족합니다. 한쪽에 몇 개가 연결되는지, 코드에서 어느 방향으로 이동할지, DB의 외래키는 누가 변경할지 함께 정해야 합니다.

김영한님의 JPA 로드맵을 학습하며 일대다·일대일·다대다를 비교했습니다. 기본적인 연관관계의 주인은 [회원과 팀의 양방향 참조](/posts/jpa-association-mapping/)에 정리했고, 여기서는 요구가 달라지면 어떤 선택이 추가되는지 살펴봅니다.

## 팀이 회원 목록만 가지고 있는 일대다

팀에서 회원 목록을 읽고 싶지만 회원은 팀을 참조하지 않는 구조를 생각해 보겠습니다. Team의 `@OneToMany`에 `@JoinColumn`을 붙여 회원 테이블의 외래키를 관리할 수 있습니다. 이 경우 객체에서 관계를 바꾸는 쪽은 Team이지만, 실제 외래키는 Member 테이블에 있습니다.

이 차이 때문에 자식 INSERT 외에 외래키를 갱신하는 SQL이 추가될 수 있습니다. `@JoinColumn`을 사용한 방식과 기본 조인 테이블 방식도 구분해서 봐야 합니다. 어노테이션 이름이 일대다라는 이유만으로 같은 SQL이 나오는 것은 아닙니다.

회원에서 팀으로도 이동해야 한다면, 보통은 외래키가 있는 `Member.team`을 주인으로 두고 `Team.members`에 `mappedBy`를 쓰는 구성이 단순합니다. 일대다 쪽을 주인으로 유지하며 반대쪽을 읽기 전용으로 만드는 방식도 가능하지만 두 매핑이 같은 외래키를 쓰지 않도록 해야 합니다.

```java
// 관계 부분만 남긴 예시: 각 엔티티의 ID와 생성자는 생략
@Entity
public class Team {
    @OneToMany
    @JoinColumn(name = "TEAM_ID")
    private List<Member> members = new ArrayList<>();
}

@Entity
public class Member {
    @ManyToOne
    @JoinColumn(name = "TEAM_ID", insertable = false, updatable = false)
    private Team team;
}
```

이 특수한 구성에서는 `Member.team`을 바꿔도 해당 필드가 외래키를 저장하지 않습니다. 조회 편의를 추가한 것과 관계를 변경할 수 있는 곳을 늘린 것은 다릅니다.

## 회원과 사물함이 일대일이라면

회원 한 명이 사물함 하나를 쓰는 관계에서는 어느 테이블에 외래키를 둘지 선택할 수 있습니다. 회원에 사물함 ID가 있으면 회원을 읽을 때 연결 여부를 알기 쉽습니다. 외래키가 사물함에 있으면 회원 쪽에서 사물함이 있는지 확인하기 위한 조회가 필요할 수 있습니다.

일대일 관계는 실제 DB의 unique 제약도 맞아야 합니다. 나중에 한 회원이 여러 사물함을 갖게 된다면 제약과 매핑을 함께 바꿔야 하므로, 어느 쪽에 외래키가 있는지만으로 변경이 모두 끝나지는 않습니다.

FK가 없는 반대편의 지연 로딩은 소유 방향, optional 조건, Hibernate 버전과 bytecode enhancement 설정 등에 영향을 받습니다. `LAZY`만 보고 추가 조회가 없다고 단정하기보다 생성 SQL을 확인해야 합니다.

## 회원과 상품의 연결에 수량이 생기면

회원은 여러 상품을 고르고 상품도 여러 회원에게 선택될 수 있습니다. 일반적인 관계형 매핑에서는 연결 테이블로 이 다대다를 표현합니다. 연결 사실만 필요하다면 `@ManyToMany`와 `@JoinTable`을 사용할 수 있습니다.

그런데 “언제 몇 개를 골랐는가”를 저장해야 한다면 수량과 시각은 회원이나 상품 자체가 아니라 둘의 연결에 속합니다. 이때 연결 테이블을 별도 엔티티로 다루면 필요한 필드와 생명주기를 표현하기 쉽습니다.

```java
@Entity
public class MemberProduct {
    @Id @GeneratedValue
    private Long id;

    @ManyToOne
    @JoinColumn(name = "MEMBER_ID")
    private Member member;

    @ManyToOne
    @JoinColumn(name = "PRODUCT_ID")
    private Product product;

    private int quantity;
    // 생성자와 접근자는 생략
}
```

회원과 상품은 각각 MemberProduct와 일대다 관계가 됩니다. 상품 연결을 한 건씩 수정하거나 추적해야 할 때도 별도 ID가 도움이 됩니다. 다대다 어노테이션을 무조건 피해야 한다기보다, 연결 자체에 필요한 데이터가 있는지부터 확인하는 것이 선택 기준입니다.
