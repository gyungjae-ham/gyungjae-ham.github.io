---
author: "luca"
pubDatetime: 2023-05-18T11:55:58+09:00
title: "SpringBoot JPA로 Entity 클래스 구성하기"
slug: "springboot-jpa-entity-setup"
featured: false
draft: false
tags: ["spring-boot", "jpa", "entity", "setup"]
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

## Pattern Matching (Java 14+)

기존 `instanceof` 후 명시적 캐스팅을 하던 코드 대신, 직접 변수 선언이 가능합니다.

```java
if (!(o instanceof Article article)) return false;
```

`instanceof` 와 캐스팅을 한 번에 처리하기 때문에 `equals` 같은 메서드에서 보일러플레이트가 줄어듭니다.

## Auditing Field 분리 방법

생성·수정 일시 같은 감시 필드를 반복해서 적기 어려우므로 분리하는 두 가지 접근이 있습니다.

1. **`@Embedded`** — 필드로 별도 클래스 포함
2. **`@MappedSuperclass`** — 상속을 통한 중복 필드 통합

상속 방식을 추천하며, 이 방식이 데이터베이스 테이블 구조와의 괴리감이 덜하다고 평가합니다. 다만 분리 방식은 팀의 취향과 도메인 모델의 순수성에 대한 트레이드오프가 있으니 팀 차원에서 결정하는 편이 좋습니다.

## equals / hashCode

Entity 클래스에서 `equals` 와 `hashCode` 를 오버라이드할 때는 **모든 필드가 아닌 `id` 만 비교** 하는 것이 일반적입니다. 영속성 컨텍스트가 동일성을 보장하는 단위가 식별자이기 때문입니다.
