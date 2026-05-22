---
author: "luca"
pubDatetime: 2023-06-15T20:53:39+09:00
title: "객체지향 쿼리 언어 (JPQL)"
slug: "jpql-introduction"
featured: false
draft: false
tags: ["jpa", "jpql", "orm"]
description: "JPA 가 지원하는 쿼리 방법들과 JPQL 의 문법 — 프로젝션, 페이징, 조인, 서브쿼리, 기본 함수까지 — 를 한 번에 훑습니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## JPA가 지원하는 다양한 쿼리 방법

- **JPQL**
- JPA Criteria
- **QueryDSL**
- SQL
- `JDBC API` 직접 사용, `MyBatis`, `SpringJdbcTemplate` 와 함께 사용

## JPQL 소개

- 가장 단순한 조회 방법
  - `EntityManager.find()`
  - 객체 그래프 탐색 (`a.getB().getC()`)
- **나이가 18살 이상인 회원을 모두 검색하고 싶다면?**

## JPQL이 필요한 이유

- `JPA` 를 사용하면 엔티티 객체를 중심으로 개발하게 됩니다.
- 검색을 할 때도 **테이블이 아닌 엔티티 객체를 대상으로 검색합니다**.
- 모든 DB 데이터를 객체로 변환해서 검색하는 것은 사실상 불가능합니다.
- 정확하게 필요한 데이터만 DB 에서 불러오려면 결국 검색 조건이 포함된 `SQL` 이 필요합니다.

## JPQL이란

- `JPA` 는 `SQL` 을 추상화한 `JPQL` 이라는 객체 지향 쿼리 언어를 제공합니다.
- `SQL` 과 문법이 유사하며, `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `JOIN` 을 지원합니다.
- `JPQL` 은 엔티티 객체를 대상으로 쿼리를 만듭니다.
- 테이블이 아닌 객체를 대상으로 검색하는 객체 지향 쿼리이고, 추상화해서 특정 데이터베이스 `SQL` 에 의존하지 않습니다.

```java
String jpql = "SELECT m FROM Member m WHERE m.name LIKE '%hello%'";

List<Member> result = em.createQuery(jpql, Member.class).getResultList();
```

## QueryDSL 소개

- 문자가 아닌 자바 코드로 `JPQL` 을 작성할 수 있도록 해줍니다.
- `JPQL` 빌더 역할입니다.
- **컴파일 시점에 문법 오류를 찾을 수 있다는 강력한 장점이 있습니다.**
- 동적 쿼리 작성이 편리합니다.
- **단순하고 쉽습니다 (실무에서 사용하는 것을 권장합니다).**

```java
// JPQL
// SELECT m FROM Member m WHERE m.age > 18
JPAFactoryQuery query = new JPAQueryFactory(em);
QMember m = QMember.member;

List<Member> list =
	query.selectFrom(m)
        	 .where(m.age.gt(18))
             .orderBy(m.name.desc())
             .fetch();
```

## JDBC 직접 사용, SpringJdbcTemplate 등

- `JPA` 를 사용하면서 `JDBC` 커넥션을 직접 사용하거나, 스프링 `JdbcTemplate`, `MyBatis` 등을 함께 사용 가능합니다.
- 단, 영속성 컨텍스트를 적절한 시점에 강제로 플러시해야 합니다.

## JPQL 문법

- `SELECT m FROM Member AS m WHERE m.age > 18`
- 엔티티와 속성은 대소문자를 구분합니다 (`Member`, `age`).
- `JPQL` 키워드는 대소문자 구분 없이 사용합니다 (`SELECT`, `FROM`, `where`).
- 엔티티 이름을 사용하며, 테이블 이름이 아닙니다 (`Member`).
- 별칭은 필수입니다 (`m`). `as` 는 생략 가능합니다.

### 집합과 정렬

- `GROUP BY`, `HAVING`
- `ORDER BY`

### TypeQuery, Query

- **`TypeQuery`**: 반환 타입이 명확할 때 사용합니다.
- **`Query`**: 반환 타입이 명확하지 않을 때 사용합니다.

```java
TypeQuery<Member> query
	em.createQuery("SELECT m FROM Member m", Member.class);

Query query =
	em.createQuery("SELECT m.username, m.age from Member m");
