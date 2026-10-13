---
author: "luca"
pubDatetime: 2023-06-15T23:38:05+09:00
modDatetime: 2026-10-13T15:32:55+09:00
title: "JPQL 조인과 fetch join의 차이"
slug: "jpql-path-fetchjoin-polymorphism"
featured: false
draft: false
tags: ["학습노트", "jpa", "jpql", "fetch-join", "n+1"]
description: "회원과 팀을 함께 조회하는 예제로 일반 조인과 fetch join을 비교합니다. 컬렉션 페이징, 상속 타입 조회, 벌크 수정에서 달라지는 동작도 정리했습니다."
---

회원을 조회한 뒤 화면에 팀 이름을 표시한다고 가정해 보겠습니다. JPQL에 팀 조인이 들어 있으니 팀 정보도 이미 읽었다고 생각하기 쉽습니다. 하지만 조건을 위해 팀을 조인하는 것과, 연관된 팀 엔티티까지 초기화하는 것은 다릅니다.

김영한님의 JPA 로드맵을 학습하면서 이 차이를 중심으로 정리했습니다. 아래 `Member`는 회원, `Team`은 팀이며 회원 여러 명이 한 팀에 속하는 모델입니다.

## 점 하나에도 조인이 생긴다

`m.username`은 회원의 일반 필드를 읽습니다. 반면 `m.team.name`처럼 연관된 객체로 이동하면 SQL에 조인이 필요할 수 있습니다.

```sql
SELECT m FROM Member m WHERE m.team.name = '팀A'
```

이런 묵시적 연관 조인은 내부 조인으로 처리됩니다. 팀이 없는 회원도 남겨야 한다면 의도를 드러내는 명시적 조인을 사용하는 편이 좋습니다.

```sql
SELECT m FROM Member m LEFT JOIN m.team t
```

컬렉션은 단일 객체처럼 계속 점을 찍어 탐색할 수 없습니다. `t.members`의 개별 회원을 조건에 쓰려면 `JOIN t.members m`처럼 조인해 별칭을 얻어야 합니다. 명시적으로 조인을 적으면 쿼리의 어느 부분에서 행이 늘거나 제외되는지도 읽기 쉽습니다.

## 일반 조인과 fetch join 비교

다음 두 JPQL은 모두 회원과 팀을 조인하지만 조회 목적이 다릅니다.

```sql
-- 팀을 조회 조건에 사용하고 회원을 반환
SELECT m FROM Member m JOIN m.team t WHERE t.name = '팀A'

-- 회원을 반환하면서 팀도 함께 로딩
SELECT m FROM Member m JOIN FETCH m.team
```

첫 번째 쿼리는 일반 조인입니다. 팀을 조건에 사용했다는 사실만으로 회원의 `team` 연관이 초기화됐다고 볼 수 없습니다. 두 번째 쿼리는 fetch join으로, 회원과 팀의 데이터를 함께 읽어 객체 관계를 구성합니다. 회원마다 팀을 사용할 화면이라면 추가 지연 로딩을 줄일 수 있습니다.

반대로 팀 이름과 회원 수만 필요하다면 엔티티 그래프 전체를 가져올 필요가 없습니다. 일반 조인과 DTO 프로젝션으로 필요한 값만 읽는 방법도 비교해야 합니다.

## 컬렉션을 함께 읽으면 행이 늘어난다

팀 A에 회원 두 명이 있을 때 다음 조회의 SQL 결과에는 팀 A가 두 행에 나타납니다.

```sql
SELECT t FROM Team t JOIN FETCH t.members WHERE t.name = '팀A'
```

회원 열이 서로 다르므로 SQL의 `DISTINCT`를 붙인다고 두 SQL 행이 하나로 줄어드는 것은 아닙니다. 엔티티 결과 목록에서 팀 중복을 없애는 처리와 DB에서 읽은 행 수를 구분해야 합니다. Hibernate 6은 fetch join으로 생기는 엔티티 결과 중복을 자동으로 제거하지만, 조인 자체의 데이터 양은 남습니다.

이 차이는 페이징에서 중요합니다. “팀 10개”를 원하는데 SQL 행에 제한을 걸면 회원 수에 따라 일부 팀의 회원만 읽을 수 있습니다. Hibernate는 컬렉션 fetch join의 페이징을 메모리에서 처리하거나 설정에 따라 오류로 거절할 수 있습니다. 부모 ID를 먼저 페이지 단위로 조회하고 연관을 추가 조회하거나, batch fetch를 사용하는 방법을 검토해야 합니다.

컬렉션 두 개를 함께 조인하면 자식 수의 곱만큼 행이 늘 수도 있습니다. Hibernate의 여러 bag 컬렉션 fetch 제한도 있으므로, N+1을 없애려고 모든 연관을 한 쿼리에 넣는 접근은 피하는 편이 좋습니다. 단일 값 연관을 fetch join하는 경우와 컬렉션을 가져오는 경우를 나눠 봐야 합니다.

## 상속 타입을 조건으로 쓰는 경우

`Item` 아래에 `Book`과 `Movie`가 있다면 `TYPE`으로 하위 타입을 고를 수 있습니다. `TREAT`는 특정 하위 타입의 속성에 접근할 때 사용합니다.

```sql
SELECT i FROM Item i WHERE TYPE(i) IN (Book, Movie)
SELECT i FROM Item i WHERE TREAT(i AS Book).author = 'kim'
```

생성 SQL은 상속 매핑과 JPA 구현에 따라 달라집니다. `SINGLE_TABLE`에서는 구분 컬럼을 활용할 수 있지만, 다른 상속 전략에서도 같은 SQL이 나온다고 보면 안 됩니다.

## 여러 행을 한 번에 수정한 뒤에는 다시 조회하기

재고가 10개 미만인 상품 가격을 일괄 변경한다고 가정해 보겠습니다. 엔티티를 모두 읽어 하나씩 바꾸는 대신 벌크 UPDATE를 사용할 수 있습니다.

```java
// 활성 트랜잭션 안에서 실행
em.flush();
int changed = em.createQuery(
    "UPDATE Product p SET p.price = p.price * 1.1 WHERE p.stockAmount < :stock"
).setParameter("stock", 10).executeUpdate();
em.clear();
```

벌크 연산은 영속성 컨텍스트의 엔티티 상태를 거치지 않고 DB를 수정합니다. 이미 메모리에 상품을 올려 두었다면 가격이 이전 값으로 남을 수 있습니다. 미반영 변경은 먼저 `flush()`하고, 벌크 수정 뒤에는 `clear()`한 다음 필요한 데이터를 다시 읽는 이유입니다. 저장하지 않은 변경이 있는데 먼저 `clear()`하면 그 변경을 잃을 수 있으므로 순서도 중요합니다.
