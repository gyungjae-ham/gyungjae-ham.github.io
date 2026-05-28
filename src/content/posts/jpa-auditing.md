---
author: "luca"
pubDatetime: 2023-05-18T11:45:46+09:00
title: "JPA Auditing"
slug: "jpa-auditing"
featured: false
draft: false
tags: ["jpa", "auditing", "spring-data-jpa", "entity"]
description: "Spring Data JPA 의 Auditing 기능으로 생성·수정 일시와 작성자를 자동으로 채우는 설정을 정리합니다."
---

> Entity 에 반복되는 생성·수정 메타 필드를 자동으로 채우는 JPA Auditing 설정을 정리하는 글입니다.

## 개요

Java 의 ORM 기술인 JPA 를 사용하여 도메인(엔티티)을 관계형 데이터베이스 테이블에 매핑할 때, **생성일자, 생성자, 수정일자, 수정자** 등의 공통 필드가 반복적으로 나타납니다.

> "Audit 은 감시하다, 감사하다 라는 뜻으로 Spring Data JPA 에서 시간에 대해서 자동으로 값을 넣어주는 기능" 입니다.

엔티티를 영속성 컨텍스트에 저장하거나 업데이트할 때 시간 데이터를 자동으로 매핑합니다.

## 설정 방법

### JpaConfig 클래스 구성

```java
package com.fastcampus.springboard.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.AuditorAware;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

import java.util.Optional;

@EnableJpaAuditing // JPA Auditing 기능 활성화
@Configuration
public class JpaConfig {

    @Bean
    public AuditorAware<String> auditorAware() {
        return () -> Optional.of("hiyeeluca");
    }
}
```

현재 `@Bean` 은 Spring Boot Security 가 적용되지 않은 상태에서 임의로 모든 수정자의 이름을 지정한 것입니다.

### Entity 클래스에 애노테이션 적용

```java
@CreatedDate
private LocalDateTime createdAt; // 생성일시

@CreatedBy
private String createdBy; // 생성자

@LastModifiedDate
private LocalDateTime modifiedAt; // 수정일시

@LastModifiedBy
private String modifiedBy; // 수정자
```

Entity 클래스 위에는 다음을 표시해야 합니다.

```java
@EntityListeners(AuditingEntityListener.class)
```

이 애노테이션이 있어야 해당 클래스에서 Auditing 기능이 동작합니다.

> 참고: Spring Boot Security 가 적용되면 `auditorAware` 의 반환값은 `SecurityContextHolder` 에서 가져온 인증 정보로 대체합니다.
