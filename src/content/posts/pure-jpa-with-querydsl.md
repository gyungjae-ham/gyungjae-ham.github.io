---
author: "luca"
pubDatetime: 2023-06-18T16:13:16+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "순수 JPA와 QueryDSL"
slug: "pure-jpa-with-querydsl"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "java", "dynamic-query"]
description: "순수 JPA 리포지토리에 QueryDSL 을 얹어 동적 쿼리를 만드는 두 가지 방식 — Builder 와 WHERE 다중 파라미터 — 을 정리합니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

이 예제는 QueryDSL 5.x에서 Member·Team 엔티티와 생성된 `QMember.member`, `QTeam.team`을 사용합니다. DTO는 `(Long memberId, String username, int age, Long teamId, String teamName)` 생성자에 `@QueryProjection`을 붙여 `QMemberTeamDto`를 생성한 전제입니다. imports와 엔티티 정의는 생략했습니다. 쓰기 메서드는 호출하는 서비스의 트랜잭션 안에서 실행해야 합니다.

## 직접 만든 리포지토리에 QueryDSL 붙이기

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

예를 들어 팀 A의 20세 회원과 팀 B의 30세 회원이 있을 때 `teamName=A, ageGoe=20`은 첫 회원만 고릅니다. 두 구현은 이 조건에서 같은 결과를 내야 합니다. 조건이 모두 비어 있으면 WHERE 제한 없이 전체를 조회합니다. 목록 API에서는 이를 허용할지 정하고, 최대 개수와 페이징도 별도로 적용해야 합니다. 하한 나이가 상한보다 큰 요청은 입력 단계에서 거절하는 식으로 정책을 명확히 할 수 있습니다.

조건 조합 문법은 [동적 쿼리 노트](/posts/querydsl-projection-dynamic-bulk/), 실제 페이지 반환은 [Spring Data와 QueryDSL 페이징](/posts/spring-data-jpa-querydsl-paging/)으로 이어집니다.
