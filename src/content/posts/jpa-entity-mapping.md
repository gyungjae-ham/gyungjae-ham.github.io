---
author: "luca"
pubDatetime: 2023-05-23T18:26:14+09:00
title: "엔티티 매핑"
slug: "jpa-entity-mapping"
featured: false
draft: false
tags: ["jpa", "entity", "mapping"]
description: "@Entity·@Table·@Column 부터 기본 키 생성 전략(IDENTITY·SEQUENCE·TABLE)까지 JPA 엔티티 매핑의 핵심을 정리한 학습 노트입니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 엔티티 매핑 소개

- 객체와 테이블 매핑: `@Entity`, `@Table`
- 필드와 컬럼 매핑: `@Column`
- 기본 키 매핑: `@Id`
- 연관관계 매핑: `@ManyToOne`, `@JoinColumn`

## 객체와 테이블 매핑

### @Entity

- `@Entity`가 붙은 클래스는 JPA가 관리하는 엔티티입니다.
- JPA를 사용해서 테이블과 매핑할 클래스는 **`@Entity`** 가 필수입니다.

#### 주의할 점

- **기본 생성자 필수** (파라미터가 없는 `public` 또는 `protected` 생성자)
- `final` 클래스, `enum`, `interface`, `inner` 클래스는 사용할 수 없습니다.
- 저장할 필드에 `final`을 사용할 수 없습니다.

#### @Entity 속성

- **`name`**: JPA에서 사용할 엔티티 이름을 지정합니다.
- **기본값**: 클래스 이름을 그대로 사용합니다.

### @Table

`@Table`은 엔티티와 매핑할 테이블을 지정합니다.

| 속성 | 기능 | 기본값 |
|------|------|-------|
| `name` | 매핑할 테이블 이름 | 엔티티 이름을 사용 |
| `catalog` | 데이터베이스 catalog 매핑 | |
| `schema` | 데이터베이스 schema 매핑 | |
| `uniqueConstraints` (DDL) | DDL 생성 시 유니크 제약 조건 생성 | |

## 데이터베이스 스키마 자동 생성

- DDL을 애플리케이션 실행 시점에 자동으로 생성해 줍니다.
- 객체 중심으로 엔티티를 생성하면 필요한 테이블을 생성해 줍니다.
- 데이터베이스 방언(`dialect`)을 활용해 적절한 DDL을 생성합니다.
- **이렇게 생성된 DDL은 개발 장비에서만 사용합니다.**
- 운영 서버에서는 사용하지 않거나 적절히 다듬은 후 사용합니다.

### hibernate.hbm2ddl.auto 속성

| 옵션 | 설명 |
|------|------|
| `create` | 기존 테이블 삭제 후 다시 생성 (`DROP` + `CREATE`) |
| `create-drop` | `create`와 같으나 종료 시점에 테이블 `DROP` |
| `update` | 변경분만 반영 (운영 DB에는 사용하면 안 됨) |
| `validate` | 엔티티와 테이블이 정상 매핑되었는지만 확인 |
| `none` | 사용하지 않음 |

### 주의할 점

- **운영 장비에는 절대 `create`, `create-drop`, `update`를 사용하면 안 됩니다.**
- 개발 초기 단계: `create` 또는 `update`
- 테스트 서버: `update` 또는 `validate`
- 스테이징과 운영 서버: `validate` 또는 `none`
- 개발·테스트·스테이징 서버에서도 직접 DDL을 작성하는 것을 권장합니다.

### DDL 생성 기능

- 제약조건 추가 예시: `@Column(nullable = false, length = 10)`
- 유니크 제약조건: `@Table(uniqueConstraints = {@UniqueConstraint(name = "NAME_AGE_UNIQUE", columnNames = {"NAME", "AGE"})})`
- DDL 생성 기능은 DDL 자동 생성 시에만 사용되며 JPA 실행 로직에는 영향을 주지 않습니다.

## 필드와 컬럼 매핑

