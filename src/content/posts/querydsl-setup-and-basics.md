---
author: "luca"
pubDatetime: 2023-06-17T16:35:37+09:00
title: "QueryDSL 설정법, 활용법 (검색조건쿼리, 기본 문법들)"
slug: "querydsl-setup-and-basics"
featured: false
draft: false
tags: ["querydsl", "jpa", "spring-data-jpa", "java"]
description: "Spring Boot 3.0 이상 환경의 QueryDSL 설정부터 검색 조건, 정렬, 페이징, 조인, 서브쿼리, Case 문까지 기본 문법을 한 번에 훑습니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## QueryDSL 설정방법 (Spring Boot 3.0 이상)

`build.gradle` 의 dependencies 에 다음을 추가합니다.

```gradle
// Querydsl 추가
implementation 'com.querydsl:querydsl-jpa:5.0.0:jakarta'
annotationProcessor "com.querydsl:querydsl-apt:${dependencyManagement.importedProperties['querydsl.version']}:jakarta"
annotationProcessor "jakarta.annotation:jakarta.annotation-api"
annotationProcessor "jakarta.persistence:jakarta.persistence-api"
```

> 참고: 이 설정으로 하면 IntelliJ 의 `build and run` 부분을 설정할 때 Q 클래스를 찾지 못하는 이슈가 있을 수 있습니다.

## QueryDSL 라이브러리

- **`com.querydsl:querydsl-apt`**: Q 클래스 생성 라이브러리
- **`com.querydsl:querydsl-jpa`**: QueryDSL 문법 제공 라이브러리
- **`p6spy-spring-boot-starter`**: 쿼리 파라미터 값 조회 라이브러리

## JPQL과 QueryDSL

### JPQL 예제

```java
@Test
void startJPQL() {
    Member findMember = em.createQuery(
        "SELECT m FROM Member m WHERE m.username = :username",
        Member.class)
        .setParameter("username", "member1")
        .getSingleResult();

    assertThat(findMember.getUsername()).isEqualTo("member1");
}
```

### QueryDSL 예제

```java
@Test
void startQuerydsl() {
    QMember m = new QMember("m");

    Member findMember = queryFactory
            .select(m)
            .from(m)
            .where(m.username.eq("member1")) // 파라미터 바인딩 처리
            .fetchOne();

    assertThat(findMember.getUsername()).isEqualTo("member1");
}
```

- **장점:** QueryDSL 은 컴파일 시점에 오류를 발견할 수 있으므로 JPQL 보다 안전합니다.

## Q-Type 활용방법

### 1. 별칭을 직접 지정하는 방법

```java
QMember qMember = new QMember("m");
```

### 2. 기본 인스턴스 사용

```java
QMember qMember = QMember.member;
```

### 3. Static Import 활용 (권장)

```java
import static study.querydsl.entity.QMember.*;

@Test
public void startQuerydsl3() {
    Member findMember = queryFactory
        .select(member)
        .from(member)
        .where(member.username.eq("member1"))
        .fetchOne();

    assertThat(findMember.getUsername()).isEqualTo("member1");
}
```

> 같은 테이블명이 없다면 static import 방법을 권장합니다.

## 검색 조건 쿼리

```java
member.username.eq("member1")           // username = 'member1'
member.username.ne("member1")           // username != 'member1'
member.username.eq("member1").not()     // username != 'member1'

member.useranme.isNotNull()             // 이름이 is not null

member.age.in(10, 20)                   // age in (10, 20)
member.age.notIn(10, 20)                // age not in (10, 20)
member.age.between(10, 30)              // between 10, 30

member.age.goe(30)                      // age >= 30
member.age.gt(30)                       // age > 30
member.age.loe(30)                      // age <= 30
member.age.lt(30)                       // age < 30

member.username.like("member%")         // like 검색
member.username.contains("member")      // like '%member%' 검색
member.username.startsWith("member")    // like 'member%' 검색
```

### AND 조건 - 체인 방식

```java
@Test
public void search() {
    Member findMember = queryFactory
            .selectFrom(member)
            .where(member.username.eq("member1")
                    .and(member.age.eq(10)))
            .fetchOne();

    assertThat(findMember.getUsername()).isEqualTo("member1");
}
```

### AND 조건 - 파라미터 방식 (권장)

```java
@Test
void searchParam() {
    Member findMember = queryFactory
        .selectFrom(member)
        .where(
            member.username.eq("member1"),
            member.age.eq(10))
        .fetchOne();

    assertThat(findMember.getUsername()).isEqualTo("member1");
}
```

> 파라미터 방식은 중간값이 `null` 이어도 무시하므로 동적 쿼리 작성에 유리합니다.

## 결과 조회

