---
author: "luca"
pubDatetime: 2023-05-18T13:08:25+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "application.yml과 build.gradle 설명"
slug: "application-yml-and-build-gradle"
featured: false
draft: false
tags: ["학습노트", "spring-boot", "configuration", "gradle", "yaml"]
description: "Spring Boot 프로젝트의 application.yml 주요 섹션과 build.gradle 의존성을 한 번에 훑는 설정 노트입니다."
---

Spring Boot 프로젝트를 시작할 때 `build.gradle`은 사용할 라이브러리를 정하고, `application.yml`은 실행 시 설정을 정합니다. 여기서는 **Spring Boot 3.x·Hibernate 6·Java 17**을 기준으로 JPA 학습 프로젝트의 두 파일을 연결해 봅니다.

## 실행 설정은 하나의 트리로 읽는다

아래는 로컬 학습용 예시입니다. `datasource`, `jpa`, `sql`은 모두 `spring` 아래에 있어야 합니다. 따로 떼어 쓴 `jpa:`를 루트에 붙이면 Spring Boot의 JPA 설정으로 적용되지 않습니다.

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/board
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        format_sql: true
        default_batch_fetch_size: 100
  sql:
    init:
      mode: never
management:
  endpoints:
    web:
      exposure:
        include: health
logging:
  level:
    org.hibernate.SQL: debug
```

비밀번호를 `********`로 쓰면 YAML에서 alias 표기로 해석될 수 있습니다. 실제 비밀은 파일에 적지 않고 환경별 설정으로 전달합니다. `ddl-auto: validate`는 스키마를 생성하지 않으므로 먼저 테이블을 준비해야 합니다. `create`는 시작할 때 기존 스키마를 지울 수 있어 폐기 가능한 학습 DB에서만 선택합니다.

SQL 바인딩 로그가 필요하면 Hibernate 6의 `org.hibernate.orm.jdbc.bind`를 사용합니다. Hibernate 5의 `org.hibernate.type.descriptor.sql.BasicBinder`와 구분합니다. 바인딩 값에는 개인정보도 포함될 수 있어 상시 trace 로그로 켜두지 않습니다.

## 의존성이 있어야 설정도 의미가 있다

Spring Boot 플러그인과 의존성 버전 관리가 적용된 Gradle 프로젝트에서 필요한 의존성만 추가합니다.

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    runtimeOnly 'com.mysql:mysql-connector-j'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
    testRuntimeOnly 'com.h2database:h2'
}
```

Thymeleaf는 서버에서 HTML을 만들 때, Data REST는 Repository 기반 HTTP 리소스를 노출할 때 추가합니다. 모든 프로젝트에 함께 넣을 필요는 없습니다.

테스트 프로필에서 H2를 사용한다면 `src/test/resources/application-test.yml`처럼 별도 설정을 두고 `@ActiveProfiles("test")`로 활성화할 수 있습니다. H2의 MySQL 모드는 MySQL 전체 동작을 재현하지 않습니다. 실제 방언·인덱스·락 동작을 검증할 때는 사용하는 MySQL 버전의 테스트 DB가 필요합니다.

설정 적용 여부는 애플리케이션이 시작됐다는 사실만으로 판단하지 않습니다. 연결한 DB, 생성 SQL, 관리 endpoint의 실제 응답을 확인합니다. 관련 경로 설정은 [Actuator 기본 설정](/posts/springboot-actuator-basics/)에서 이어집니다.
