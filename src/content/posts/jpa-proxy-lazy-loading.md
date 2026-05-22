---
author: "luca"
pubDatetime: 2023-06-07T21:49:07+09:00
title: "JPA 프록시, 지연로딩, 고아 객체"
slug: "jpa-proxy-lazy-loading"
featured: false
draft: false
tags: ["jpa", "proxy", "lazy-loading", "orphan-removal"]
description: "JPA 프록시 동작 원리와 지연·즉시 로딩 선택, 영속성 전이와 고아 객체 옵션까지 한 번에 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 프록시

### 프록시 기초

- **`em.find()`**: 데이터베이스를 통해 실제 엔티티 객체를 조회합니다.
- **`em.getReference()`**: "데이터베이스 조회를 미루는 가짜(프록시) 엔티티를 조회"합니다.
  - 실제 사용 시점에 쿼리가 실행됩니다.

### 프록시 특징

- 실제 클래스를 상속받아 생성됩니다.
- 실제 클래스와 동일한 외형을 가집니다.
- 프록시 객체는 실제 객체의 참조(`target`)를 보관합니다.
- 프록시 객체를 호출하면 실제 객체의 메소드가 실행됩니다.

### 프록시 객체 초기화

메소드를 호출하는 시점에 영속성 컨텍스트에 요청하여 실제 엔티티를 `target`에 매핑합니다.

### 프록시 주의사항

- "처음 사용할 때 한 번만 초기화됩니다."
- 초기화 후에도 프록시 객체는 유지되며, 실제 엔티티에 접근할 수 있게 됩니다.
- 타입 체크 시 `instanceof`를 사용해야 합니다 (`==` 비교는 실패할 수 있습니다).
- "영속성 컨텍스트에 찾는 엔티티가 이미 있으면 실제 엔티티를 반환합니다."
- 준영속 상태에서 초기화하면 `LazyInitializationException`이 발생합니다.

### 프록시 확인 방법

```java
emf.getPersistenceUnitUtil().isLoaded(entity);
org.hibernate.Hibernate.initialize(entity);
```

## 즉시 로딩과 지연 로딩

### 지연 로딩

```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "TEAM_ID")
private Team team;
```

연관 엔티티를 프록시로 조회하고, 실제 사용 시점에 쿼리를 실행합니다.

### 즉시 로딩

```java
@ManyToOne(fetch = FetchType.EAGER)
@JoinColumn(name = "TEAM_ID")
private Team team;
```

엔티티를 조회할 때 연관 엔티티도 함께 조회합니다.

### 주의사항

- "가급적이면 지연 로딩만 사용하도록 합니다 (특히 실무에서는)."
- 즉시 로딩은 "N + 1 문제를 일으킵니다."
- `@ManyToOne`, `@OneToOne`은 기본이 즉시 로딩이므로 `LAZY`로 설정해야 합니다.
- `@OneToMany`, `@ManyToMany`는 기본이 지연 로딩입니다.

## 영속성 전이: CASCADE

특정 엔티티를 영속화할 때 연관 엔티티도 함께 영속화합니다.

**주요 종류**: `ALL`, `PERSIST`, `REMOVE`, `MERGE`, `REFRESH`, `DETACH`

## 고아 객체

"부모 엔티티와 연관관계가 끊어진 자식 엔티티를 자동으로 삭제합니다."

```java
orphanRemoval = true
```

### 주의사항

- "참조하는 곳(엔티티)이 하나일 때 사용합니다."
- 특정 엔티티의 개인 소유일 때만 사용합니다.
- `@OneToOne`, `@OneToMany`만 가능합니다.

### CASCADE.ALL + orphanRemoval = true

자식 엔티티의 생명주기를 부모를 통해 관리할 수 있으며, DDD의 Aggregate Root 개념 구현에 유용합니다.