```java
// 리스트 조회
List<Member> fetch = queryFactory
    .selectFrom(member)
    .fetch();

// 단 건 조회
Member findMember1 = queryFactory
    .selectFrom(member)
    .fetchOne();

// 첫 번째 건 조회
Member findMember2 = queryFactory
    .selectFrom(member)
    .fetchFirst();

// 페이징 정보 포함
QueryResults<Member> results = queryFactory
    .selectFrom(member)
    .fetchResults();

// Count 쿼리
long count = queryFactory
    .selectFrom(member)
    .fetchCount();
```

| 메서드 | 설명 |
|--------|------|
| `fetch()` | 리스트 조회, 데이터 없으면 빈 리스트 |
| `fetchOne()` | 단 건 조회 (없으면 `null`, 2건 이상이면 예외) |
| `fetchFirst()` | `limit(1).fetchOne()` 과 동일 |
| `fetchResults()` | 페이징 정보 포함 (count 쿼리 추가 실행) |
| `fetchCount()` | count 쿼리로 변경해서 조회 |

## 정렬

```java
/**
 * 회원 정렬 순서
 * 1. 회원 나이 내림차순(desc)
 * 2. 회원 이름 올림차순(asc)
 * 단 2에서 회원 이름이 없으면 마지막에 출력(nulls last)
 */
@Test
public void sort() {
    em.persist(new Member(null, 100));
    em.persist(new Member("member5", 100));
    em.persist(new Member("member6", 100));

    List<Member> result = queryFactory
        .selectFrom(member)
        .where(member.age.eq(100))
        .orderBy(member.age.desc(), member.username.asc().nullsLast())
        .fetch();

    Member member5 = result.get(0);
    Member member6 = result.get(1);
    Member memberNull = result.get(2);

    assertThat(member5.getUsername()).isEqualTo("member5");
    assertThat(member6.getUsername()).isEqualTo("member6");
    assertThat(memberNull.getUsername()).isNull();
}
```

- `desc()`, `asc()`: 일반 정렬
- `nullsLast()`, `nullsFirst()`: `null` 데이터 순서 지정

## 페이징

### 조회 건수 제한

```java
@Test
public void paging1() {
    List<Member> result = queryFactory
        .selectFrom(member)
        .orderBy(member.username.desc())
        .offset(1)  // 0부터 시작(zero index)
        .limit(2)   // 최대 2건 조회
        .fetch();

    assertThat(result.size()).isEqualTo(2);
}
```

### 전체 조회 수 필요시

```java
@Test
public void paging2() {
    QueryResults<Member> queryResults = queryFactory
        .selectFrom(member)
        .orderBy(member.username.desc())
        .offset(1)
        .limit(2)
        .fetchResults();

    assertThat(queryResults.getTotal()).isEqualTo(4);
    assertThat(queryResults.getLimit()).isEqualTo(2);
    assertThat(queryResults.getOffset()).isEqualTo(1);
    assertThat(queryResults.getResults().size()).isEqualTo(2);
}
```

> **주의:** count 쿼리가 실행되므로 성능 주의가 필요합니다. 실무에서는 count 전용 쿼리를 별도로 작성하는 것이 좋습니다.

## 집합

### 집합 함수

```java
/**
 * JPQL
 * select
 *  COUNT(m),      // 회원 수
 *  SUM(m.age),    // 나이 합
 *  AVG(m.age),    // 평균 나이
 *  MAX(m.age),    // 최대 나이
 *  MIN(m.age)     // 최소 나이
 * from Member m
 */

@Test
public void aggregation() throws Exception {
    List<Tuple> result = queryFactory
        .select(member.count(),
                member.age.sum(),
                member.age.avg(),
                member.age.max(),
                member.age.min())
        .from(member)
        .fetch();

    Tuple tuple = result.get(0);
    assertThat(tuple.get(member.count())).isEqualTo(4);
    assertThat(tuple.get(member.age.sum())).isEqualTo(100);
    assertThat(tuple.get(member.age.avg())).isEqualTo(25);
    assertThat(tuple.get(member.age.max())).isEqualTo(40);
    assertThat(tuple.get(member.age.min())).isEqualTo(10);
}
```

### GroupBy

```java
/**
 * 팀의 이름과 각 팀의 평균 연령을 구해라.
 */
@Test
public void group() throws Exception {
    List<Tuple> result = queryFactory
        .select(team.name, member.age.avg())
        .from(member)
        .join(member.team, team)
        .groupBy(team.name)
        .fetch();

    Tuple teamA = result.get(0);
    Tuple teamB = result.get(1);

    assertThat(teamA.get(team.name)).isEqualTo("teamA");
    assertThat(teamA.get(member.age.avg())).isEqualTo(15);

    assertThat(teamB.get(team.name)).isEqualTo("teamB");
    assertThat(teamB.get(member.age.avg())).isEqualTo(35);
}
```

