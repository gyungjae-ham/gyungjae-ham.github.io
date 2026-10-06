---
author: "luca"
pubDatetime: 2023-08-16T17:49:19+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 성능을 볼 때 batch fetch와 OSIV를 구분하는 이유"
slug: "jpa-performance-tuning"
featured: false
draft: false
tags:
  ["학습노트", "jpa", "performance", "n+1", "fetch-join", "batch-size", "osiv"]
description: "연관 로딩의 쿼리 수와 데이터 양을 살펴보고, batch fetch·페이징·OSIV가 각각 바꾸는 범위를 구분합니다. 세션 수명과 JDBC 연결 점유도 따로 봅니다."
---

주문 목록에서 주문별 항목을 차례로 읽으면, 목록 조회 한 번 뒤에 항목 조회가 주문 수만큼 반복될 수 있습니다. JPA 성능을 볼 때는 어떤 엔티티를 반환했는지뿐 아니라 응답을 만드는 동안 접근한 연관관계까지 확인해야 합니다.

이 글은 Spring Boot 3.x·Hibernate 6의 일반적인 조회 동작을 기준으로 설명합니다. 사용 중인 매핑과 버전에 따라 생성 SQL은 달라질 수 있습니다.

## batch fetch가 줄이는 것은 왕복 횟수다

설명용으로 주문 10개와 각 주문의 지연 로딩 항목을 생각해보겠습니다. 아무 묶음 조회가 없으면 목록 조회 이후 항목 조회가 열 번 생길 수 있습니다. batch fetch를 사용하면 같은 영속성 컨텍스트에 있는 미초기화 대상을 모아 여러 주문의 항목을 IN 조건으로 읽을 수 있습니다.

```yaml
spring:
  jpa:
    properties:
      hibernate:
        default_batch_fetch_size: 100
```

```sql
SELECT * FROM orders WHERE user_id = ?;
SELECT * FROM order_item WHERE order_id IN (?, ?, ?);
```

SQL은 동작을 설명하는 축약 예시입니다. 한 종류의 컬렉션을 배치 크기만큼 모두 묶을 수 있다는 조건에서는 `1 + ceil(N / batch_size)` 형태로 생각할 수 있지만, 캐시 상태·접근 순서·다른 연관관계가 끼면 실제 횟수는 다릅니다.

크기를 늘리면 왕복은 줄어도 한 번에 읽는 행과 메모리가 늘어납니다. DB·드라이버·버전의 바인딩 제한과 실제 실행 계획을 확인해야 합니다. 모든 DB에 같은 IN 한도를 적용하지 않습니다.

## fetch join과 페이징을 함께 쓸 때

컬렉션을 fetch join하면 부모 한 행이 자식 수만큼 늘어납니다. 여기에 페이지 제한을 걸면 Hibernate가 메모리에서 제한하거나 설정에 따라 실패할 수 있습니다. 부모 ID를 먼저 페이지 단위로 읽고 필요한 연관을 나중에 조회하는 방법, batch fetch, DTO 조회 등을 비교합니다.

일대일 지연 로딩도 소유 방향과 optional 조건, 프록시·bytecode enhancement 지원을 함께 봐야 합니다. `LAZY`와 배치 크기만 설정했다고 모든 관계가 같은 방식으로 로딩되지는 않습니다. [Hibernate 6.6 조회 설명](https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#fetching)

## OSIV는 세션의 수명을 바꾼다

OSIV는 웹 요청 처리 중 영속성 컨텍스트를 열어 두어 Service의 트랜잭션 이후에도 지연 로딩이 가능하게 합니다. **영속성 컨텍스트가 열려 있는 시간과 JDBC 커넥션을 점유한 시간은 같지 않습니다.** 연결 획득·반환은 트랜잭션과 Hibernate의 connection handling 설정 등에 따라 달라집니다.

따라서 OSIV가 켜져 있다는 이유만으로 외부 API를 기다리는 내내 연결이 반드시 유지된다고 단정하지 않습니다. 컨트롤러나 직렬화 단계에서 SQL이 추가되는지, 그 과정의 연결 점유가 얼마나 되는지 관측합니다.

`spring.jpa.open-in-view: false`를 선택하면 트랜잭션 안에서 응답에 필요한 데이터를 준비하기 쉬워집니다. 대신 닫힌 컨텍스트의 미초기화 연관을 나중에 접근하는 코드를 정리해야 합니다. 기존 API에서는 DTO 변환과 필요한 조회를 먼저 검증한 뒤 바꾸는 편이 안전합니다.

## Kotlin 엔티티와 조회 API의 조건

Kotlin 엔티티에는 JPA용 기본 생성자와 프록시가 필요한 경우의 open 설정을 준비합니다. `kotlin-jpa`의 no-arg 지원과 all-open 설정은 역할이 다릅니다. data class의 생성된 `equals`·`hashCode`·`toString`에 연관관계가 들어가는지도 확인합니다.

`findById`는 이미 영속성 컨텍스트나 캐시에 있으면 SQL 없이 반환할 수 있습니다. `getReferenceById`도 언제나 새 프록시만 만들고 SELECT를 생략한다고 단정할 수는 없습니다. 실제 로딩은 접근과 구현 조건에 따라 확인합니다.

변경 전후에는 같은 수의 주문과 항목으로 전체 응답 생성까지 실행합니다. SQL 횟수만 줄었는지, 읽은 행과 응답 시간·메모리도 줄었는지를 함께 보면 설정의 효과를 과장하지 않을 수 있습니다.
