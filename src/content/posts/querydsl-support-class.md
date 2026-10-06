---
author: "luca"
pubDatetime: 2023-06-18T18:19:12+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "QueryDSL 페이징 지원 클래스를 만들기 전에 나눌 책임"
slug: "querydsl-support-class"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "spring-data-jpa", "java"]
description: "공통화할 수 있는 offset·limit과 조회마다 달라지는 정렬·count를 구분합니다. QueryDSL 4 학습 코드와 5.x의 count API 차이도 정리합니다."
---

여러 Repository에서 QueryDSL 페이징 코드가 반복되면 공통 지원 클래스를 만들고 싶어집니다. 하지만 공통화할 부분과 쿼리마다 달라야 하는 부분을 먼저 나눠야 합니다. offset·limit은 같아도 정렬 가능한 필드와 count의 의미는 다를 수 있습니다.

## 지원 클래스가 대신할 수 있는 것

`JPAQueryFactory`의 제공이나 페이지 제한 적용은 공통화하기 쉽습니다. 반면 조인된 별칭의 정렬, null 순서, 동일 값의 tie-break, 컬렉션 조인 후 count는 각 조회의 정책입니다.

Spring의 `Querydsl.applyPagination`을 감싸는 것만으로 모든 정렬 문제가 해결되지는 않습니다. 원래의 정렬 변환에 다시 위임하고 있기 때문입니다. 공통 클래스가 처리한다고 설명하려면 실제로 어떤 입력 정렬이 어떤 OrderSpecifier로 바뀌는지 보여줘야 합니다.

## 상속 전에 조합으로 시작할 수 있다

Repository가 JPAQueryFactory를 받고, 내용 조회와 count 조회를 직접 만드는 방식으로도 중복이 많지 않을 수 있습니다. [명시적인 페이징 예시](/posts/spring-data-jpa-querydsl-paging/)처럼 먼저 정책을 드러낸 뒤, 여러 조회에서 정말 같은 부분만 함수로 추출합니다.

이 글의 초기 학습 코드는 QueryDSL 4.x의 `fetchCount()`를 사용했습니다. QueryDSL JPA 5.x에서는 이 API가 deprecated이며 복잡한 그룹 조회에는 자동 count 변환의 한계가 있습니다. 새 지원 코드를 만든다면 content와 `Long` count 조회를 별도로 전달하거나, 총 개수가 필요 없는 Slice를 검토합니다.

공통화 이후에도 쿼리 자체의 검증은 남습니다. 같은 정렬값의 여러 행, null, 마지막 페이지, 조인으로 늘어난 행을 데이터로 넣어 봅니다. 추상 클래스가 짧아졌다는 사실보다 호출부에서 조회 정책을 여전히 읽을 수 있는지가 중요합니다.
