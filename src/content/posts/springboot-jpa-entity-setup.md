---
author: "luca"
pubDatetime: 2023-05-18T11:55:58+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "SpringBoot JPA로 Entity 클래스 구성하기"
slug: "springboot-jpa-entity-setup"
featured: false
draft: false
tags: ["학습노트", "spring-boot", "jpa", "entity", "setup"]
description: "JPA Entity 클래스를 구성할 때 자주 사용하는 어노테이션, Pattern Matching, Auditing 필드 분리 방법을 정리합니다."
---

> Spring Boot 에서 JPA Entity 클래스를 작성할 때 챙겨야 할 어노테이션과 설계 선택지를 짧게 정리하는 글입니다.

## 주요 어노테이션과 설정

Entity 클래스 작성 시 자주 등장하는 어노테이션과 설정을 정리합니다.

- **`@Getter`, `@ToString`** — 편의성을 위한 롬복 어노테이션
- **`@Table(indexes = {...})`** — 빠른 검색을 위한 인덱스 설정
- **`@EntityListeners(AuditingEntityListener.class)`** — Auditing 활성화
- **`@Id @GeneratedValue(strategy = GenerationType.IDENTITY)`** — 기본 키 설정
- **`@OneToMany(mappedBy = "article", cascade = CascadeType.ALL)`** — 양방향 관계 설정
- **`@CreatedDate`, `@CreatedBy`, `@LastModifiedDate`, `@LastModifiedBy`** — 감시 필드

## Pattern Matching (Java 16 정식 기능)

Java 14·15에서는 preview였고 Java 16에서 정식 기능이 됐습니다. 기존 `instanceof` 후 명시적 캐스팅을 하던 코드 대신 직접 변수를 선언할 수 있습니다. [JEP 394](https://openjdk.org/jeps/394)

```java
if (!(o instanceof Article article)) return false;
```

`instanceof` 와 캐스팅을 한 번에 처리하기 때문에 `equals` 같은 메서드에서 보일러플레이트가 줄어듭니다.

## Auditing Field 분리 방법

생성·수정 일시 같은 감시 필드를 반복해서 적기 어려우므로 분리하는 두 가지 접근이 있습니다.

1. **`@Embedded`** — 필드로 별도 클래스 포함
2. **`@MappedSuperclass`** — 상속을 통한 중복 필드 통합

상속 방식이 데이터베이스 테이블 구조와 가깝게 매핑되어 편합니다. 다만 도메인 모델의 순수성을 중시한다면 `@Embedded` 가 더 자연스러우니, 팀 차원에서 한 가지를 정해두는 편이 좋습니다.

## equals / hashCode

DB 생성 ID로 동등성을 구현할 때는 저장 전 `id == null`인 서로 다른 객체를 같다고 취급하지 않아야 합니다. 또한 저장 후 ID가 생기며 hash 값이 바뀌면 이미 HashSet에 넣은 객체를 찾지 못할 수 있습니다. Hibernate 프록시와 일반 객체의 클래스 비교도 검토 대상입니다.

따라서 ID만 비교하는 코드를 일괄 적용하기보다, 불변 자연키가 있는지·저장 전 객체를 컬렉션 키로 쓰는지·준영속 객체끼리 비교하는지를 먼저 정합니다. 영속성 컨텍스트의 인스턴스 동일성과 애플리케이션의 `equals` 정책은 별개의 문제입니다.
