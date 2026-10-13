---
author: "luca"
pubDatetime: 2023-08-16T17:49:19+09:00
modDatetime: 2026-10-13T15:32:55+09:00
title: "JPA batch fetch와 OSIV 설정을 이해하기"
slug: "jpa-performance-tuning"
featured: false
draft: false
tags:
  ["학습노트", "jpa", "performance", "n+1", "fetch-join", "batch-size", "osiv"]
description: "주문 목록 뒤에 붙는 추가 조회는 batch fetch로 줄일 수 있습니다. OSIV는 무엇이 다른지, 쿼리 수와 세션 수명을 나눠 살펴봅니다."
---

주문 목록을 조회하는 SQL은 한 번인데 API에서는 여러 쿼리가 나갈 수 있습니다. 응답을 만들면서 각 주문의 상품 목록에 접근하기 때문입니다. 주문 10개를 가져온 뒤 상품을 하나씩 읽으면 추가 조회가 열 번 발생하는 식입니다.

이 문제를 볼 때 `default_batch_fetch_size`와 OSIV 설정이 함께 언급되곤 합니다. 하지만 두 설정이 바꾸는 것은 다릅니다. 하나는 연관 데이터를 묶어 읽는 방식이고, 다른 하나는 웹 요청에서 영속성 컨텍스트를 열어 두는 범위입니다. Spring Boot 3.x·Hibernate 6 기준으로 구분해 봤습니다.

## 상품 목록을 주문마다 읽는 대신 묶어서 읽기

지연 로딩 상태인 주문상품 컬렉션을 batch fetch로 읽으면, 같은 영속성 컨텍스트에 있는 여러 주문의 항목을 묶어 가져올 수 있습니다.

```yaml
spring:
  jpa:
    properties:
      hibernate:
        default_batch_fetch_size: 100
```

동작을 단순화하면 다음과 같습니다. 실제 SQL과 묶음 크기는 접근 순서와 매핑 등에 따라 달라집니다.

```sql
SELECT * FROM orders WHERE user_id = ?;
SELECT * FROM order_item WHERE order_id IN (?, ?, ?);
```

이 설정은 DB 왕복을 줄이는 데 도움이 됩니다. 다만 읽어야 할 상품 자체가 사라지지는 않습니다. 묶음 크기를 키우면 한 번에 읽는 행과 메모리도 늘어나므로, 숫자를 크게 설정하는 것만으로 최적화가 끝나지는 않습니다. DB와 드라이버의 바인딩 제한, 실제 실행 계획도 확인해야 합니다.

## fetch join 하나로 끝내기 어려운 조회

주문과 상품을 fetch join하면 한 쿼리로 읽을 수 있지만, 주문 하나가 상품 수만큼 SQL 행으로 반복됩니다. 여기에 주문 20개라는 페이지 조건을 적용하는 것은 단순히 SQL 20행을 가져오는 것과 다릅니다.

Hibernate는 컬렉션 fetch join과 페이징을 함께 사용하면 전체 조인 결과를 읽고 메모리에서 제한하거나, 설정에 따라 오류로 처리할 수 있습니다. 주문 ID를 먼저 페이지 단위로 읽은 뒤 상품을 조회하는 방법과 batch fetch, DTO 조회를 비교해야 합니다. [Hibernate 조회 문서](https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html#fetching)

## OSIV를 끄기 전에 필요한 데이터를 준비하기

OSIV가 켜져 있으면 서비스의 트랜잭션이 끝난 뒤에도 웹 요청 안에서 지연 로딩이 가능할 수 있습니다. 그래서 컨트롤러나 JSON 직렬화 단계에서 예상하지 못한 SQL이 추가되기도 합니다.

`spring.jpa.open-in-view: false`로 바꾸면 이런 접근을 정리하는 계기가 됩니다. 대신 주문 응답을 만드는 데 필요한 상품을 트랜잭션 안에서 조회하고 DTO로 변환해야 합니다. 조회 준비 없이 설정만 끄면 닫힌 영속성 컨텍스트에서 미초기화 연관에 접근하다 실패할 수 있습니다.

여기서 영속성 컨텍스트가 열려 있는 시간과 JDBC 커넥션을 점유한 시간을 같게 보면 안 됩니다. 커넥션 획득과 반환은 트랜잭션과 Hibernate 설정에도 영향을 받습니다. OSIV가 켜졌으니 외부 API를 기다리는 내내 DB 연결을 잡고 있다고 단정하기보다 실제 점유 시간을 확인해야 합니다.

설정을 비교할 때는 같은 수의 주문과 상품으로 응답 생성까지 실행합니다. SQL 횟수뿐 아니라 읽은 행 수, 응답 시간, 메모리 사용량을 같이 봐야 합니다. 쿼리는 줄었지만 훨씬 큰 결과를 읽는 변경인지도 이때 드러납니다.
