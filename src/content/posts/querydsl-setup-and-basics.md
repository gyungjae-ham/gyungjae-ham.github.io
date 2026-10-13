---
author: "luca"
pubDatetime: 2023-06-17T16:35:37+09:00
modDatetime: 2026-10-13T15:47:36+09:00
title: "QueryDSL로 회원 검색 쿼리 작성하기"
slug: "querydsl-setup-and-basics"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "spring-data-jpa", "java"]
description: "회원명 검색에서 팀별 집계까지 같은 데이터로 쿼리를 확장합니다. Q 타입, 조건, 정렬, 조인과 서브쿼리의 의미를 코드와 결과로 확인합니다."
---

회원명으로 찾던 검색에 나이 범위와 팀 조건이 추가되면 문자열 JPQL을 조합하는 코드가 길어집니다. QueryDSL은 엔티티를 나타내는 Q 타입을 사용해 이 조건을 Java 코드로 작성하게 해 줍니다. 필드명과 타입 오류를 컴파일 단계에서 찾기 쉽지만, 생성된 쿼리의 성능까지 보장하는 것은 아닙니다.

김영한님의 JPA 로드맵을 학습한 예제이며 **Java 17·Spring Boot 3.0.x·QueryDSL 5.0.0**을 기준으로 합니다. 설정은 [Q 타입 생성하기](/posts/querydsl-quick-setup/)에 따로 정리했습니다. 여기서는 준비된 `JPAQueryFactory`, `QMember.member`, `QTeam.team`으로 조회하는 코드에 집중합니다.

## 같은 데이터로 결과 비교하기

각 코드는 독립된 조회 예시입니다. 엔티티와 imports는 생략했으며 다음 데이터가 저장돼 있다고 가정합니다. 쓰기 테스트에서는 매번 초기 상태를 준비해야 합니다.

| 회원명  | 나이 | 팀    |
| ------- | ---- | ----- |
| member1 | 10   | teamA |
| member2 | 20   | teamA |
| member3 | 30   | teamB |
| member4 | 40   | teamB |

```java
Member found = queryFactory
    .selectFrom(member)
    .where(member.username.eq("member1"))
    .fetchOne();
```

이 쿼리는 member1을 찾습니다. `member.username`은 문자열 필드 이름이 아니라 생성된 Q 타입의 속성입니다. 같은 엔티티를 한 쿼리에서 여러 용도로 참조할 때는 `new QMember("other")`처럼 다른 별칭을 만들 수 있습니다.

`fetchOne()`은 결과가 없으면 null이고 두 건 이상이면 예외입니다. 목록은 `fetch()`로 받으며, 결과가 없으면 빈 목록을 반환합니다. `fetchFirst()`는 최대 한 건만 가져오지만 어떤 한 건인지 중요하다면 정렬도 지정해야 합니다.

## 조건과 정렬을 붙이기

```java
List<Member> found = queryFactory
    .selectFrom(member)
    .where(member.age.goe(20), member.age.loe(30))
    .orderBy(member.age.desc(), member.id.desc())
    .fetch();
```

`goe`는 이상, `loe`는 이하입니다. 위 데이터에서는 member3, member2 순서가 됩니다. `where`에 여러 조건을 나열하면 AND로 결합하고 null 조건은 무시합니다. 입력에 따라 조건을 생략하는 예제는 [동적 회원 검색](/posts/pure-jpa-with-querydsl/)에서 이어집니다.

문자열에는 `eq`, `contains`, `startsWith` 등을 사용할 수 있습니다. 단순히 편한 메서드로만 보기보다 정확히 일치하는지, 포함하는지에 따라 검색 결과와 인덱스 사용 가능성이 달라진다는 점을 생각해야 합니다.

페이지 제한은 정렬 뒤에 적용합니다.

```java
List<Member> page = queryFactory
    .selectFrom(member)
    .orderBy(member.username.desc(), member.id.desc())
    .offset(1)
    .limit(2)
    .fetch();
```

첫 결과를 건너뛰므로 member3과 member2를 가져오는 예입니다. 정렬값이 같은 경우를 위해 ID를 함께 사용했습니다. 전체 개수까지 필요하면 content와 count 쿼리를 나눠 작성합니다. QueryDSL JPA 5.x의 `fetchResults()`와 `fetchCount()`는 deprecated이며 복잡한 그룹 쿼리의 자동 count 변환에는 한계가 있습니다. [Spring Data 페이징 예제](/posts/spring-data-jpa-querydsl-paging/)

## 팀을 조건에 쓰는 조인과 함께 로딩하는 조인

```java
List<Member> teamMembers = queryFactory
    .selectFrom(member)
    .join(member.team, team)
    .where(team.name.eq("teamA"))
    .fetch();
```

이 조회는 member1과 member2를 고르지만 결과 순서는 지정하지 않았습니다. 테스트에서도 특정 순서라고 단정하면 안 됩니다. 팀을 조인 조건에 사용했다는 사실만으로 `Member.team`이 초기화됐다고 볼 수도 없습니다.

회원과 팀 데이터를 함께 읽으려면 조인 뒤에 `.fetchJoin()`을 사용할 수 있습니다. `Member.team`이 LAZY인 상황에서 로딩 여부를 비교하려면 `flush()`와 `clear()`로 기존 컨텍스트를 비운 뒤 확인해야 합니다. 이미 팀을 읽어 둔 객체를 쓰면 차이가 드러나지 않을 수 있습니다.

LEFT JOIN의 ON 조건은 결과 필터와도 구분합니다.

```java
List<Tuple> rows = queryFactory
    .select(member, team)
    .from(member)
    .leftJoin(member.team, team).on(team.name.eq("teamA"))
    .fetch();
```

이 경우 회원은 남기고 teamA인 경우에만 팀이 연결됩니다. 같은 조건을 WHERE에 두면 teamA에 속하지 않은 회원이 결과에서 빠집니다. 연관관계 없는 엔티티의 외부 조인처럼 Hibernate 확장에 의존하는 문법은 모든 JPA 구현체에서 지원된다고 가정하지 않아야 합니다.

## 팀별 평균과 서브쿼리

```java
List<Tuple> averages = queryFactory
    .select(team.name, member.age.avg())
    .from(member)
    .join(member.team, team)
    .groupBy(team.name)
    .orderBy(team.name.asc())
    .fetch();
```

teamA의 평균은 15, teamB는 35입니다. `groupBy`로 묶은 결과를 필터링하려면 `having`을 사용합니다. 예를 들어 평균이 20 이상인 팀만 남기는 조건을 둘 수 있습니다.

전체 평균보다 나이가 많은 회원은 서브쿼리로 찾을 수도 있습니다.

```java
QMember other = new QMember("other");
List<Member> older = queryFactory
    .selectFrom(member)
    .where(member.age.gt(
        JPAExpressions.select(other.age.avg()).from(other)
    ))
    .fetch();
```

전체 평균은 25이므로 member3과 member4가 대상입니다. 바깥 회원과 평균 계산에 사용하는 회원의 별칭을 구분했습니다. 이 글의 표준 JPQL 기준에서 서브쿼리는 WHERE·HAVING에 사용하며, SELECT 서브쿼리 등은 구현체 확장 지원을 확인해야 합니다.

QueryDSL로 옮겨도 쿼리의 의미는 여전히 같습니다. 어떤 행을 남기는지, 조인으로 행이 늘어나는지, 전체 개수는 무엇을 세는지 작은 데이터로 확인한 뒤 실제 SQL을 보는 순서가 도움이 됩니다.
