---
author: "luca"
pubDatetime: 2023-05-24T22:38:06+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "연관관계 매핑"
slug: "jpa-association-mapping"
featured: false
draft: false
tags: ["학습노트", "jpa", "association", "relationship", "orm"]
description: "테이블 중심 설계의 한계, 단방향·양방향 연관관계, 연관관계의 주인과 mappedBy 까지 객체 지향 매핑의 핵심을 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 테이블을 중심으로 엔티티를 만들 경우

외래키를 ID 값으로만 가지고 있으면 관련 객체를 직접 조회해야 합니다. 객체 참조를 매핑하는 방법과 필요한 시점에 ID로 조회하는 방법은 각각 결합도와 조회 비용이 다릅니다. 아래 코드는 매핑에 필요한 부분만 남겼으며 기본 생성자·접근자 등은 생략했습니다.

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

이 예시에서는 주문과 회원을 따로 조회합니다. 객체 참조로 바꾸더라도 지연 로딩을 사용하면 추가 SQL이 발생할 수 있으므로, 매핑만으로 쿼리 수가 줄어든다고 보지는 않습니다.

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

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "member_id")
    private Member member;
    // ...
}

// 직접 접근
Member findMember = order.getMember();
```

## ID로 연결할지 객체로 탐색할지

ID만 보관하면 객체 그래프를 바로 탐색할 수는 없지만, 관련 엔티티를 언제 읽을지 호출부에서 명확히 정할 수 있습니다. 객체 참조는 탐색을 편하게 만드는 대신 로딩 시점과 연관관계 관리 책임을 고려해야 합니다. ID를 사용했다는 사실만으로 설계나 UML이 잘못됐다고 판단하지 않습니다.

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
- 주인이 아닌 쪽의 변경만으로는 이 관계의 FK가 갱신되지 않습니다. 컬렉션 자체를 수정할 수 없다는 뜻은 아닙니다.
- 주인은 `mappedBy`를 사용하지 않습니다.
- 주인이 아닌 쪽은 `mappedBy`로 주인을 지정합니다.

**여기서 다루는 다대일·일대다 양방향 관계에서는 외래키가 있는 다대일 쪽이 주인입니다.**

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
team.getMembers().add(member);  // 메모리만 변경, 이 코드만으로 FK는 갱신되지 않음
```

**올바른 예**

```java
member.setTeam(team);  // 주인 쪽
```

### 순수 객체 상태를 위해 양쪽 모두 설정

`team.getMembers().add(member)`는 메모리의 컬렉션을 바꾸지만 FK를 쓰는 `member.team`은 바꾸지 않습니다. 반대로 `member.setTeam(team)`만 호출하면 DB의 FK는 갱신할 수 있어도 이미 로드된 `team.members`는 자동으로 추가되지 않습니다. 두 객체 참조를 함께 관리해야 메모리와 저장 결과가 어긋나지 않습니다. 아래는 최초 연결 예시이며, 팀을 변경할 때는 이전 팀 컬렉션에서 제거하는 처리도 필요합니다.

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
