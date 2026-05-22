---
author: "luca"
pubDatetime: 2023-06-18T15:57:22+09:00
title: "프로젝션과 결과 반환, 동적쿼리, 벌크 쿼리"
slug: "querydsl-projection-dynamic-bulk"
featured: false
draft: false
tags: ["querydsl", "jpa", "dynamic-query", "java"]
description: "QueryDSL 의 프로젝션 종류, 동적 쿼리 두 가지 방식, 벌크 연산과 SQL 함수 호출까지 한 번에 정리합니다."
---

> 김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다.

## 프로젝션 결과 반환

**프로젝션**은 `SELECT` 대상을 지정하는 것입니다.

### 프로젝션 대상이 하나

단일 대상일 때는 타입을 명확하게 지정할 수 있습니다. 둘 이상일 경우 튜플이나 DTO 로 조회합니다.

```java
List<String> result = queryFactory
    .select(member.username)
    .from(member)
    .fetch();
```

### 튜플 조회

```java
List<Tuple> result = queryFactory
    .select(member.username, member.age)
    .from(member)
    .fetch();

for (Tuple tuple : result) {
    String username = tuple.get(member.username);
    Integer age = tuple.get(member.age);
}
```

### DTO 조회 - 순수 JPA

순수 JPA 는 `new` 명령어를 사용하며 패키지명을 완전히 작성해야 합니다.

```java
List<MemberDto> result = em.createQuery(
    "SELECT new study.querydsl.dto.MemberDto(m.username, n.age) "
    + "from Member m", MemberDto.class)
    .getResultList();
```

### QueryDSL 빈 생성 - 3가지 방법

**프로퍼티 접근 (Setter)**

```java
List<MemberDto> result = queryFactory
    .select(Projections.bean(MemberDto.class,
        member.username,
        member.age))
    .from(member)
    .fetch();
```

**필드 직접 접근**

```java
List<MemberDto> result = queryFactory
    .select(Projections.fields(MemberDto.class,
        member.username,
        member.age))
    .from(member)
    .fetch();
```

**별칭이 다를 경우**

```java
List<UserDto> fetch = queryFactory
    .select(Projections.fields(UserDto.class,
        member.username.as("name"),
        ExpressionUtils.as(
            JPAExpressions
                .select(memberSub.age.max())
                .from(memberSub), "age")
    ))
    .from(member)
    .fetch();
```

**생성자 사용**

```java
List<MemberDto> result = queryFactory
    .select(Projections.constructor(MemberDto.class,
        member.username,
        member.age))
    .from(member)
    .fetch();
```

## @QueryProjection

DTO 의 생성자에 `@QueryProjection` 을 붙이면 컴파일 시점에 QMemberDto 가 생성됩니다.

```java
@Data
public class MemberDto {
    private String username;
    private int age;

    @QueryProjection
    public MemberDto(String username, int age) {
        this.username = username;
        this.age = age;
    }
}
```

사용 방법은 다음과 같습니다.

```java
List<MemberDto> result = queryFactory
    .select(new QMemberDto(member.username, member.age))
    .from(member)
    .fetch();
```

- 이 방식은 "컴파일러로 타입을 확인할 수 있으므로 가장 안전한 방법"입니다.
- 다만 DTO 에 QueryDSL 어노테이션을 유지해야 한다는 점은 트레이드오프입니다.

## 동적 쿼리 - BooleanBuilder

### BooleanBuilder 방식

```java
private List<Member> searchMember1(String usernameCond, Integer ageCond) {
    BooleanBuilder builder = new BooleanBuilder();
    if (usernameCond != null) {
        builder.and(member.username.eq(usernameCond));
    }
    if (ageCond != null) {
        builder.and(member.age.eq(ageCond));
    }
    return queryFactory
        .selectFrom(member)
        .where(builder)
        .fetch();
}
```

### WHERE 다중 파라미터 (권장)

```java
private List<Member> searchMember2(String usernameCond, Integer ageCond) {
    return queryFactory
        .selectFrom(member)
        .where(usernameEq(usernameCond), ageEq(ageCond))
        .fetch();
}

private BooleanExpression usernameEq(String usernameCond) {
    return usernameCond != null ? member.username.eq(usernameCond) : null;
}

private BooleanExpression ageEq(Integer ageCond) {
    return ageCond != null ? member.age.eq(ageCond) : null;
}
```

이 방식은 "코드가 깔끔해지기 때문에 더 선호되는 방법"입니다. `where` 절의 `null` 값은 무시되며, 메서드 재활용이 가능합니다.

## 수정, 삭제 벌크 연산

**대량 데이터 수정**

```java
long count = queryFactory
    .update(member)
    .set(member.username, "비회원")
    .where(member.age.lt(28))
    .execute();
```

**기존 숫자에 1 더하기**

```java
long count = queryFactory
    .update(member)
    .set(member.age, member.age.add(1))
    .execute();
```

**기존 숫자에 2 곱하기**

```java
long count = queryFactory
    .update(member)
    .set(member.age, member.age.multiply(2))
    .execute();
```

**대량 데이터 삭제**

```java
long count = queryFactory
    .delete(member)
    .where(member.age.gt(18))
    .execute();
```

> 중요: "영속성 컨텍스트에 있는 엔티티를 무시하고 실행되므로 배치 쿼리를 실행하고 나면 영속성 컨텍스트를 초기화하는 것이 안전합니다."

## SQL Function 호출하기

**Replace 함수**

```java
String result = queryFactory
    .select(Expressions.stringTemplate(
        "function('replace', {0}, {1}, {2})",
        member.username, "member", "M"))
    .from(member)
    .fetchFirst();
```

**Lower 함수**

```java
.select(member.username)
.from(member)
.where(member.username.eq(
    Expressions.stringTemplate("function('lower', {0})", member.username)))
```

또는 QueryDSL 내장 함수를 사용합니다.

```java
.where(member.username.eq(member.username.lower()))
```
