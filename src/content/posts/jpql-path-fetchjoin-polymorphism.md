---
author: "luca"
pubDatetime: 2023-06-15T23:38:05+09:00
title: "경로표현식, Fetch Join, 다형성 쿼리"
slug: "jpql-path-fetchjoin-polymorphism"
featured: false
draft: false
tags: ["jpa", "jpql", "fetch-join", "n+1"]
description: "JPQL 의 경로 표현식, 묵시적·명시적 조인, Fetch Join 의 한계, 다형성 쿼리와 벌크 연산 주의점까지 정리합니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 경로 표현식

점을 찍어 객체 그래프를 탐색하는 것을 말합니다.

```
SELECT m.username -> 상태 필드
	FROM Member m
    JOIN m.team t -> 단일 값 연관 필드
    JOIN m.orders o -> 컬렉션 값 연관 필드
WHERE t.name = '팀A'
```

### 경로 표현식 용어 정리

- **상태 필드**: 단순히 값을 저장하기 위한 필드
- **연관 필드**: 연관관계를 위한 필드
  - **단일 값 연관 필드**: `@ManyToOne`, `@OneToOne`, 대상이 엔티티
  - **컬렉션 값 연관 필드**: `@OneToMany`, `@ManyToMany`, 대상이 컬렉션

### 단일 값 연관 경로 탐색

- **JPQL**: `SELECT o.member FROM Order o`
- **SQL**: `SELECT m.* FROM Orders o Inner JOIN Member m on o.member_id = m.id`

### 명시적 조인, 묵시적 조인

- **명시적 조인**: `JOIN` 키워드 직접 사용
  - `SELECT m FROM Member m JOIN m.team t`
- **묵시적 조인**: 경로 표현식에 의해 묵시적으로 SQL 조인 발생 (내부 조인만 가능)
  - `SELECT m.team FROM Member m`

### 경로 탐색을 사용한 묵시적 조인 시 주의사항

- 항상 내부 조인입니다.
- 컬렉션은 경로 탐색의 끝이며, 명시적 조인을 통해 별칭을 얻어야 합니다.
- 경로 탐색은 주로 `SELECT`, `WHERE` 절에서 사용하지만 묵시적 조인으로 인해 SQL 의 `FROM` (JOIN) 절에 영향을 줍니다.
- **가급적이면 묵시적 조인 대신에 명시적 조인을 사용하도록 합니다.**
- 조인은 SQL 튜닝에 중요한 포인트입니다.
- 묵시적 조인은 조인이 일어나는 상황을 한눈에 파악하기가 어려우므로 명시적으로 사용합니다.

## Fetch Join

- **실무에서 자주 쓰는 핵심 기능입니다.**
- SQL 조인의 종류가 아닙니다.
- JPQL 에서 **성능 최적화**를 위해서 제공하는 기능입니다.
- 연관된 엔티티나 컬렉션을 **SQL 한 번에 함께 조회**하는 기능입니다.
- `JOIN FETCH` 명령어를 사용합니다.
- `[LEFT | INNER] JOIN FETCH 조인경로` 형태입니다.

### 엔티티 페치 조인

회원을 조회하면서 연관된 팀도 함께 조회합니다 (SQL 한 번).

- **[JPQL]**

  ```
  SELECT m FROM Member m JOIN FETCH m.team
  ```

- **[SQL]**

  ```
  SELECT M.*, T.* FROM Member m INNER JOIN Team t ON m.TEAM_ID = t.id
  ```

### 컬렉션 페치 조인

일대다 관계, 컬렉션 페치 조인. 똑같은 결과가 컬렉션의 크기만큼 반복되어 출력됩니다.

- **[JPQL]**

  ```
  SELECT t
  FROM Team t JOIN FETCH t.members
  WHERE t.name = '팀A'
  ```

- **[SQL]**

  ```
  SELECT t.*, m.*
  FROM Team t
  INNNER JOIN Member m ON T.id = m.TEAM_ID
  WHERE t.name = '팀A'
  ```

### 페치 조인과 DISTINCT

- SQL 의 `DISTINCT` 는 중복된 결과를 제거하는 명령입니다.
- JPQL 의 `DISTINCT` 는 2가지 기능을 제공합니다.
  1. SQL 에 `DISTINCT` 를 추가합니다.
  2. 어플리케이션에서 엔티티 중복을 제거합니다 (**컬렉션 페치 조인의 중복 데이터를 해결합니다**).
  - **하이버네이트 6 부터는 `DISTINCT` 명령어를 사용하지 않아도 어플리케이션에서 중복 제거가 자동으로 적용됩니다.**

```
SELECT DISTINCT t
FROM Team t JOIN FETCH t.members
WHERE t.name = '팀A'
```

### 페치 조인과 일반 조인의 차이

- 페치 조인을 사용할 때만 연관된 엔티티도 함께 **조회(즉시 로딩)** 합니다.
- **페치 조인은 객체 그래프를 SQL 한 번에 조회하는 개념입니다.**

### 페치 조인의 특징과 한계

- **페치 조인 대상에는 별칭을 줄 수 없습니다.**
  - 하이버네이트에서는 가능하지만, 가급적 사용하지 않도록 합니다.
