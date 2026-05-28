---
author: "luca"
pubDatetime: 2023-05-24T22:38:06+09:00
title: "연관관계 매핑"
slug: "jpa-association-mapping"
featured: false
draft: false
tags: ["jpa", "association", "relationship", "orm"]
description: "테이블 중심 설계의 한계, 단방향·양방향 연관관계, 연관관계의 주인과 mappedBy 까지 객체 지향 매핑의 핵심을 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 테이블을 중심으로 엔티티를 만들 경우

테이블 구조를 기준으로 엔티티를 설계하면 객체 지향적이지 않은 코드가 됩니다.

```java
@Entity
public class Member {
    @Id @GeneratedValue
    @Column(name = "member_id")
    private Long id;
    // ...
}

@Entity
public class Order {
    @Id @GeneratedValue
    @Column(name = "order_id")
    private Long id;

    @Column(name = "member_id")
    private Long memberId;
    // ...
}
```

이 경우 연관된 객체에 접근하려면 여러 번의 쿼리를 거쳐야 합니다.

```java
Order order = em.find(Order.class, 1L);
Long memberId = order.getMemberId();
Member findMember = em.find(Member.class, memberId);
```

객체 참조를 사용하면 다음과 같이 바뀝니다.

```java
@Entity
public class Order {
    @Id @GeneratedValue
    @Column(name = "order_id")
    private Long id;

    private Member member;
    // ...
}

// 직접 접근
Member findMember = order.getMember();
```

## 테이블 설계의 문제점

- 객체 설계가 테이블 설계에 맞춰지게 됩니다.
- 외래키가 객체에 그대로 노출됩니다.
- 객체 그래프 탐색이 불가능합니다.
- UML 관계가 부정확해집니다.

> **UML (Unified Modeling Language)**: 실제 코드를 작성하기 전에 소프트웨어 아키텍처, 변수, 함수를 계획하기 위한 시각화 기법입니다.

## 연관관계가 필요한 이유

- **테이블은 외래키와 `JOIN`** 으로 연관된 레코드를 찾습니다.
- **객체는 참조**를 통해 연관된 객체에 접근합니다.

## 단방향 연관관계 매핑

```java
@Entity
public class Member {
    @ManyToOne
    @JoinColumn(name = "TEAM_ID")
    private Team team;
    // ...
}
```

## 양방향 매핑

데이터베이스 테이블은 외래키 하나로 양방향 관계를 표현하지만, 객체는 양쪽 모두에 명시적인 참조가 필요합니다.

```java
@Entity
public class Team {
    @OneToMany(mappedBy = "team")
    private List<Member> members = new ArrayList<>();
}
```

## 연관관계의 주인과 mappedBy

- **객체 관계**: 단방향 연결 2개로 양방향을 흉내냅니다.
- **테이블 관계**: 외래키 1개로 양방향 연결을 표현합니다.

**양방향 매핑 규칙**

- 주인만 외래키를 관리합니다 (생성, 수정).
- 주인이 아닌 쪽은 읽기 전용입니다.
- 주인은 `mappedBy`를 사용하지 않습니다.
- 주인이 아닌 쪽은 `mappedBy`로 주인을 지정합니다.

**외래키가 있는 쪽을 주인으로 지정합니다.**

```java
// Member 가 주인 (TEAM_ID 를 가짐)
@Entity
public class Member {
    @ManyToOne
    @JoinColumn(name = "TEAM_ID")
    private Team team;
}
```

## 양방향 매핑 시 많이 하는 실수들

### 주인이 아닌 쪽에만 값을 설정

**잘못된 예**

```java
team.getMembers().add(member);  // 주인이 아님, 읽기 전용
```

**올바른 예**

```java
member.setTeam(team);  // 주인 쪽
```

### 순수 객체 상태를 위해 양쪽 모두 설정

DB로 플러시하지 않으면, 주인이 아닌 쪽에만 설정한 변경은 메모리상의 객체에 반영되지 않습니다. 이를 방지하기 위해 항상 양쪽 모두 설정합니다.

```java
public void setTeam(Team team) {
    this.team = team;
    team.getMembers().add(this);
}
```

### 양방향 관계의 무한 루프 주의

- `toString()`, `lombok`, JSON 라이브러리 사용에 주의합니다.
- Entity 객체를 JSON으로 직접 반환하지 말고 DTO를 사용합니다.

## 양방향 매핑 정리

- **단방향 매핑만으로 시작합니다.**
- 양방향 관계는 필요할 때에만 추가합니다.
- 양방향 추가는 데이터베이스 스키마에 영향을 주지 않습니다.
