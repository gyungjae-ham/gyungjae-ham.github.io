---
author: "luca"
pubDatetime: 2023-05-18T13:33:27+09:00
modDatetime: 2026-10-13T15:44:59+09:00
title: "JPA가 줄여 주는 코드와 직접 확인할 SQL"
slug: "why-jpa"
featured: false
draft: false
tags: ["학습노트", "jpa", "orm", "introduction"]
description: "엔티티 저장과 변경 감지는 반복적인 SQL 작성을 줄여 줍니다. 같은 객체의 재조회, 쓰기 지연, 연관 로딩에서 그 기능이 적용되는 조건을 살펴봅니다."
---

회원 정보를 조회하고 수정하는 기능에는 SQL 결과를 객체로 옮기고 변경할 값을 UPDATE 파라미터에 넣는 코드가 반복됩니다. JPA는 매핑된 엔티티를 관리해 이런 반복 작업을 줄여 줍니다.

김영한님의 JPA 로드맵을 학습하면서 저장·조회 코드가 간단해지는 점과, 그래도 직접 확인해야 할 SQL을 함께 정리했습니다.

```java
em.persist(member);
Member found = em.find(Member.class, memberId);
found.setName("변경할 이름");
em.remove(found);
```

위 코드는 하나의 사용 흐름을 실행한 결과가 아니라 각 연산의 형태입니다. managed 엔티티의 변경은 flush 때 SQL로 동기화될 수 있습니다. 매핑을 통해 반복 SQL을 줄이지만, 스키마 마이그레이션과 커스텀 쿼리까지 필드 추가만으로 해결되는 것은 아닙니다.

## 같은 회원을 다시 조회할 때

하나의 영속성 컨텍스트에서 ID가 1인 회원을 `find`로 두 번 조회하면 같은 managed 인스턴스를 받습니다. 이미 관리 중인 객체를 다시 사용할 수 있어 DB 접근을 줄일 수 있습니다. 이때의 캐시는 애플리케이션 모든 요청이 공유하는 캐시와는 다릅니다.

이 기능을 DB의 `REPEATABLE READ` 격리 수준과 동일하게 볼 수는 없습니다. JPQL의 검색 결과, 새로운 행, 스칼라 조회까지 모두 같은 스냅샷으로 고정하는 것이 아니기 때문입니다. 자세한 내용은 [영속성 컨텍스트](/posts/jpa-persistence-context/)에서 다룹니다.

## 쓰기 지연과 JDBC 배치는 다르다

JPA는 변경 SQL을 flush까지 미룰 수 있지만 모든 INSERT가 커밋 시점까지 대기하지는 않습니다. IDENTITY 생성 전략에서는 ID를 얻기 위해 이른 INSERT가 필요할 수 있습니다. 명시적 flush나 쿼리 전 자동 flush도 있습니다.

여러 SQL이 실제 JDBC 배치로 전송되는지는 Hibernate의 batch 설정, ID 전략, 드라이버 등 추가 조건에 달려 있습니다. 엔티티를 여러 번 `persist`했다는 사실만으로 배치가 적용됐다고 판단하지 않습니다.

## 객체 탐색에도 조회 비용이 있다

`member.getTeam()`처럼 관계를 탐색할 수 있지만 접근 시 추가 SQL이 발생할 수 있습니다. `EAGER`는 연관 데이터를 즉시 준비하라는 요구이며, 언제나 JOIN 한 번으로 읽으라는 뜻은 아닙니다. 필요한 화면의 조회 경로에서 fetch join·DTO 조회·batch fetch를 선택하고 실제 SQL을 확인합니다.

JPA의 이점은 SQL을 몰라도 된다는 데 있지 않습니다. 반복적인 저장 코드를 줄인 뒤, 중요한 조회에 어떤 SQL이 나가는지 더 집중해서 볼 수 있다는 데 있습니다.
