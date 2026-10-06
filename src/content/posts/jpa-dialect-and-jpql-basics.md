---
author: "luca"
pubDatetime: 2023-05-19T19:35:14+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "JPA 방언과 JPQL: 같은 조회가 DB별 SQL로 바뀌는 과정"
slug: "jpa-dialect-and-jpql-basics"
featured: false
draft: false
tags: ["학습노트", "jpa", "dialect", "jpql", "hibernate"]
description: "데이터베이스 방언이 필요한 이유와 JPA 구동 방식, JPQL 이 SQL 과 다른 지점을 정리한 학습 노트입니다."
---

김영한님의 JPA 로드맵을 따라 학습하면서 정리한 노트입니다. JPA는 엔티티를 대상으로 코드를 작성하게 하지만, 실제 저장과 조회에는 DB가 이해하는 SQL이 필요합니다. 그 사이를 Hibernate 같은 구현체와 데이터베이스 방언(Dialect)이 연결합니다.

## 같은 페이징 요청이 다른 SQL이 되는 이유

JPQL에서 회원을 ID순으로 조회한 뒤 `setFirstResult(20)`과 `setMaxResults(10)`을 적용하면, 앞의 20건을 건너뛴 최대 10건을 요청한다는 뜻입니다. 구현체는 선택한 DB와 버전에 맞춰 이 제한을 SQL로 표현합니다.

MySQL의 LIMIT, 과거 Oracle에서 쓰던 ROWNUM 기반 쿼리는 모양이 다릅니다. Oracle 12c 이후에는 OFFSET/FETCH 구문도 지원합니다. 따라서 “Oracle은 항상 ROWNUM으로 페이징한다”는 설명은 버전과 방언을 빠뜨린 것입니다. Hibernate 6은 지원 DB의 메타데이터로 방언을 추론할 수 있으므로 모든 애플리케이션에 `hibernate.dialect`를 직접 넣을 필요도 없습니다.

이 추상화가 DB 간 동작을 모두 같게 만들지는 않습니다. 타입, 잠금, 함수, 실행 계획은 실제 DB에서 확인해야 합니다.

## EntityManager의 수명은 누가 관리하는가

직접 JPA를 구동하면 `Persistence`로 `EntityManagerFactory`를 만들고, 여기서 `EntityManager`를 생성합니다. Factory는 공유하고 재사용할 수 있지만 EntityManager 자체는 여러 스레드가 동시에 공유해서 쓰는 객체가 아닙니다.

EntityManager를 반드시 HTTP 요청마다 만든다는 규칙은 없습니다. 애플리케이션이 직접 수명을 정할 수도 있고, Spring에서는 주입된 프록시가 트랜잭션 등에 연결된 EntityManager로 호출을 위임합니다. 요청과 트랜잭션의 경계는 설정에 따라 다릅니다.

관리 중인 엔티티의 필드를 바꾸면 flush 때 변경을 감지해 UPDATE를 실행할 수 있습니다. flush는 commit 직전뿐 아니라 명시적 호출이나 쿼리 실행 전에 일어날 수 있으며, SQL 실행 후에도 트랜잭션이 rollback될 수 있습니다.

## JPQL은 테이블 대신 엔티티 이름을 쓴다

```java
List<Member> members = em.createQuery(
        "select m from Member m where m.age >= :age order by m.id", Member.class)
    .setParameter("age", 20)
    .setFirstResult(20)
    .setMaxResults(10)
    .getResultList();
```

`Member`와 `age`는 엔티티와 속성 이름입니다. 위 코드는 매핑된 Member가 있다는 전제의 조회 예시이며, 실제 테이블·컬럼 이름은 매핑과 방언을 통해 SQL에 반영됩니다. ID 정렬은 같은 조건으로 페이지를 읽을 때 순서를 명확하게 해 주지만, 페이지 사이에 데이터가 추가·삭제되는 문제까지 해결하지는 않습니다.

다음 노트인 [JPQL 조회와 벌크 연산](/posts/jpql-introduction/)에서 결과 타입과 조회 방법을 다룹니다. 방언과 영속성 컨텍스트 설명은 [Hibernate 6.6 문서](https://docs.jboss.org/hibernate/orm/6.6/userguide/html_single/Hibernate_User_Guide.html)를 기준으로 보완했습니다.
