---
author: "luca"
pubDatetime: 2023-05-18T13:33:27+09:00
title: "JPA 장점"
slug: "why-jpa"
featured: false
draft: false
tags: ["jpa", "orm", "introduction"]
description: "CRUD 생산성, 유지보수, 객체-관계 패러다임 불일치 해결, 1차 캐시·쓰기 지연 등 JPA 의 장점을 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 생산성 — JPA 와 CRUD

- **저장**: `jpa.persist(member)`
- **조회**: `Member member = jpa.find(memberId)`
- **수정**: `member.setName("변경할 이름")`
- **삭제**: `jpa.remove(member)`

## 유지보수

- **기존**: 필드가 변경되면 모든 SQL을 수정해야 했습니다.
- **JPA**: 필드만 추가하면 됩니다 (JPA가 SQL을 생성해 주기 때문입니다).

## JPA와 패러다임 불일치 해결

### 1. JPA와 상속

- 상속관계일 경우 (DB에서는 슈퍼타입 테이블과 서브타입 테이블 관계일 경우)
  - 저장할 때, 관계 맺은 테이블들에 모두 `INSERT`를 해야 하지만 JPA를 사용하면 `jpa.persist(객체)`만 호출하면 나머지 SQL은 JPA가 알아서 처리합니다.
  - 조회할 때, 관계를 맺은 테이블들을 `JOIN`해서 SQL문을 작성해야 하지만 `jpa.find(객체.class, id)`만 호출하면 나머지 SQL을 JPA가 알아서 처리합니다.

### 2. JPA와 연관관계

연관관계를 저장할 때는 `member.setTeam(team)`, `jpa.persist(member)`와 같이 저장할 수 있습니다.

### 3. JPA와 객체 그래프 탐색

```java
Member member = jpa.find(Member.class, memberId);
Team team = member.getTeam();
```

객체 참조를 따라 그래프를 탐색할 수 있습니다.

### 4. JPA와 비교하기

동일한 트랜잭션에서 조회한 엔티티는 같음을 보장받습니다.

```java
String memberId = "100";
Member member1 = jpa.find(Member.class, memberId);
Member member2 = jpa.find(Member.class, memberId);

member1 == member2 // 같다
```

### 5. JPA의 성능 최적화 기능

#### 1차 캐시와 동일성 보장

- 같은 트랜잭션 안에서는 같은 엔티티를 반환합니다 — 약간의 조회 성능 향상이 있으며 위 조회에서 SQL은 1번만 실행됩니다.
- DB Isolation Level이 `Read Commit`이어도 애플리케이션에서 `Repeatable Read`를 보장합니다.

#### 트랜잭션을 지원하는 쓰기 지연 — INSERT

- 트랜잭션을 커밋할 때까지 `INSERT SQL`을 모읍니다.
- JDBC BATCH SQL 기능을 사용해서 한 번에 SQL을 전송합니다.

```java
transaction.begin(); // [트랜잭션] 시작

em.persist(memberA);
em.persist(memberB);
em.persist(memberC);
// 여기까지 INSERT SQL을 데이터베이스에 보내지 않는다.

// 커밋하는 순간 데이터베이스에 INSERT SQL을 모아서 한번에 보낸다.
transaction.commit(); // [트랜잭션] 커밋
```

#### 지연 로딩과 즉시 로딩

- **지연 로딩**: 객체가 실제 사용될 때 로딩합니다.
- **즉시 로딩**: `JOIN SQL`로 한 번에 연관된 객체까지 미리 조회합니다.
