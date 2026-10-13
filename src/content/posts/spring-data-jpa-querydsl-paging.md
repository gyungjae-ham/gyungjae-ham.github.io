---
author: "luca"
pubDatetime: 2023-06-18T17:42:44+09:00
modDatetime: 2026-10-13T15:51:36+09:00
title: "QueryDSL 목록 조회의 정렬과 전체 개수 계산"
slug: "spring-data-jpa-querydsl-paging"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "spring-data-jpa", "java"]
description: "회원은 두 명인데 조인 결과가 세 행이면 전체 개수는 무엇일까요. 페이지의 내용과 count가 같은 대상을 세도록 쿼리를 나눠 작성합니다."
---

회원 목록에서 주문을 함께 조인한다고 생각해 보겠습니다. 회원 A의 주문이 두 건, B의 주문이 한 건이면 조인 결과는 세 행이 될 수 있습니다. 화면에는 회원 두 명을 보여 주는데 전체 개수를 3으로 반환하면 페이지 안내가 맞지 않습니다.

페이징은 offset과 limit 외에도 무엇을 한 항목으로 셀지, 같은 정렬값의 순서는 어떻게 할지 정해야 합니다. 먼저 조인 없는 단순한 회원 조회로 content와 count를 분리해 보겠습니다.

이 글은 Spring Data JPA와 QueryDSL 5.x를 기준으로 합니다. 커스텀 구현은 fragment 인터페이스와 그 이름에 `Impl`을 붙인 구현을 조합할 수 있습니다. 예를 들어 `MemberSearchRepository`와 `MemberSearchRepositoryImpl`을 만들고, 기본 JpaRepository가 fragment를 상속하게 합니다. 기존 Repository 이름 자체에 `Impl`을 붙이는 관례와 구분합니다. [Spring Data 커스텀 구현](https://docs.spring.io/spring-data/jpa/reference/repositories/custom-implementations.html)

## 정렬과 count를 드러낸 예시

다음은 성인 회원을 ID 오름차순으로 조회하는 메서드 부분입니다. `queryFactory`와 생성된 `member` Q 타입이 준비되어 있다고 가정합니다. 이 API는 정렬이 고정이므로 전달된 `Pageable.sort`를 조용히 무시하지 않고 거절합니다.

```java
public Page<Member> findAdults(Pageable pageable) {
    if (pageable.isUnpaged() || pageable.getSort().isSorted()) {
        throw new IllegalArgumentException("페이지 크기를 지정하고 정렬은 생략해야 합니다.");
    }
    BooleanExpression condition = member.age.goe(19);

    List<Member> content = queryFactory
        .selectFrom(member)
        .where(condition)
        .orderBy(member.id.asc())
        .offset(pageable.getOffset())
        .limit(pageable.getPageSize())
        .fetch();

    Long total = queryFactory
        .select(member.count())
        .from(member)
        .where(condition)
        .fetchOne();

    return new PageImpl<>(content, pageable, total == null ? 0L : total);
}
```

이름이나 나이로 정렬해야 한다면 허용할 필드를 QueryDSL 표현식으로 매핑하고, 마지막에 고유 ID를 추가해 동률 순서를 정합니다. 클라이언트가 보낸 속성명을 무제한으로 쿼리에 연결하지 않습니다. 요청 페이지 크기의 상한도 API에서 정합니다.

## 조인이 생기면 무엇을 세는지 다시 확인하기

QueryDSL JPA의 `fetchResults()`·`fetchCount()`는 5.x에서 deprecated입니다. 복잡한 GROUP BY·HAVING을 올바른 JPQL count 쿼리로 바꾸기 어려운 경우가 있기 때문입니다. [QueryDSL 5.0 변경 기록](https://github.com/querydsl/querydsl/releases/tag/QUERYDSL_5_0_0)

단순 목록에서는 위처럼 내용과 count를 분리하면 읽기 쉽습니다. 컬렉션 조인으로 회원 행이 늘어난다면 세고 싶은 것이 조인 행인지 고유 회원인지 다시 정해야 합니다. count에서 조인을 제거해도 되는지도 필터 조건에 달려 있습니다.

`PageableExecutionUtils.getPage`로 일부 count를 생략할 수 있지만, 내용 목록과 전체 개수가 같은 단위를 세는 조건을 먼저 만족해야 합니다. 총 개수가 필요하지 않다면 한 건 더 읽어 다음 페이지 존재만 알려주는 Slice도 선택지입니다.

## 같은 나이의 회원이 여러 명일 때

예를 들어 같은 나이의 회원을 여러 명 넣고 페이지 크기를 2로 두면, 나이 정렬만으로는 동률 순서가 불명확합니다. ID tie-break를 더한 뒤 첫 페이지와 다음 페이지의 중복·누락을 확인합니다. 빈 결과와 마지막 페이지도 별도 사례입니다.

ID를 추가하면 같은 데이터에서 동률 순서를 정할 수 있습니다. 다만 첫 페이지를 읽은 뒤 앞쪽에 새 회원이 추가되면 다음 offset 페이지에 이미 본 회원이 나올 수 있습니다. 변경이 잦은 목록에서는 cursor 방식이나 같은 시점의 데이터를 유지해야 하는 요구까지 따로 검토해야 합니다.
