---
author: "luca"
pubDatetime: 2023-05-23T18:26:14+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 엔티티 매핑: 컬럼 제약과 식별자 생성 시점 구분하기"
slug: "jpa-entity-mapping"
featured: false
draft: false
tags: ["학습노트", "jpa", "entity", "mapping"]
description: "@Entity·@Table·@Column 부터 기본 키 생성 전략(IDENTITY·SEQUENCE·TABLE)까지 JPA 엔티티 매핑의 핵심을 정리한 학습 노트입니다."
---

김영한님의 JPA 로드맵을 따라 정리한 학습 노트입니다. 엔티티 매핑에서 헷갈리기 쉬운 것은 Java 필드의 의미, DB 제약, 식별자를 얻는 시점이 서로 다른 설정이라는 점입니다. 아래 설명은 Jakarta Persistence 3.1과 Hibernate 6 계열을 기준으로 합니다.

## 필드 선언과 DB 제약을 함께 읽기

```java
@Entity
@Table(name = "catalog_item")
public class CatalogItem {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal price;

    @Enumerated(EnumType.STRING)
    private ItemStatus status;

    protected CatalogItem() {}
}
```

`ItemStatus` enum과 imports를 생략한 MySQL 계열의 학습용 매핑입니다. DDL 생성 시 name은 최대 길이 100의 NOT NULL 문자 컬럼, price는 전체 자릿수 12·소수 자릿수 2의 decimal 컬럼을 의도합니다. 이는 가격을 소수 둘째 자리로 반올림하는 도메인 정책까지 정해 주는 설정은 아닙니다.

`@Column`의 precision과 scale 애노테이션 기본값은 각각 0입니다. precision 0은 구현체가 추론하도록 하는 값이므로 `19, 2`를 모든 JPA 구현의 기본값으로 외우면 안 됩니다. 금액처럼 DB 타입이 중요한 필드는 명시하고 생성된 DDL이나 마이그레이션을 확인하는 편이 명확합니다.

문자열 enum은 상수를 재정렬해도 저장값의 의미를 유지합니다. 다만 이름 자체를 바꾸면 데이터 이관이 필요합니다. ORDINAL을 사용할 수 없는 것은 아니지만, 순서 변경이 기존 데이터의 뜻을 바꾼다는 비용을 감수해야 합니다. 더 안정된 외부 코드를 쓰고 싶으면 converter를 별도로 둘 수 있습니다.

`@Temporal`은 `java.util.Date`·`Calendar`용입니다. `LocalDate`, `LocalDateTime` 같은 지원 타입에는 붙이지 않습니다. `@Transient` 필드는 JPA 저장 대상에서 빠집니다.

## ID를 얻는 시점과 INSERT·commit은 다르다

| 전략      | 식별자를 얻는 방식                 | 확인할 비용                  |
| --------- | ---------------------------------- | ---------------------------- |
| 직접 할당 | persist 전에 애플리케이션이 지정   | 충돌 방지와 불변성           |
| IDENTITY  | INSERT 결과로 DB 생성값을 받음     | 조기 INSERT, 배치 제약       |
| SEQUENCE  | DB sequence와 식별자 할당기를 사용 | 할당 단위와 DB sequence 설정 |
| TABLE     | 별도 테이블에서 식별자 구간 확보   | 키 테이블의 경합·추가 접근   |
| AUTO      | 구현체가 타입·DB 등을 보고 선택    | 실제 선택된 전략             |

IDENTITY에서는 ID를 알아야 하므로 활성 트랜잭션의 일반적인 persist 흐름에서 INSERT가 일찍 실행될 수 있습니다. 반면 SEQUENCE는 ID를 먼저 확보하고 INSERT를 flush까지 미룰 수 있습니다. 어느 경우든 SQL이 실행됐다는 사실과 트랜잭션이 commit됐다는 사실은 다릅니다.

`allocationSize = 50`은 한 번의 호출로 시퀀스 값을 50번 읽어 배열에 보관한다는 뜻이 아닙니다. Hibernate의 pooled 계열 최적화는 식별자 구간을 확보한 뒤 여러 ID를 메모리에서 생성해 DB 왕복을 줄입니다. 정확한 알고리즘과 sequence의 increment 일치는 설정에 따라 확인해야 합니다. 중단·재시작으로 번호가 비는 것은 허용해야 하며 업무상 연속 번호로 쓰기에는 맞지 않습니다.

기본 sequence나 키 테이블 이름도 JPA가 `hibernate_sequence` 등으로 고정한 값은 아닙니다. 구현체·버전별 생성 규칙에 기대기보다 이름이 중요하면 매핑과 마이그레이션에 명시합니다.

## 운영 스키마는 변경 과정을 관리한다

`create`와 `create-drop`은 기존 데이터를 지울 수 있고 `update`는 검토된 데이터 이관 계획을 대신하지 않습니다. 운영에서는 명시적인 마이그레이션과 `validate` 또는 자동 생성 비활성화를 조합해 변경 과정을 관리하는 편이 적합합니다. 애노테이션을 바꿨다고 이미 존재하는 DB 제약이 자동으로 바뀌었다고 가정하지 않습니다.

필드·식별자 애노테이션의 기준은 [Jakarta Persistence 3.1 명세](https://jakarta.ee/specifications/persistence/3.1/jakarta-persistence-spec-3.1), flush의 구체적인 흐름은 [영속성 컨텍스트 노트](/posts/jpa-persistence-context/)에서 이어서 볼 수 있습니다.
