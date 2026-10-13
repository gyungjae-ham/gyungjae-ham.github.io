---
author: "luca"
pubDatetime: 2023-05-18T13:08:25+09:00
modDatetime: 2026-10-13T15:42:49+09:00
title: "Spring Boot의 Gradle 의존성과 YAML 설정 연결하기"
slug: "application-yml-and-build-gradle"
featured: false
draft: false
tags: ["학습노트", "spring-boot", "configuration", "gradle", "yaml"]
description: "JPA 의존성을 추가하는 일과 DB 연결 정보를 정하는 일은 서로 다릅니다. 로컬 MySQL 프로젝트를 예로 두 설정 파일의 역할을 살펴봅니다."
---

Spring Boot에서 MySQL을 사용하려면 드라이버를 추가하는 것만으로는 부족합니다. 어느 DB에 연결할지 주소와 계정도 필요합니다. 반대로 YAML에 DB 주소를 적어 두어도 드라이버와 JPA 관련 라이브러리가 준비돼 있지 않으면 원하는 구성이 만들어지지 않습니다.

`build.gradle`은 빌드와 의존성을, `application.yml`은 실행 시 설정을 담당합니다. **Spring Boot 3.x·Hibernate 6·Java 17**의 JPA 학습 프로젝트를 예로 두 파일을 연결해 보겠습니다.

## YAML에서는 들여쓰기도 설정의 일부다

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

이 예시를 실행할 때는 MySQL에 board DB와 필요한 테이블을 먼저 준비하고, DB_USERNAME과 DB_PASSWORD를 전달해야 합니다. 시작 후에는 실제로 연결한 DB와 생성 SQL을 확인합니다. 설정 파일을 읽었다고 기대한 값이 적용됐다고 보기는 어렵기 때문입니다. 관리 경로 확인은 [Actuator 기본 설정](/posts/springboot-actuator-basics/)에서 이어집니다.
