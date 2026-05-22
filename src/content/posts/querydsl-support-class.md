---
author: "luca"
pubDatetime: 2023-06-18T18:19:12+09:00
title: "QueryDSL 지원 클래스 만들기"
slug: "querydsl-support-class"
featured: false
draft: false
tags: ["querydsl", "jpa", "spring-data-jpa", "java"]
description: "QuerydslRepositorySupport 의 한계를 짚고, 페이징·정렬까지 깔끔하게 처리하는 커스텀 추상 클래스를 직접 구현해봅니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 사용하는 이유

스프링 데이터 JPA 가 제공하는 `QuerydslRepositorySupport` 는 편리하지만 몇 가지 한계가 있습니다.

- 메소드 체인이 풀리는 문제와 `FROM` 절로 시작해야 하는 가독성 문제가 있습니다.
- **`sort` 기능이 완전하지 않다는 치명적인 단점**이 존재합니다.
- 따라서 커스텀 추상 클래스를 직접 구현하여 코드량을 줄이고자 합니다.

## QueryDSL 을 지원하는 추상 클래스 생성하기

QueryDSL 4.x 버전에 맞춘 지원 라이브러리입니다. 스프링 데이터 JPA 의 `QuerydslRepositorySupport` 를 참고하여 작성합니다.

```java
/**
 * Querydsl 4.x 버전에 맞춘 Querydsl 지원 라이브러리
 * @see org.springframework.data.jpa.repository.support.QuerydslRepositorySupport
 */
@Repository
public abstract class Querydsl4RepositorySupport {
    private final Class domainClass;
    private Querydsl querydsl;
    private EntityManager entityManager;
    private JPAQueryFactory queryFactory;

    public Querydsl4RepositorySupport(Class<?> domainClass) {
        Assert.notNull(domainClass, "Domain class must not be null!");
        this.domainClass = domainClass;
    }

    @Autowired
    public void setEntityManager(EntityManager entityManager) {
        Assert.notNull(entityManager, "EntityManager must not be null!");
        JpaEntityInformation entityInformation = JpaEntityInformationSupport.getEntityInformation(domainClass, entityManager);
        SimpleEntityPathResolver resolver = SimpleEntityPathResolver.INSTANCE;
        EntityPath path = resolver.createPath(entityInformation.getJavaType());
        this.entityManager = entityManager;
        this.querydsl = new Querydsl(entityManager, new PathBuilder<>(path.getType(), path.getMetadata()));
        this.queryFactory = new JPAQueryFactory(entityManager);
    }

    @PostConstruct
    public void validate() {
        Assert.notNull(entityManager, "EntityManager must not be null!");
        Assert.notNull(querydsl, "Querydsl must not be null!");
        Assert.notNull(queryFactory, "QueryFactory must not be null!");
    }

    protected JPAQueryFactory getQueryFactory() {
        return queryFactory;
    }

    protected Querydsl getQuerydsl() {
        return querydsl;
    }

    protected EntityManager getEntityManager() {
        return entityManager;
    }

    protected <T> JPAQuery<T> select(Expression<T> expr) {
        return getQueryFactory().select(expr);
    }

    protected <T> JPAQuery<T> selectFrom(EntityPath<T> from) {
        return getQueryFactory().selectFrom(from);
    }

    protected <T> Page<T> applyPagination(Pageable pageable, Function<JPAQueryFactory, JPAQuery> contentQuery) {
        JPAQuery jpaQuery = contentQuery.apply(getQueryFactory());
        List<T> content = getQuerydsl().applyPagination(pageable, jpaQuery).fetch();
        return PageableExecutionUtils.getPage(content, pageable, jpaQuery::fetchCount);
    }

    protected <T> Page<T> applyPagination(Pageable pageable, Function<JPAQueryFactory, JPAQuery> contentQuery, Function<JPAQueryFactory, JPAQuery> countQuery) {
        JPAQuery jpaContentQuery = contentQuery.apply(getQueryFactory());
        List<T> content = getQuerydsl().applyPagination(pageable, jpaContentQuery).fetch();
        JPAQuery countResult = countQuery.apply(getQueryFactory());
        return PageableExecutionUtils.getPage(content, pageable, countResult::fetchCount);
    }
}
```

- **`select` / `selectFrom`** 을 protected 메서드로 노출하여 `JPAQueryFactory` 를 매번 꺼낼 필요가 없도록 합니다.
- **`applyPagination`** 은 페이징 처리를 내부적으로 처리해주는 메소드입니다. 카운트 쿼리를 분리하는 오버로드도 함께 제공합니다.

