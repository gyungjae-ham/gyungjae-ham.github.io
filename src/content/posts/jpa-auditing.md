---
author: "luca"
pubDatetime: 2023-05-18T11:45:46+09:00
modDatetime: 2026-10-13T15:48:40+09:00
title: "JPA Auditing으로 작성·수정 정보 기록하기"
slug: "jpa-auditing"
featured: false
draft: false
tags: ["학습노트", "jpa", "auditing", "spring-data-jpa", "entity"]
description: "게시글을 저장하는 경로마다 날짜를 넣지 않으려면 Auditing을 사용할 수 있습니다. 설정을 연결하고 자동 갱신되지 않는 벌크 수정도 구분합니다."
---

게시글의 작성·수정 시각을 각 서비스 메서드에서 채우면, 새 저장 경로를 추가할 때 빠뜨리기 쉽습니다. Spring Data JPA의 Auditing은 엔티티 생명주기 이벤트에서 이 값을 채웁니다. 아래는 Spring Data JPA 3.x 기준 설정 노트입니다.

## 기록할 작업 주체 제공하기

```java
@Configuration
@EnableJpaAuditing
class JpaConfig {
    @Bean
    AuditorAware<String> auditorAware() {
        return () -> Optional.of("example-user");
    }
}
```

이 예제는 설정의 관계만 보여주며 imports는 생략했습니다. `AuditorAware`의 고정 문자열은 학습용입니다. 실제 서비스에서는 인증된 사용자나 배치 실행 주체를 반환하도록 구현합니다. 시간만 기록한다면 `AuditorAware`는 필요하지 않습니다.

## 엔티티의 변경 시점에 필드 채우기

공통 필드를 부모 클래스에 모으는 예는 다음과 같습니다. `@MappedSuperclass`는 별도 테이블을 만들지 않고 자식 엔티티에 매핑 정보를 전달합니다.

```java
@MappedSuperclass
@EntityListeners(AuditingEntityListener.class)
abstract class AuditedEntity {
    @CreatedDate
    @Column(updatable = false)
    private Instant createdAt;

    @LastModifiedDate
    private Instant modifiedAt;

    @CreatedBy
    @Column(updatable = false)
    private String createdBy;

    @LastModifiedBy
    private String modifiedBy;
}
```

예를 들어 A가 글을 생성하고 나중에 B가 제목을 바꾸면, 생성자·생성 시각은 유지되고 수정자·수정 시각이 B의 변경에 맞춰 갱신되어야 합니다. 기본 설정은 최초 생성 때 수정 필드도 채웁니다. 변경 검증에서는 엔티티를 수정한 뒤 `flush()`하여 콜백을 발생시키고, `clear()` 후 다시 조회해 DB에 저장된 값을 확인할 수 있습니다. flush는 commit과 다르므로 테스트 종료 시 rollback될 수 있습니다.

## 벌크 수정에서도 자동으로 바뀔까

예를 들어 게시글 1,000개의 상태를 JPQL UPDATE 한 번으로 바꾸면, 각 엔티티를 읽어 수정하는 과정을 거치지 않습니다. Auditing은 모든 SQL을 감시하는 기능이 아니므로 이 경로에서는 수정 시각이 기대처럼 채워지지 않을 수 있습니다. DB에서 직접 실행한 UPDATE도 마찬가지입니다. 이런 작업은 쿼리에 수정 시각을 포함하는 등 별도 정책이 필요합니다.

일반 엔티티 수정 테스트에서는 변경 전후의 시간이 맞는지 확인할 수 있습니다. 실제 시계에 의존하지 않게 하려면 `DateTimeProvider`로 시간을 제공하는 방법이 있습니다.

설정 조건과 지원 애노테이션은 [Spring Data JPA Auditing 문서](https://docs.spring.io/spring-data/jpa/reference/auditing.html)를 참고했습니다.