| 어노테이션 | 설명 |
|-----------|------|
| `@Column` | 컬럼 매핑 |
| `@Temporal` | 날짜 타입 매핑 (`DATE`, `TIME`, `TIMESTAMP`) |
| `@Enumerated` | `enum` 타입 매핑 |
| `@Lob` | `BLOB`, `CLOB` 매핑 |
| `@Transient` | 특정 필드를 컬럼에 매핑하지 않음 |

### @Column

| 속성 | 설명 | 기본값 |
|------|------|-------|
| `name` | 필드와 매핑할 테이블의 컬럼 이름 | 객체의 필드 이름 |
| `insertable`, `updatable` | 등록, 변경 가능 여부 | `TRUE` |
| `nullable` (DDL) | `null` 값 허용 여부 | |
| `unique` (DDL) | 유니크 제약조건 | |
| `columnDefinition` (DDL) | 데이터베이스 컬럼 정보를 직접 지정 | |
| `length` (DDL) | 문자 길이 제약조건 (`String` 타입만) | 255 |
| `precision`, `scale` (DDL) | `BigDecimal` 타입에서 사용 | `precision = 19`, `scale = 2` |

### @Enumerated

자바 `enum` 타입을 매핑할 때 사용합니다.

| 속성 | 설명 | 기본값 |
|------|------|-------|
| `value` | `EnumType.ORDINAL` (순서) 또는 `EnumType.STRING` (이름) | `EnumType.ORDINAL` |

**주의**: `ORDINAL`을 사용하면 `enum`에 새로운 타입을 추가할 때 기존 데이터의 매핑이 깨질 수 있으므로 반드시 **`STRING`을 사용**합니다.

### @Temporal

날짜 타입(`java.util.Date`, `java.util.Calendar`)을 매핑할 때 사용합니다.

참고: `LocalDate`, `LocalDateTime`을 사용할 때는 생략이 가능합니다.

| 속성 | 설명 |
|------|------|
| `value` | `TemporalType.DATE` (날짜), `TIME` (시간), `TIMESTAMP` (날짜와 시간) |

### @Lob

- 데이터베이스 `BLOB`, `CLOB` 타입과 매핑됩니다.
- 지정할 수 있는 속성이 없습니다.
- 필드 타입이 문자면 `CLOB` 매핑, 나머지는 `BLOB`이 매핑됩니다.
  - `CLOB`: `String`, `char[]`, `java.sql.CLOB`
  - `BLOB`: `byte[]`, `java.sql.BLOB`

### @Transient

- 필드를 매핑하지 않습니다.
- 데이터베이스에 저장 및 조회하지 않습니다.
- 메모리상에서만 임시로 값을 보관하고 싶을 때 사용합니다.

```java
@Transient
private Integer temp;
```

## 기본 키 매핑

- `@Id`
- `@GeneratedValue`

```java
@Id @GeneratedValue(strategy = GenerationType.AUTO)
private Long id;
```

### 기본 키 매핑 방법

- **직접 할당**: `@Id`만 사용해서 할당합니다.
- **자동 생성** (`@GeneratedValue`)
  - **`IDENTITY`**: 데이터베이스에 위임
  - **`SEQUENCE`**: 데이터베이스 시퀀스 오브젝트 사용 (`@SequenceGenerator` 필요)
  - **`TABLE`**: 키 생성용 테이블 사용 (`@TableGenerator` 필요)
  - **`AUTO`**: 방언에 따라 자동으로 지정 (기본값)

### IDENTITY 전략 특징

- 기본 키 생성을 데이터베이스에 위임합니다.
- 주로 MySQL, PostgreSQL, SQL Server, DB2에서 사용합니다 (예: MySQL의 `AUTO_INCREMENT`).
- JPA는 보통 트랜잭션 커밋 시점에 `INSERT SQL`을 실행합니다.
- **`IDENTITY` 전략은 `commit()` 시점이 아닌 `persist()` 시점에 즉시 `INSERT SQL`을 실행하고 DB에서 식별자를 조회합니다.**

### SEQUENCE 전략 특징