- **둘 이상의 컬렉션은 페치 조인할 수 없습니다.**
- **컬렉션을 페치 조인하면 페이징 API (`setFirstResult`, `setMaxResult`) 를 사용할 수 없습니다.**
  - 일대일, 다대일 같은 단일 값 연관 필드들은 페치 조인해도 페이징이 가능합니다.
  - 하이버네이트는 경고 로그를 남기고 메모리에서 페이징해 줍니다 (매우 위험).
- 연관된 엔티티들은 SQL 한 번으로 조회 가능합니다 — **성능 최적화**.
- 엔티티에 직접 적용하는 글로벌 로딩 전략보다 우선합니다.
  - `@OneToMany(fetch = FetchType.LAZY)`
- **실무에서 글로벌 로딩 전략은 모두 지연 로딩으로 해 둡니다.**
- 성능 최적화가 필요한 곳은 모두 페치 조인을 적용하도록 합니다.

### 페치 조인 정리

- 모든 것을 페치 조인으로 해결할 수는 없습니다.
- 페치 조인은 객체 그래프를 유지할 때 사용하면 효과적입니다.
- 여러 테이블을 조인해서 엔티티가 가진 모양이 아닌 전혀 다른 결과를 내야 하면, 페치 조인보다는 일반 조인을 사용하고 필요한 데이터들만 조회해서 DTO 로 반환하는 것이 효과적입니다.

## 다형성 쿼리

### TYPE

조회 대상을 특정 자식으로 한정합니다. (예: `Item` 중에 `Book`, `Movie` 를 조회)

- **[JPQL]**

  ```
  SELECT i FROM Item i
  WHERE type(i) IN (Book, Movie)
  ```

- **[SQL]**

  ```
  SELECT i FROM Item i
  WHERE i.DTYPE in ('B', 'M')
  ```

### TREAT

자바의 타입 캐스팅과 유사합니다. 상속 구조에서 부모 타입을 특정 자식 타입으로 다룰 때 사용합니다.

- `FROM`, `WHERE`, `SELECT` (하이버네이트 지원) 에서 사용합니다.
- 예: 부모인 `Item` 과 자식 `Book`.
- **[JPQL]**

  ```
  SELECT i FROM Item i
  WHERE TREAT(i as Book).author = 'kim'
  ```

- **[SQL]**

  ```
  SELECT i.* FROM Item i
  WHERE i.DTYPE = 'B' and i.author = 'kim'
  ```

## 엔티티 직접 사용

JPQL 에서 엔티티를 직접 사용하면 SQL 에서 해당 엔티티의 기본 키 값을 사용합니다.

- **[JPQL]**

  ```
  SELECT COUNT(m.id) FROM Member m //엔티티의 아이디를 사용
  SELECT COUNT(m) FROM Member m //엔티티를 직접 사용
  ```

- **[SQL] (JPQL 둘 다 같은 다음 SQL 실행)**

  ```
  SELECT COUNT(m.id) AS cnt FROM Member m
  ```

## Named 쿼리

- 미리 정의해서 이름을 부여해두고 사용하는 JPQL 입니다.
- 정적 쿼리입니다.
- 어노테이션, XML 에 정의합니다.
- 어플리케이션 로딩 시점에 초기화 후 재사용합니다.
- **어플리케이션 로딩 시점에 쿼리를 검증**합니다.

### Named 쿼리 환경에 따른 설정

- XML 이 항상 우선권을 가집니다.
- 어플리케이션 운영 환경에 따라 다른 XML 을 배포할 수 있습니다.

## 벌크 연산

재고가 10개 미만은 모든 상품의 가격을 10% 상승하려면 어떻게 해야 할까요?

JPA 변경 감지 기능으로 실행하려면 너무 많은 쿼리가 실행됩니다.

1. 재고가 10개 미만인 상품을 리스트로 조회합니다.
2. 상품 엔티티의 가격을 10% 증가합니다.
3. 트랜잭션 커밋 시점에 변경 감지가 동작합니다.

변경된 데이터가 100건이라면 100번의 UPDATE SQL 이 실행됩니다.

### 벌크 연산 예제

쿼리 한 번으로 여러 테이블 로우를 변경합니다 (엔티티).

- **`executeUpdate()`** 의 결과는 영향받은 엔티티 수를 반환합니다.
- **UPDATE, DELETE** 를 지원합니다.
- **INSERT** (INSERT INTO .. SELECT, 하이버네이트 지원) 도 가능합니다.

```java
String qlString = "UPDATE Product p " +
				  "SET p.price = p.price * 1.1 " +
                  "WHERE p.stockAmount < :stockAmount";

int resultCount = em.createQuery(qlString)
				.setParameter("stockAmount", 10)
                .executeUpdate();
```

### 벌크 연산 주의

- 벌크 연산은 영속성 컨텍스트를 무시하고 데이터베이스에 직접 쿼리합니다.
  - 벌크 연산을 먼저 실행합니다.
  - **벌크 연산 수행 후 영속성 컨텍스트를 초기화**합니다.
