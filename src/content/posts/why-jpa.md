---
author: "luca"
pubDatetime: 2023-05-18T13:33:27+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 장점"
slug: "why-jpa"
featured: false
draft: false
tags: ["학습노트", "jpa", "orm", "introduction"]
description: "CRUD 생산성, 유지보수, 객체-관계 패러다임 불일치 해결, 1차 캐시·쓰기 지연 등 JPA 의 장점을 정리한 학습 노트입니다."
---

JPA를 사용하면 엔티티의 저장·조회·변경을 객체 중심으로 표현할 수 있습니다. 이 노트는 김영한님의 JPA 로드맵을 학습하며 정리한 개념을 바탕으로, 편리한 기능과 그 기능이 적용되는 조건을 나눠 설명합니다.

```java
em.persist(member);
Member found = em.find(Member.class, memberId);
found.setName("변경할 이름");
em.remove(found);
```

위 코드는 하나의 사용 흐름을 실행한 결과가 아니라 각 연산의 형태입니다. managed 엔티티의 변경은 flush 때 SQL로 동기화될 수 있습니다. 매핑을 통해 반복 SQL을 줄이지만, 스키마 마이그레이션과 커스텀 쿼리까지 필드 추가만으로 해결되는 것은 아닙니다.

## 같은 객체를 관리하는 범위

같은 영속성 컨텍스트에서 같은 식별자의 엔티티를 조회하면 같은 managed 인스턴스를 받습니다. 이미 관리 중인 객체를 `find`로 조회할 때 DB 접근을 줄일 수 있습니다.

이 기능을 DB의 `REPEATABLE READ` 격리 수준과 동일하게 볼 수는 없습니다. JPQL의 검색 결과, 새로운 행, 스칼라 조회까지 모두 같은 스냅샷으로 고정하는 것이 아니기 때문입니다. 자세한 내용은 [영속성 컨텍스트](/posts/jpa-persistence-context/)에서 다룹니다.

## 쓰기 지연과 JDBC 배치는 다르다

JPA는 변경 SQL을 flush까지 미룰 수 있지만 모든 INSERT가 커밋 시점까지 대기하지는 않습니다. IDENTITY 생성 전략에서는 ID를 얻기 위해 이른 INSERT가 필요할 수 있습니다. 명시적 flush나 쿼리 전 자동 flush도 있습니다.

여러 SQL이 실제 JDBC 배치로 전송되는지는 Hibernate의 batch 설정, ID 전략, 드라이버 등 추가 조건에 달려 있습니다. 엔티티를 여러 번 `persist`했다는 사실만으로 배치가 적용됐다고 판단하지 않습니다.

## 객체 탐색에도 조회 비용이 있다

`member.getTeam()`처럼 관계를 탐색할 수 있지만 접근 시 추가 SQL이 발생할 수 있습니다. `EAGER`는 연관 데이터를 즉시 준비하라는 요구이며, 언제나 JOIN 한 번으로 읽으라는 뜻은 아닙니다. 필요한 화면의 조회 경로에서 fetch join·DTO 조회·batch fetch를 선택하고 실제 SQL을 확인합니다.

JPA의 이점은 SQL을 몰라도 된다는 데 있지 않습니다. 반복적인 저장 코드를 줄인 뒤, 중요한 조회에 어떤 SQL이 나가는지 더 집중해서 볼 수 있다는 데 있습니다.