- 데이터베이스 시퀀스는 유일한 값을 순서대로 생성하는 특별한 데이터베이스 오브젝트입니다.
- Oracle, PostgreSQL, DB2, H2 데이터베이스에서 사용합니다.
- `persist()` 시점에 DB에서 시퀀스 값을 가져와 ID 값을 지정합니다.

```
Hibernate:
    call next value for MEMBER_SEQ
```

- 그 다음 ID 값을 채워 넣고 영속성 컨텍스트에 저장합니다 (아직 DB에 `INSERT SQL`은 날아가지 않습니다).
- 이후 `commit()` 시점에 DB에 `INSERT SQL`이 실행됩니다.
- **`allocationSize` 옵션으로 최적화**: `allocationSize = 50`을 설정하면 미리 50개의 시퀀스 값을 가져와 메모리에 저장하고 사용합니다.

#### SEQUENCE 전략 매핑

```java
@Entity
@SequenceGenerator(
    name = "MEMBER_SEQ_GENERATOR",
    sequenceName = "MEMBER_SEQ",
    initialValue = 1, allocationSize = 1)
public class Member {

    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE,
        generator = "MEMBER_SEQ_GENERATOR")
    private Long id;
}
```

#### @SequenceGenerator 속성

| 속성 | 설명 | 기본값 |
|------|------|-------|
| `name` | 식별자 생성기 이름 | 필수 |
| `sequenceName` | 데이터베이스에 등록된 시퀀스 이름 | `hibernate_sequence` |
| `initialValue` | DDL 생성 시 시퀀스 시작 수 | 1 |
| `allocationSize` | 시퀀스 한 번 호출에 증가하는 수 | 50 |
| `catalog`, `schema` | 데이터베이스 catalog, schema 이름 | |

### TABLE 전략

- 키 생성 전용 테이블을 만들어 데이터베이스 시퀀스를 흉내내는 전략입니다.
- **장점**: 모든 데이터베이스에 적용 가능합니다.
- **단점**: 성능 문제가 있을 수 있습니다.

#### TABLE 전략 매핑

키 생성 전용 테이블 생성:

```sql
create table MY_SEQUENCES (
    sequence_name varchar(255) not null,
    next_val bigint,
    primary key ( sequence_name )
)
```

설정:

```java
@Entity
@TableGenerator(
    name = "MEMBER_SEQ_GENERATOR",
    table = "MY_SEQUENCES",
    pkColumnValue = "MEMBER_SEQ", allocationSize = 1)
public class Member {

    @Id
    @GeneratedValue(strategy = GenerationType.TABLE,
                    generator = "MEMBER_SEQ_GENERATOR")
    private Long id;
}
```

#### @TableGenerator 속성

| 속성 | 설명 | 기본값 |
|------|------|-------|
| `name` | 식별자 생성기 이름 | 필수 |
| `table` | 키 생성 테이블명 | `hibernate_sequences` |
| `pkColumnName` | 시퀀스 컬럼명 | `sequence_name` |
| `valueColumnName` | 시퀀스 값 컬럼명 | `next_val` |
| `pkColumnValue` | 키로 사용할 값 이름 | 엔티티 이름 |
| `initialValue` | 초기 값 | 0 |
| `allocationSize` | 시퀀스 한 번 호출에 증가하는 수 | 50 |
| `catalog`, `schema` | 데이터베이스 catalog, schema | |
| `uniqueConstraints` (DDL) | 유니크 제약 조건 | |

## 권장하는 식별자 전략

- **기본 키 제약 조건**: `null`이 아니어야 하고, 유일해야 하며, **변하면 안 됩니다.**
- 미래까지 이 조건을 만족하는 자연키는 찾기 어렵습니다.
- 대리키(비즈니스와 무관한 값)를 사용하도록 합니다.
- 예를 들어 주민등록번호도 기본 키로 적절하지 않습니다.
- **권장**: `Long`형 + 대체키 + 키 생성 전략 사용
  - `Auto-Increment`, `Sequence`, `uuid` 등