### groupBy() 와 having()

```java
.groupBy(item.price)
.having(item.price.gt(1000))
```

## 조인

### 기본 조인

**기본 문법:**

```java
join(조인 대상, 별칭으로 사용할 Q타입)
```

**예제:**

```java
/**
 * 팀A에 소속된 모든 회원
 */
@Test
public void join() throws Exception {
    QMember member = QMember.member;
    QTeam team = QTeam.team;

    List<Member> result = queryFactory
        .selectFrom(member)
        .join(member.team, team)
        .where(team.name.eq("teamA"))
        .fetch();

    assertThat(result)
        .extracting("username")
        .containsExactly("member1", "member2");
}
```

**조인 종류:**

- `join()`, `innerJoin()`: 내부 조인
- `leftJoin()`: left 외부 조인
- `rightJoin()`: right 외부 조인

### 세타 조인

연관관계가 없는 필드로 조인합니다.

```java
/**
 * 세타 조인(연관관계가 없는 필드로 조인)
 * 회원의 이름이 팀 이름과 같은 회원 조회
 */
@Test
public void theta_join() throws Exception {
    em.persist(new Member("teamA"));
    em.persist(new Member("teamB"));

    List<Member> result = queryFactory
        .select(member)
        .from(member, team)
        .where(member.username.eq(team.name))
        .fetch();

    assertThat(result)
        .extracting("username")
        .containsExactly("teamA", "teamB");
}
```

> 외부 조인은 `ON` 절을 사용하면 가능합니다.

### 조인 ON 절

#### 1. 조인 대상 필터링

```java
/**
 * 예) 회원과 팀을 조인하면서, 팀 이름이 teamA인 팀만 조인, 회원은 모두 조회
 * JPQL: SELECT m, t FROM Member m LEFT JOIN m.team t on t.name = 'teamA'
 * SQL: SELECT m.*, t.* FROM Member m LEFT JOIN Team t ON m.TEAM_ID=t.id
 *      and t.name='teamA'
 */
@Test
public void join_on_filtering() throws Exception {
    List<Tuple> result = queryFactory
        .select(member, team)
        .from(member)
        .leftJoin(member.team, team).on(team.name.eq("teamA"))
        .fetch();

    for (Tuple tuple : result) {
        System.out.println("tuple = " + tuple);
    }
}
```

> 내부 조인에서는 `WHERE` 절과 기능이 동일하므로, 외부 조인이 필요할 때만 `ON` 절을 사용합니다.

#### 2. 연관관계 없는 엔티티 외부 조인

```java
/**
 * 회원의 이름과 팀의 이름이 같은 대상 외부 조인
 * JPQL: SELECT m, t FROM Member m LEFT JOIN Team t on m.username = t.name
 * SQL: SELECT m.*, t.* FROM Member m LEFT JOIN Team t ON m.username = t.name
 */
@Test
public void join_on_no_relation() throws Exception {
    em.persist(new Member("teamA"));
    em.persist(new Member("teamB"));

    List<Tuple> result = queryFactory
        .select(member, team)
        .from(member)
        .leftJoin(team).on(member.username.eq(team.name))
        .fetch();

    for (Tuple tuple : result) {
        System.out.println("t=" + tuple);
    }
}
```

> 일반 조인은 `leftJoin(member.team, team)`, ON 조인은 `from(member).leftJoin(team).on(xxx)` 형태입니다.

### 페치 조인

페치 조인은 SQL 조인을 활용해 연관된 엔티티를 한 번의 쿼리로 조회합니다. 성능 최적화에 주로 사용됩니다.

#### 페치 조인 미적용

```java
@PersistenceUnit
EntityManagerFactory emf;

@Test
public void fetchJoinNo() throws Exception {
    em.flush();
    em.clear();

    Member findMember = queryFactory
        .selectFrom(member)
        .where(member.username.eq("member1"))
        .fetchOne();

    boolean loaded = emf.getPersistenceUnitUtil().isLoaded(findMember.getTeam());

    assertThat(loaded).as("페치 조인 미적용").isFalse();
}
```

#### 페치 조인 적용

```java
@Test
public void fetchJoinUse() throws Exception {
    em.flush();
    em.clear();

    Member findMember = queryFactory
        .selectFrom(member)
        .join(member.team, team).fetchJoin()
        .where(member.username.eq("member1"))
        .fetchOne();

    boolean loaded = emf.getPersistenceUnitUtil().isLoaded(findMember.getTeam());

    assertThat(loaded).as("페치 조인 적용").isTrue();
}
```

