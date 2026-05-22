---
author: "luca"
pubDatetime: 2023-05-18T13:08:25+09:00
title: "application.yml과 build.gradle 설명"
slug: "application-yml-and-build-gradle"
featured: false
draft: false
tags: ["spring-boot", "configuration", "gradle", "yaml"]
description: "Spring Boot 프로젝트의 application.yml 주요 섹션과 build.gradle 의존성을 한 번에 훑는 설정 노트입니다."
---

> Spring Boot 프로젝트 초기 설정에서 자주 사용하는 항목들을 정리하는 글입니다. `application.yml` 값은 학습용 예시입니다.

## application.yml 설정

### Debug 및 Actuator

```yaml
debug: false
management.endpoints.web.exposure.include: "*"
```

전체 디버그를 비활성화하고, `Actuator` 의 모든 엔드포인트를 노출합니다.

### Logging

```yaml
logging:
  level:
    com.fastcampus.springboard: debug
    org.springframework.web.servlet: debug
    org.hibernate.type.descriptor.sql.BasicBinder: trace
```

- 루트 패키지의 모든 로그를 **debug** 레벨로 설정합니다.
- 웹 서블릿 요청·응답을 추적합니다.
- JPA 쿼리의 **바인딩 파라미터** 를 표시합니다.

### DataSource

```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/board
    username: hiyee
    password: ********
    driver-class-name: com.mysql.cj.jdbc.Driver
```

MySQL 데이터베이스 연결을 구성합니다.

### JPA & Hibernate

```yaml
  jpa:
    defer-datasource-initialization: true
    hibernate.ddl-auto: create
    show-sql: true
    properties:
      hibernate.format_sql: true
      hibernate.default_batch_fetch_size: 100
```

Hibernate 가 자동으로 DDL 을 생성하고, SQL 을 포맷팅하며, 배치 페칭을 설정합니다.

### H2 및 기타

```yaml
  h2.console.enabled: false
  sql.init.mode: ALWAYS
  data.rest:
    base-path: /api
    detection-strategy: ANNOTATED
```

### Test 프로필

```yaml
---
spring:
  config.activate.on-profile: testdb
  datasource:
    url: jdbc:h2:mem:board;mode=mysql
    driverClassName: org.h2.Driver
  test.database.replace: none
```

테스트 환경에서는 H2 인메모리 데이터베이스를 **MySQL 호환성 모드** 로 사용합니다.

## build.gradle 의존성

```gradle
dependencies {
  implementation 'org.springframework.boot:spring-boot-starter-actuator'
  implementation 'org.springframework.boot:spring-boot-starter-web'
  implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
  implementation 'org.springframework.boot:spring-boot-starter-data-rest'
  implementation 'org.springframework.data:spring-data-rest-hal-explorer'
  implementation 'org.springframework.boot:spring-boot-starter-thymeleaf'

  runtimeOnly 'com.h2database:h2'
  runtimeOnly 'com.mysql:mysql-connector-j'

  compileOnly 'org.projectlombok:lombok'
  annotationProcessor 'org.projectlombok:lombok'

  developmentOnly 'org.springframework.boot:spring-boot-devtools'
  testImplementation 'org.springframework.boot:spring-boot-starter-test'
}
```

**핵심 라이브러리 요약:**

- **Spring Boot Starter Actuator** — 애플리케이션 상태 관리
- **Spring Data JPA** — 데이터 접근 계층
- **Spring Data REST** — RESTful API 자동 생성
- **Thymeleaf** — 템플릿 엔진
- **Lombok** — 보일러플레이트 코드 제거
- **Spring Boot DevTools** — 자동 재시작 및 라이브 리로드
- **H2 및 MySQL 드라이버** — 데이터베이스 연결
