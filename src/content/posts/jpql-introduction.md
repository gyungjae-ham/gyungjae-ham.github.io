---
author: "luca"
pubDatetime: 2023-06-15T20:53:39+09:00
modDatetime: 2026-10-13T15:39:22+09:00
title: "JPQL로 회원 검색과 페이지 조회하기"
slug: "jpql-introduction"
featured: false
draft: false
tags: ["학습노트", "jpa", "jpql", "orm"]
description: "회원 전체를 읽어 필터링하지 않고 DB에서 필요한 대상을 고르는 방법입니다. 엔티티 이름으로 쿼리를 작성하고 DTO 조회와 페이징으로 확장해 봅니다."
---

JPA의 `find()`는 ID를 아는 엔티티를 가져올 때 편합니다. 하지만 “18세 이상인 회원을 이름순으로 보여 달라”는 요구에는 ID 하나로 조회하는 API만으로 부족합니다. 모든 회원을 읽어 Java에서 걸러 내는 것도 데이터가 많아지면 부담이 됩니다.

JPQL은 이런 검색 조건을 엔티티와 속성 이름으로 작성하는 쿼리 언어입니다. JPA 구현체가 이를 SQL로 바꿔 DB에서 필요한 행을 조회합니다. 김영한님의 JPA 로드맵을 따라 학습한 내용으로, 기본 문법은 JPA 2.x 기준입니다. Spring Boot 3의 Jakarta Persistence에서는 관련 import가 `javax.persistence`에서 `jakarta.persistence`로 바뀝니다.

## 테이블 대신 엔티티를 대상으로 쓰기

다음은 Member 엔티티에서 나이가 18 이상인 회원을 찾는 예시입니다. 엔티티 매핑과 EntityManager 준비는 생략했습니다.

```java
List<Member> members = em.createQuery(
    "SELECT m FROM Member m WHERE m.age >= :age ORDER BY m.username, m.id",
    Member.class
).setParameter("age", 18).getResultList();
```

여기서 `Member`는 테이블 이름이 아니라 엔티티 이름이고, `age`와 `username`은 객체의 속성입니다. 엔티티·속성 이름은 대소문자를 구분합니다. `m`은 쿼리 안에서 사용하는 별칭입니다.

입력값은 문자열에 직접 이어 붙이지 않고 파라미터로 바인딩합니다. 위처럼 이름을 붙이면 조건이 늘어도 어떤 값이 들어가는지 읽기 쉽습니다. 결과가 없을 때 `getResultList()`는 빈 목록을 반환합니다. 반면 `getSingleResult()`는 정확히 한 결과를 기대하므로 0건이면 `NoResultException`, 여러 건이면 `NonUniqueResultException`이 발생합니다.

## 화면에 필요한 값만 DTO로 받기

이름과 나이만 표시하는 목록이라면 회원 엔티티 전체가 필요하지 않을 수 있습니다. 조회할 대상을 SELECT에 지정하는 것을 프로젝션이라고 합니다.

```sql
SELECT m FROM Member m
SELECT m.username, m.age FROM Member m
SELECT new example.MemberSummary(m.username, m.age) FROM Member m
```

첫 쿼리는 엔티티를, 두 번째는 개별 값을 반환합니다. 세 번째는 DTO 생성자를 호출하는 표현입니다. `example.MemberSummary`는 설명용 클래스 이름이며, 실제 패키지를 포함한 이름과 값의 순서·타입에 맞는 생성자가 필요합니다. 여러 값을 `Object[]`로 받은 뒤 순서대로 꺼내기보다 결과의 의미를 DTO에 담을 수 있습니다.

## 정렬을 정한 뒤 페이지를 자르기

```java
List<Member> page = em.createQuery(
    "SELECT m FROM Member m ORDER BY m.username DESC, m.id DESC",
    Member.class
).setFirstResult(10)
 .setMaxResults(20)
 .getResultList();
```

시작 위치는 0부터 계산하므로 이 예시는 앞의 10개를 건너뛰고 최대 20개를 가져옵니다. 이름이 같은 회원도 있을 수 있어 ID를 함께 정렬 조건에 넣었습니다. 다만 이처럼 순서를 정해도 요청 사이에 데이터가 추가·삭제되면 offset 기반 페이지의 내용은 달라질 수 있습니다.

## 팀 이름을 조건에 사용하는 조회

회원 여러 명이 한 팀에 속한다고 가정하면 엔티티 관계를 따라 조인할 수 있습니다.

```sql
SELECT m FROM Member m JOIN m.team t WHERE t.name = '팀A'
SELECT m, t FROM Member m LEFT JOIN m.team t ON t.name = '팀A'
```

첫 쿼리는 팀 A 소속 회원을 고릅니다. 두 번째는 회원을 남겨 두고 팀 A에 해당하는 경우에만 팀을 연결합니다. LEFT JOIN의 조건을 ON에 둘지 WHERE에 둘지에 따라 회원이 결과에 남는지가 달라집니다.

일반 조인이 연관 엔티티의 로딩까지 보장하는 것은 아닙니다. 화면에서 회원과 팀 객체를 함께 사용할 때는 [fetch join과 일반 조인의 차이](/posts/jpql-path-fetchjoin-polymorphism/)도 확인해야 합니다.

서브쿼리로 다른 조회 결과와 비교할 수도 있습니다.

```sql
SELECT m FROM Member m
WHERE m.age > (SELECT AVG(other.age) FROM Member other)
```

표준 JPQL과 Hibernate의 확장은 지원 범위가 다릅니다. SQL에서 되던 모든 FROM 서브쿼리나 DB 함수를 그대로 쓸 수 있다고 가정하면 안 됩니다. 실제 버전의 지원 문법을 확인하고, 복잡한 조회는 생성 SQL과 실행 계획도 봐야 합니다.

검색 조건이 선택적으로 늘어나면 문자열 JPQL을 조합하는 코드가 복잡해집니다. 그때 [QueryDSL](/posts/querydsl-setup-and-basics/)을 사용하면 조건을 Java 코드로 조합할 수 있습니다. JPQL의 조회 의미를 이해한 뒤 옮기면 코드가 짧아졌다는 것뿐 아니라 어떤 SQL이 필요한지도 함께 판단하기 쉽습니다.