> 조인 뒤에 `.fetchJoin()` 을 추가하면 됩니다.

## 서브쿼리

`com.querydsl.jpa.JPAExpressions` 를 사용합니다.

### 서브쿼리 - eq 사용

```java
/**
 * 나이가 가장 많은 회원 조회
 */
@Test
public void subQuery() throws Exception {
    QMember memberSub = new QMember("memberSub");

    List<Member> result = queryFactory
        .selectFrom(member)
        .where(member.age.eq(
            JPAExpressions
                .select(memberSub.age.max())
                .from(memberSub)
        )).fetch();

    assertThat(result).extracting("age").containsExactly(40);
}
```

### 서브쿼리 - goe 사용

```java
/**
 * 나이가 평균 나이 이상인 회원
 */
@Test
public void subQuery() throws Exception {
    QMember memberSub = new QMember("memberSub");

    List<Member> result = queryFactory
        .selectFrom(member)
        .where(member.age.goe(
            JPAExpressions
                .select(memberSub.age.avg())
                .from(memberSub)
        )).fetch();

    assertThat(result).extracting("age").containsExactly(30, 40);
}
```

### 서브쿼리 - 여러 건 처리 (in 사용)

```java
/**
 * 서브쿼리 여러 건 처리, in 사용
 */
@Test
public void subQuery() throws Exception {
    QMember memberSub = new QMember("memberSub");

    List<Member> result = queryFactory
        .selectFrom(member)
        .where(member.age.in(
            JPAExpressions
                .select(memberSub.age)
                .from(memberSub)
                .where(memberSub.age.gt(10))
        )).fetch();

    assertThat(result).extracting("age").containsExactly(20, 30, 40);
}
```

### select 절에 서브쿼리

```java
@Test
public void subQuery() throws Exception {
    QMember memberSub = new QMember("memberSub");

    List<Member> result = queryFactory
        .select(member.username,
                JPAExpressions
                    .select(memberSub.age.avg())
                    .from(memberSub)
        ).from(member)
        .fetch();
}
```

### Static Import 활용

```java
import static com.querydsl.jpa.JPAExpressions.select;

List<Member> result = queryFactory
    .selectFrom(member)
    .where(member.age.eq(
        select(memberSub.age.max())
            .from(memberSub)
    )).fetch();
```

## Case 문

`SELECT`, `WHERE`, `ORDER BY` 절에서 사용 가능합니다.

### 단순한 조건

```java
List<String> result = queryFactory
    .select(member.age
        .when(10).then("열살")
        .when(20).then("스무살")
        .otherwise("기타"))
    .from(member)
    .fetch();
```

### 복잡한 조건

```java
List<String> result = queryFactory
    .select(new CaseBuilder()
        .when(member.age.between(0, 20)).then("0~20살")
        .when(member.age.between(21, 30)).then("21~30살")
        .otherwise("기타"))
    .from(member)
    .fetch();
```

### orderBy 에서 Case 문 함께 사용하기

```java
/**
 * 임의의 순서로 회원을 출력하고 싶은 상황
 * 1. 0 ~ 30살이 아닌 회원을 가장 먼저 출력
 * 2. 0 ~ 20살 회원 출력
 * 3. 21 ~ 30살 회원 출력
 */
NumberExpression<Integer> rankPath = new CaseBuilder()
    .when(member.age.between(0, 20)).then(2)
    .when(member.age.between(21, 30)).then(1)
    .otherwise(3);

List<Tuple> result = queryFactory
    .select(member.username, member.age, rankPath)
    .from(member)
    .orderBy(rankPath.desc())
    .fetch();

for (Tuple tuple : result) {
    String username = tuple.get(member.username);
    Integer age = tuple.get(member.age);
    Integer rank = tuple.get(rankPath);
    System.out.println("username = " + username + " age = " + age + " rank = " + rank);
}
```

> QueryDSL 은 자바 코드이므로 복잡한 조건을 변수로 선언해 재사용할 수 있습니다.

## 상수, 문자 더하기

### 상수

```java
Tuple result = queryFactory
    .select(member.username, Expressions.constant("A"))
    .from(member)
    .fetchFirst();
```

### 문자 더하기 (concat)

```java
String result = queryFactory
    .select(member.username.concat("_").concat(member.age.stringValue()))
    .from(member)
    .where(member.username.eq("member1"))
    .fetchOne();
```

> `member.age.stringValue()` 로 문자가 아닌 타입을 문자로 변환할 수 있습니다. 이 방법은 ENUM 처리에도 자주 사용됩니다.

## 다음 포스트

프로젝션과 결과 반환, 동적 쿼리, 벌크 쿼리.
