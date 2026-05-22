---
author: "luca"
pubDatetime: 2023-05-19T19:35:14+09:00
title: "방언, 작동원리, JPQL"
slug: "jpa-dialect-and-jpql-basics"
featured: false
draft: false
tags: ["jpa", "dialect", "jpql", "hibernate"]
description: "데이터베이스 방언이 필요한 이유와 JPA 구동 방식, JPQL 이 SQL 과 다른 지점을 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 데이터베이스 방언

JPA는 특정 데이터베이스에 종속되지 않지만, 각 데이터베이스마다 SQL 문법이 다르다는 문제가 있습니다. 예를 들어 다음과 같습니다.

- **가변 문자**: MySQL은 `VARCHAR`, Oracle은 `VARCHAR2`
- **문자열 함수**: SQL 표준 `SUBSTRING()` vs Oracle의 `SUBSTR()`
- **페이징**: MySQL의 `LIMIT` vs Oracle의 `ROWNUM`

방언은 "SQL 표준을 지키지 않는 특정 데이터베이스만의 고유한 기능"입니다. `hibernate.dialect` 속성에서 지정하며, 하이버네이트는 40개 이상의 데이터베이스 방언을 지원합니다.

## JPA 구동 방식

`Persistence` 클래스가 설정 정보를 읽어 `EntityManagerFactory`를 생성하고, 이를 통해 `EntityManager`를 생성합니다. 주요 특징은 다음과 같습니다.

- `EntityManagerFactory`는 애플리케이션 시작 시 한 번만 생성합니다.
- `EntityManager`는 요청마다 생성합니다.
- **`EntityManager`는 쓰레드 간 공유가 금지됩니다.**
- **모든 데이터 변경은 트랜잭션 내에서 실행합니다.**

## JPA Update Query

JPA가 관리하는 엔티티는 트랜잭션 커밋 시점에 변경 사항이 감지되면, 자동으로 `UPDATE` 쿼리가 생성되어 커밋됩니다. 개발자가 명시적으로 쿼리를 작성할 필요가 없습니다.

## JPQL이란

JPQL은 "객체 지향 쿼리" 언어로, 테이블이 아닌 엔티티 객체를 대상으로 검색합니다. SQL을 추상화하여 특정 데이터베이스에 의존하지 않습니다.

### JPQL의 이점

페이징 처리 예시에서, JPQL은 데이터베이스 방언별 차이를 자동으로 처리합니다. `setFirstResult()`와 `setMaxResults()`를 사용하면 각 DB에 맞는 쿼리(MySQL은 `limit offset`, Oracle은 `ROWNUM` 등)가 자동 생성됩니다.

### JPQL 기능

- `SELECT`, `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `JOIN`을 지원합니다.
- **핵심 차이: JPQL은 엔티티 객체 대상, SQL은 테이블 대상입니다.**