## 지원 추상 클래스를 상속받은 레포지토리 예제

실제로 추상 클래스를 상속받아 사용하는 모습입니다.

```java
@Repository
public class MemberTestRepository extends Querydsl4RepositorySupport {
    // 생성자에 타겟 엔티티를 넣어줍니다
    public MemberTestRepository() {
        super(Member.class);
    }

    public List<Member> basicSelect() {
        // QueryFactory 생성 없이 바로 작성할 수 있게 됩니다
        return select(member)
                .from(member)
                .fetch();
    }

    public List<Member> basicSelectFrom() {
        // QueryFactory 생성 없이 바로 작성할 수 있게 됩니다
        return selectFrom(member)
                .fetch();
    }

    public Page<Member> searchPageByApplyPage(MemberSearchCondition condition, Pageable pageable) {
        JPAQuery<Member> query = selectFrom(member)
                .leftJoin(member.team, team)
                .where(usernameEq(condition.getUsername()),
                        teamNameEq(condition.getTeamName()),
                        ageGoe(condition.getAgeGoe()),
                        ageLoe(condition.getAgeLoe()));

        // 페이징 처리를 해주는 부분입니다(offset, limit) 처리를 알아서 처리해줍니다
        List<Member> content = getQuerydsl().applyPagination(pageable, query)
                .fetch();
        return PageableExecutionUtils.getPage(content, pageable, query::fetchCount);
    }

    // searchPageByApplyPage와 동일한 기능을 합니다
    // getQuerydsl().applyPagination 부분을 내부적으로 처리하고 있는 메소드를 사용했습니다
    public Page<Member> applyPagination(MemberSearchCondition condition, Pageable pageable) {
        return applyPagination(pageable, contentQuery -> contentQuery
                .selectFrom(member)
                .leftJoin(member.team, team)
                .where(usernameEq(condition.getUsername()),
                        teamNameEq(condition.getTeamName()),
                        ageGoe(condition.getAgeGoe()),
                        ageLoe(condition.getAgeLoe())));
    }

    // 앞 선 학습에서 나왔던 searchComplex에서 조회하는 쿼리와 카운트 쿼리를 분리했었습니다
    // 위 예제의 두 쿼리를 하나의 메서드로 합쳐서 구현한 부분입니다(람다식으로 구현)
    public Page<Member> applyPagination2(MemberSearchCondition condition, Pageable pageable) {
        return applyPagination(pageable, contentQuery -> contentQuery
                        .selectFrom(member)
                        .leftJoin(member.team, team)
                        .where(usernameEq(condition.getUsername()),
                                teamNameEq(condition.getTeamName()),
                                ageGoe(condition.getAgeGoe()),
                                ageLoe(condition.getAgeLoe())),
                countQuery -> countQuery
                        .selectFrom(member)
                        .leftJoin(member.team, team)
                        .where(usernameEq(condition.getUsername()),
                                teamNameEq(condition.getTeamName()),
                                ageGoe(condition.getAgeGoe()),
                                ageLoe(condition.getAgeLoe()))
        );
    }

    // 아래 메서드들은 동적 쿼리를 WHERE절의 다중 파라미터로 해결하기 위한 메서드 구현입니다
    private BooleanExpression usernameEq(String username) {
        return isEmpty(username) ? null : member.username.eq(username);
    }

    private BooleanExpression teamNameEq(String teamName) {
        return isEmpty(teamName) ? null : team.name.eq(teamName);
    }

    private BooleanExpression ageGoe(Integer ageGoe) {
        return ageGoe == null ? null : member.age.goe(ageGoe);
    }

    private BooleanExpression ageLoe(Integer ageLoe) {
        return ageLoe == null ? null : member.age.loe(ageLoe);
    }
}
```

- **`basicSelect` / `basicSelectFrom`** 처럼 `QueryFactory` 생성 없이 바로 작성할 수 있게 됩니다.
- **`searchPageByApplyPage`** 는 `getQuerydsl().applyPagination` 을 직접 호출하여 `offset`, `limit` 을 자동 처리합니다.
- **`applyPagination`** 은 동일한 기능을 더 간결한 람다식으로 표현한 모습입니다.
- **`applyPagination2`** 는 조회 쿼리와 카운트 쿼리를 분리하여 카운트 쿼리를 최적화할 수 있도록 두 람다를 받는 형태입니다.
