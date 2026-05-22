---
author: "luca"
pubDatetime: 2023-06-18T16:13:16+09:00
title: "순수 JPA와 QueryDSL"
slug: "pure-jpa-with-querydsl"
featured: false
draft: false
tags: ["querydsl", "jpa", "java", "dynamic-query"]
description: "순수 JPA 리포지토리에 QueryDSL 을 얹어 동적 쿼리를 만드는 두 가지 방식 — Builder 와 WHERE 다중 파라미터 — 을 정리합니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 실무 활용 - 순수 JPA와 Querydsl

### 순수 JPA 리포지토리

`EntityManager` 와 `JPAQueryFactory` 를 함께 들고 가는 모양이 기본입니다.

```java
@Repository
public class MemberJpaRepository {

    private final EntityManager em;
    private final JPAQueryFactory queryFactory;

    public MemberJpaRepository(EntityManager em) {
        this.em = em;
        this.queryFactory = new JPAQueryFactory(em);
    }

    public void save(Member member) {
        em.persist(member);
    }

    public Optional<Member> findById(Long id) {
        Member findMember = em.find(Member.class, id);
        return Optional.ofNullable(findMember);
    }

    public List<Member> findAll() {
        return em.createQuery("select m from Member m", Member.class)
                .getResultList();
    }

    public List<Member> findByUsername(String username) {
        return em.createQuery("select m from Member m where m.username = :username", Member.class)
                .setParameter("username", username)
                .getResultList();
    }

}
```

### QueryDSL 추가

`em.createQuery` 로 작성하던 JPQL 을 QueryDSL 메서드 체이닝으로 옮긴 모습입니다.

```java
public List<Member> findAll_Querydsl() {
    return queryFactory
            .selectFrom(member).fetch();
}

public List<Member> findByUsername_Querydsl(String username) {
    return queryFactory
            .selectFrom(member)
            .where(member.username.eq(username))
            .fetch();
}
```

## 동적 쿼리와 성능 최적화 조회 - Builder 사용

### 1. 검색 조건 클래스 생성

검색 조건을 묶은 DTO 입니다. 회원명, 팀명, 나이 범위(`ageGoe`, `ageLoe`) 를 받습니다.

```java
@Data
public class MemberSearchCondition {
    // 회원명, 팀명, 나이(ageGoe, ageLoe)
    private String username;
    private String teamName;
    private Integer ageGoe;
    private Integer ageLoe;
}
```

### 2. Builder를 사용한 동적쿼리

`BooleanBuilder` 에 조건을 누적하는 방식입니다.

```java
public List<MemberTeamDto> searchByBuilder(MemberSearchCondition condition) {

        BooleanBuilder builder = new BooleanBuilder();
        // null이 아닌 빈 문자열이 들어올 경우를 대비해서
        // StringUtils.hasText로 검증해줍니다
        if (hasText(condition.getUsername())) {
            builder.and(member.username.eq(condition.getUsername()));
        }
        if (hasText(condition.getTeamName())) {
            builder.and(team.name.eq(condition.getTeamName()));
        }
        if (condition.getAgeGoe() != null) {
            builder.and(member.age.goe(condition.getAgeGoe()));
        }
        if (condition.getAgeLoe() != null) {
            builder.and(member.age.loe(condition.getAgeLoe()));
        }
        return queryFactory
                .select(new QMemberTeamDto(
                        member.id,
                        member.username,
                        member.age,
                        team.id.as("teamId"),
                        team.name.as("teamName")))
                .from(member)
                .leftJoin(member.team, team)
                .where(builder)
                .fetch();
    }
```

- **`hasText`** 로 `null` 과 빈 문자열을 함께 걸러줍니다.
- 조건들이 모두 누적된 후 마지막에 `.where(builder)` 로 한 번에 적용합니다.

### 3. WHERE절에 파라미터를 사용한 예제

`BooleanExpression` 메서드를 만들어 `where` 절에 콤마로 나열하는 방식입니다.

```java
public List<MemberTeamDto> search(MemberSearchCondition condition) {
        return queryFactory
                // @QueryProjection으로 생성자 주입으로 projection
                .select(new QMemberTeamDto(
                        member.id.as("memberId"),
                        member.username,
                        member.age,
                        team.id.as("teamId"),
                        team.name.as("teamName")))
                .from(member)
                .leftJoin(member.team, team)
                .where(
                // WHERE절 파라미터 방식으로 동적 쿼리 구현
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
```

- `where` 절의 `null` 은 자동으로 무시되므로 동적 쿼리를 깔끔하게 표현할 수 있습니다.
- 각 조건이 메서드로 분리되어 **재사용과 조합**이 자유롭다는 점이 큰 장점입니다.
