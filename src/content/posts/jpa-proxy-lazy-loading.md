---
author: "luca"
pubDatetime: 2023-06-07T21:49:07+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 프록시, 지연로딩, 고아 객체"
slug: "jpa-proxy-lazy-loading"
featured: false
draft: false
tags: ["학습노트", "jpa", "proxy", "lazy-loading", "orphan-removal"]
description: "JPA 프록시 동작 원리와 지연·즉시 로딩 선택, 영속성 전이와 고아 객체 옵션까지 한 번에 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 프록시

### 프록시 기초

- **`em.find()`**: 식별자로 엔티티를 찾습니다. 영속성 컨텍스트에 이미 있으면 DB 조회 없이 반환할 수 있습니다.
- **`em.getReference()`**: 상태 조회를 미룰 수 있는 참조를 얻습니다. Hibernate에서는 미초기화 프록시일 수 있지만, 이미 관리 중인 엔티티나 설정에 따라 새 프록시를 만들지 않을 수도 있습니다.

### 프록시 특징

- 아래 특징은 Hibernate의 일반적인 서브클래스 프록시를 기준으로 합니다. 바이트코드 enhancement를 쓰는 방식과는 구분합니다.
- 실제 클래스와 동일한 외형을 가집니다.
- 프록시 객체는 실제 객체의 참조(`target`)를 보관합니다.
- 프록시 객체를 호출하면 실제 객체의 메소드가 실행됩니다.

### 프록시 객체 초기화

메소드를 호출하는 시점에 영속성 컨텍스트에 요청하여 실제 엔티티를 `target`에 매핑합니다.

### 프록시 주의사항

- 처음 사용할 때 한 번만 초기화됩니다.
- 초기화 후에도 프록시 객체는 유지되며, 실제 엔티티에 접근할 수 있게 됩니다.
- 타입 체크 시 `instanceof`를 사용해야 합니다 (`==` 비교는 실패할 수 있습니다).
- 영속성 컨텍스트에 찾는 엔티티가 이미 있으면 실제 엔티티를 반환합니다.
- 세션이 닫힌 뒤 미초기화 참조를 사용하면 `LazyInitializationException`이 날 수 있습니다. 이미 로딩된 데이터 접근까지 모두 실패하는 것은 아닙니다.

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

- 조회마다 필요한 데이터가 다르면 LAZY를 기본으로 두고 fetch join·EntityGraph 등으로 조회 범위를 명시할 수 있습니다. LAZY도 반복 접근하면 N+1이 발생합니다.
- EAGER는 연관 데이터를 함께 준비하라는 요구이며, 반드시 SQL JOIN 한 번으로 가져오라는 뜻은 아닙니다. 추가 SELECT가 발생할 수 있습니다.
- `@ManyToOne`, `@OneToOne`의 기본은 EAGER입니다. LAZY 적용 여부에는 프록시 생성과 매핑 조건도 영향을 줍니다.
- `@OneToMany`, `@ManyToMany`는 기본이 지연 로딩입니다.

## 영속성 전이: CASCADE

특정 엔티티를 영속화할 때 연관 엔티티도 함께 영속화합니다.

**주요 종류**: `ALL`, `PERSIST`, `REMOVE`, `MERGE`, `REFRESH`, `DETACH`

## 고아 객체

부모 엔티티와 연관관계가 끊어진 자식 엔티티를 자동으로 삭제합니다.

```java
orphanRemoval = true
```

### 주의사항

- 참조하는 곳(엔티티)이 하나일 때 사용합니다.
- 특정 엔티티의 개인 소유일 때만 사용합니다.
- `@OneToOne`, `@OneToMany`만 가능합니다.

### CASCADE.ALL + orphanRemoval = true

자식 엔티티의 생명주기를 부모를 통해 관리할 수 있으며, DDD의 Aggregate Root 개념 구현에 유용합니다.

예를 들어 회원 10명의 이름만 보여주는 화면과 팀 이름까지 보여주는 화면은 필요한 데이터가 다릅니다. 팀이 모두 다르고 캐시가 비어 있다는 가정에서, 회원 목록 뒤에 팀을 하나씩 조회하면 추가 SELECT가 최대 10회 생길 수 있습니다. 이 숫자는 측정 결과가 아닌 N+1을 설명하는 예입니다. [조회별 fetch 계획과 배치 크기](/posts/jpa-performance-tuning/)에서 이 차이를 더 다룹니다. 구현 세부사항은 [Hibernate 6.6 문서](https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html)를 참고했습니다.