```

### 결과 조회 API

- **`query.getResultList()`**: 결과가 하나 이상일 때 리스트를 반환합니다.
  - 결과가 없으면 빈 리스트를 반환합니다.
- **`query.getSingleResult()`**: 결과가 정확히 하나일 때 단일 객체를 반환합니다.
  - 결과가 없으면: `javax.persistence.NoResultException`
  - 둘 이상이면: `javax.persistence.NonUniqueResultException`

### 파라미터 바인딩 - 이름 기준, 위치 기준

- 이름 기준

  ```
  SELECT m FROM Member m WHERE m.username = :username

  query.setParameter("username", usernameParam);
  ```

- 위치 기준 (위치 기준은 웬만하면 지양하도록 합니다)

  ```
  SELECT m FROM Member m WHERE m.username = ?1

  query.setParameter(1, usernameParam);
  ```

### 프로젝션

- **`SELECT` 절에 조회할 대상을 지정하는 것**입니다.
- 프로젝션 대상: 엔티티, 임베디드 타입, 스칼라 타입 (숫자, 문자 등 기본 데이터 타입).
- `SELECT m FROM Member m` → 엔티티 프로젝션
- `SELECT m.team FROM Member m` → 엔티티 프로젝션
- `SELECT m.address FROM Member m` → 임베디드 타입 프로젝션
- `SELECT m.username, m.age FROM Member m` → 스칼라 타입 프로젝션
- `DISTINCT` 로 중복을 제거합니다.

### 프로젝션 - 여러 값 조회

- 여러 타입을 한 번에 조회할 경우에는?
- `SELECT m.username, m.age FROM Member m`

1. `Query` 타입으로 조회
2. `Object[]` 타입으로 조회
3. `new` 명령어로 조회

- 단순 값을 `DTO` 로 바로 조회

  ```
  SELECT new jpabook.jpql.UserDTO(m.username, m.age) FROM Member m
  ```

- 패키지 명을 포함한 전체 클래스 명을 입력합니다.
- 순서와 타입이 일치하는 생성자가 필요합니다.

### 페이징 API

- `JPA` 는 페이징을 다음 두 `API` 로 추상화합니다.
- **`setFirstResult(int startPosition)`**: 조회 시작 위치 (0부터 시작).
- **`setMaxResults(int maxResult)`**: 조회할 데이터 수.

```java
// 페이징 쿼리
String jpql = "SELECT m FROM Member m ORDER BY m.name DESC";
List<Member> resultList = em.createQuery(jpql, Member.class)
								.setFirstResult(10)
                                    .setMaxResults(20)
                                    .getResultList();
```

### 조인

- 내부 조인 (Inner Join): `SELECT m FROM Member m [INNER] JOIN m.team t`
- 외부 조인 (Outer Join): `SELECT m FROM Member m LEFT [OUTER] JOIN m.team t`
- 세타 조인: `SELECT COUNT(m) FROM Member m, Team t WHERE m.username = t.name`

#### 조인 - ON 절

- `ON` 절을 활용한 조인 (JPA 2.1 부터 지원)
  1. 조인 대상 필터링
  2. 연관관계 없는 엔티티 외부 조인 (하이버네이트 5.1 부터)

#### 조인 대상 필터링

- 예) 회원과 팀을 조인하면서, 팀 이름이 A 인 팀만 조인하기.
- **JPQL**

  ```
  SELECT m, t FROM Member m LEFT JOIN m.team t ON t.name = 'A
  ```

- **SQL**

  ```
  SELECT m.*, t.* FROM Member m LEFT JOIN Team t ON m.TEAM_ID = t.id and t.name = 'A
  ```

### 서브 쿼리

- **보통 메인 쿼리와 서브쿼리가 아무런 상관이 없어야 성능이 잘 나옵니다.**
- 나이가 평균보다 많은 회원

  ```
  SELECT m FROM Member m
  WHERE m.age > (SELECT AVG(m2.age) FROM Member m2)
  ```

- 한 건이라도 주문한 고객

  ```
  SELECt m FROM Member m
  WHERE (SELECT COUNT(o) FROM Order o WHERE m = o.member) > 0
  ```

#### 서브 쿼리 지원 함수

- `[NOT] EXISTS (subquery)`: 서브 쿼리에 결과가 존재하면 참
  - `{ALL | ANY | SOME} (subquery)`
  - **`ALL`**: 모두 만족하면 참
  - **`ANY`, `SOME`**: 같은 의미, 조건을 하나라도 만족하면 참

#### 서브 쿼리 - 예제

- 팀 A 소속인 회원

  ```
  SELECT m FROM Member m
  WHERE EXISTS (SELECT t FROM m.team t WHERE t.name = 'A')
  ```

- 전체 상품 각각의 재고보다 주문량이 많은 주문들

  ```
  SELECT o FROM Order o
  WHERE o.orderAmount > ALL (SELECT p.stockAmount FROM Product p)
  ```

- 어떤 팀이든 팀에 소속된 회원

  ```
  SELECT m FROM Member m
  WHERE m.team = ANY (SELECT t FROM Team t)
  ```

### JPQL 타입 표현

- **문자**: `'HELLO'`, `'She''s'`
- **숫자**: `10L` (Long), `10D` (Double), `10F` (Float)
- **Boolean**: `TRUE`, `FALSE`
- **ENUM**: `jpabook.MemberType.Admin` (패키지명 포함)
- **엔티티 타입**: `TYPE(m) = Member` (상속 관계에서 사용)

### JPQL 기본 함수

- **`CONCAT`**: 문자를 더하는 함수
- **`SUBSTRING`**: 문자열을 부분 잘라내는 함수
- **`TRIM`**: 공백을 제거하는 함수
- **`LOWER`, `UPPER`**: 대소문자 변환하는 함수
- **`LENGTH`**: 길이
- **`LOCATE`**: 문자열에서 특정 문자의 위치 반환 함수
- **`ABS`, `SQRT`, `MOD`**: 수학 함수
- **`SIZE`, `INDEX`**: `JPA` 용도
