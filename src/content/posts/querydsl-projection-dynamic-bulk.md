---
author: "luca"
pubDatetime: 2023-06-18T15:57:22+09:00
modDatetime: 2026-10-13T15:51:36+09:00
title: "QueryDSL DTO 조회와 동적 조건 만들기"
slug: "querydsl-projection-dynamic-bulk"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "dynamic-query", "java"]
description: "회원 목록에 이름과 나이만 필요할 때 DTO로 바로 조회할 수 있습니다. 매핑 방식의 차이와 선택적인 검색 조건, 벌크 수정 후 재조회까지 살펴봅니다."
---

회원 검색 API가 이름과 나이만 반환한다면 엔티티 전체를 가져온 뒤 다시 DTO로 옮길 필요가 없을 수 있습니다. QueryDSL에서 필요한 필드를 직접 DTO로 조회하는 방법과, 검색값이 있을 때만 조건을 넣는 방법을 정리했습니다.

김영한님의 JPA 로드맵을 학습한 QueryDSL 5.x 예제입니다. 준비된 `JPAQueryFactory`와 Member 엔티티, Q 타입을 사용하며 각 코드는 독립된 조각입니다.

## 프로젝션 결과 반환

SELECT에서 무엇을 가져올지 지정하는 것을 프로젝션이라고 합니다. 이름만 가져오면 문자열 목록으로, 이름과 나이를 함께 가져오면 두 값을 담을 객체로 받아야 합니다.

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
    "SELECT new study.querydsl.dto.MemberDto(m.username, m.age) "
    + "from Member m", MemberDto.class)
    .getResultList();
```

### QueryDSL 빈 생성 - 3가지 방법

QueryDSL 5.x의 개별 예시입니다. `bean`은 기본 생성자와 쓰기 가능한 프로퍼티, `fields`는 기본 생성자와 대응 필드를 준비해야 합니다. `constructor`는 인자 순서와 타입이 일치하는 생성자가 필요하며, 생성자 일치 여부는 실행 때 드러날 수 있습니다. 아래에서 엔티티·Q 타입과 EntityManager 준비는 생략했습니다.

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

DTO 필드가 username 대신 name이면 조회 표현식에 별칭을 맞춥니다. 아래 최대 나이 서브쿼리는 SELECT 위치의 서브쿼리를 지원하는 Hibernate 확장을 전제로 합니다. `UserDto`에는 name과 age 필드 및 기본 생성자가 필요합니다.

```java
QMember memberSub = new QMember("memberSub");
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

- 생성된 Q 타입의 생성자를 통해 인자 타입을 컴파일 때 확인할 수 있습니다. 쿼리의 의미나 DB 실행 성공까지 보장하는 것은 아닙니다.
- 다만 DTO 에 QueryDSL 어노테이션을 유지해야 한다는 점은 트레이드오프입니다.

## 사용자가 입력한 검색 조건만 추가하기

이름만 입력한 요청에 나이 조건까지 붙이면 원하는 회원을 찾지 못할 수 있습니다. 아래 두 구현은 null을 미입력으로 다룹니다. 빈 문자열과 공백을 어떻게 취급할지는 API의 입력 정책에 맞춰 추가해야 합니다.

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

### 조건을 메서드로 나누기

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

`where`의 null 인자는 무시됩니다. 조건 조합을 재사용하기 좋지만 모든 조건이 null이면 전체 조회가 될 수 있습니다. 검색 API의 빈 조건 정책과 최대 조회 범위를 먼저 정합니다. 같은 회원·팀 검색을 두 방식으로 비교한 예시는 [동적 검색 쿼리](/posts/pure-jpa-with-querydsl/)에 있습니다.

## 여러 회원을 한 번에 바꾼 뒤 메모리 값 확인하기

목록 조회와 달리 여러 행을 일괄 수정할 때는 벌크 쿼리를 사용할 수 있습니다. 다음은 문법을 설명하는 개별 예제이며 실제 업무 정책을 표현한 것은 아닙니다.

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

위 벌크 예시는 활성 트랜잭션 안에서 실행합니다. 미반영 엔티티 변경이 있다면 먼저 `em.flush()`하고, 벌크 실행 뒤 `em.clear()`와 재조회로 오래된 메모리 값을 사용하지 않게 합니다. clear는 저장되지 않은 변경을 버릴 수 있으므로 순서를 바꾸지 않습니다.

## 기본 표현식으로 부족할 때 DB 함수 사용하기

사용자명 일부를 치환하는 함수처럼 DB 기능이 필요할 수 있습니다. 먼저 QueryDSL에 해당 표현식이 있는지 확인하고, 직접 함수 템플릿을 쓴다면 선택한 DB와 JPA 구현이 그 함수를 지원하는지도 확인합니다.

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
