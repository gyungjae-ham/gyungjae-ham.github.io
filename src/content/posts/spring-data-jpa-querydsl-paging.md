---
author: "luca"
pubDatetime: 2023-06-18T17:42:44+09:00
title: "스프링 데이터 JPA와 QueryDSL, 페이징"
slug: "spring-data-jpa-querydsl-paging"
featured: false
draft: false
tags: ["querydsl", "jpa", "spring-data-jpa", "java"]
description: "스프링 데이터 JPA 의 사용자 정의 리포지토리에 QueryDSL 을 얹어 페이징을 구현하고, 카운트 쿼리까지 최적화하는 흐름을 정리합니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 스프링 데이터 JPA - MemberRepository

스프링 데이터 JPA 가 제공하는 기본 리포지토리 모양은 다음과 같습니다.

```java
public interface MemberRepository extends JpaRepository<Member, Long> {
    List<Member> findByUsername(String username);
}
```

## 사용자 정의 레포지토리

### 1. 사용자 정의 인터페이스 작성

QueryDSL 로 작성한 동적 쿼리를 스프링 데이터 JPA 리포지토리에 얹기 위해 별도의 인터페이스를 만듭니다.

```java
public interface MemberRepositoryCustom {
    List<MemberTeamDto> search(MemberSearchCondition condition);
}
```

### 2. 사용자 정의 인터페이스 구현

- 커스텀하려는 `Repository` 클래스 명 + `Impl` 로 구현을 해줘야 합니다.

```java
public class MemberRepositoryImpl implements MemberRepositoryCustom {

    private final JPAQueryFactory queryFactory;

    public MemberRepositoryImpl(EntityManager em) {
        this.queryFactory = new JPAQueryFactory(em);
    }

    @Override
    // 회원명, 팀명, 나이(ageGoe, ageLoe)
    public List<MemberTeamDto> search(MemberSearchCondition condition) {
        return queryFactory
                .select(new QMemberTeamDto(
                        member.id,
                        member.username,
                        member.age,
                        team.id,
                        team.name))
                .from(member)
                .leftJoin(member.team, team)
                .where(
                        usernameEq(condition.getUsername()),
                        teamNameEq(condition.getTeamName()),
                        ageGoe(condition.getAgeGoe()),
                        ageLoe(condition.getAgeLoe()
                        ))
                .fetch();
    }

    private BooleanExpression usernameEq(String username) {
        return hasText(username) ? member.username.eq(username) : null;
    }

    private BooleanExpression teamNameEq(String teamName) {
        return hasText(teamName) ? team.name.eq(teamName) : null;
    }

    private BooleanExpression ageGoe(Integer ageGoe) {
        return ageGoe != null ? member.age.goe(ageGoe) : null;
    }

    private BooleanExpression ageLoe(Integer ageLoe) {
        return ageLoe != null ? member.age.loe(ageLoe) : null;
    }
}
```

### 3. 스프링 데이터 레포지토리에 사용자 정의 인터페이스 상속

```java
public interface MemberRepository extends JpaRepository<Member, Long>, MemberRepositoryCustom {
    List<Member> findByUsername(String username);
}
```

## QueryDSL 페이징 연동

### 사용자 정의 인터페이스에 페이징 2가지 추가하기

```java
public interface MemberRepositoryCustom {
    List<MemberTeamDto> search(MemberSearchCondition condition);

    Page<MemberTeamDto> searchPageSimple(MemberSearchCondition condition, Pageable pageable);

    Page<MemberTeamDto> searchPageComplex(MemberSearchCondition condition, Pageable pageable);
}
```

### 전체 카운트를 한번에 조회하는 방법

#### searchPageSimple(): fetchResults() 사용

```java
@Override
public Page<MemberTeamDto> searchPageSimple(MemberSearchCondition condition, Pageable pageable) {
        QueryResults<MemberTeamDto> results = queryFactory
                .select(new QMemberTeamDto(
                        member.id.as("memberId"),
                        member.username,
                        member.age,
                        team.id.as("teamId"),
                        team.name.as("teamName")))
                .from(member)
                .leftJoin(member.team, team)
                .where(
                        usernameEq(condition.getUsername()),
                        teamNameEq(condition.getTeamName()),
                        ageGoe(condition.getAgeGoe()),
                        ageLoe(condition.getAgeLoe()
                        ))
                .offset(pageable.getOffset())
                .limit(pageable.getPageSize())
                .fetchResults();

        List<MemberTeamDto> content = results.getResults();
        long total = results.getTotal();

        return new PageImpl<>(content, pageable, total);
}
```

- QueryDSL 이 제공하는 `fetchResults()` 를 사용하면 내용과 카운트를 한 번에 조회할 수 있습니다 (**실제 쿼리는 2번 실행됩니다 — 기본 쿼리, count 쿼리**).
- `fetchResults()` 는 카운트 쿼리 실행 시 필요 없는 `order by` 를 제거합니다.

#### searchPageComplex()

```java
/**
  * 복잡한 페이징
  * 데이터 조회 쿼리와, 전체 카운트 쿼리를 분리
  */
@Override
public Page<MemberTeamDto> searchPageComplex(MemberSearchCondition condition, Pageable pageable) {
        List<MemberTeamDto> content = queryFactory
                .select(new QMemberTeamDto(
                        member.id,
                        member.username,
                        member.age,
                        team.id,
                        team.name))
                .from(member)
                .leftJoin(member.team, team)
                .where(
                        usernameEq(condition.getUsername()),
                        teamNameEq(condition.getTeamName()),
                        ageGoe(condition.getAgeGoe()),
                        ageLoe(condition.getAgeLoe()
                        ))
                .offset(pageable.getOffset())
                .limit(pageable.getPageSize())
                .fetch();

        long total = queryFactory
                        .select(member)
                        .from(member)
                        .leftJoin(member.team, team)
                        .where(usernameEq(condition.getUsername()),
                               teamNameEq(condition.getTeamName()),
                               ageGoe(condition.getAgeGoe()),
                               ageLoe(condition.getAgeLoe()))
                        .fetchCount();

        return new PageImpl<>(content, pageable, total);
}
```

- 전체 카운트를 조회하는 방법을 최적화할 수 있으면 이렇게 분리합니다.
- 조회 쿼리와 별개로 카운트 쿼리는 단순해서 최적화해야 할 경우에 이렇게 사용합니다.

### Count 쿼리 최적화

카운트 쿼리가 생략 가능한 경우에는 생략해서 처리합니다.

- 페이지 시작이면서 컨텐츠 사이즈가 페이지 사이즈보다 작을 경우
- 마지막 페이지일 때 (`offset` + 컨텐츠 사이즈를 더해서 전체 사이즈를 구함)

진행 흐름은 다음과 같습니다.

- 기존 `count` 쿼리를 날리던 부분에서 `fetchCount()` 를 제외하고 변수로 만들어줍니다.
- 해당 변수는 `변수명.fetchCount()` 를 실행해야 카운트 쿼리를 날리는 상태입니다.
- 스프링 데이터에서 제공하는 `PageableExecutionUtils.getPage` 를 사용합니다.
- 필요한 경우에만 카운트 쿼리가 동작하게 됩니다.

```java
JPAQuery<Member> countQuery = queryFactory
        .select(member)
        .from(member)
        .leftJoin(member.team, team)
        .where(usernameEq(condition.getUsername()),
               teamNameEq(condition.getTeamName()),
               ageGoe(condition.getAgeGoe()),
               ageLoe(condition.getAgeLoe())
        );

return PageableExecutionUtils.getPage(content, pageable, countQuery::fetchCount);
```
