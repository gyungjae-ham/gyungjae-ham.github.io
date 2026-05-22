---
author: "luca"
pubDatetime: 2023-05-18T11:58:54+09:00
title: "SpringBoot Actuator"
slug: "springboot-actuator-basics"
featured: false
draft: false
tags: ["spring-boot", "actuator", "monitoring", "health"]
description: "Spring Boot Actuator 의 역할과 endpoint 노출·경로·CORS 설정을 짧게 훑는 학습 노트입니다."
---

> Spring Boot 애플리케이션의 상태를 다루는 `Actuator` 의 기본기를 정리하는 글입니다.

## Spring Boot Actuator

간단히 말하자면 `Spring Boot Application` 의 상태를 관리해 줍니다.

- `Spring Boot Application` 의 상태 정보(`health`, `properties`, `beans`, 구동된 `AutoConfiguration` 목록 등)를 다룰 수 있도록 자동으로 설정합니다.
- 각종 추상화 클래스(`HealthIndicator` 등)를 제공하여, 상태 정보를 변경할 수 있도록 Service 를 제공합니다.

### 노출할 항목 설정

```yaml
# Actuator 감춰져 있는 모든 endpoint 정보 표출하도록 설정
management.endpoints.web.exposure.include: "*"

# health와 metrics 정보만 노출
management.endpoints.web.exposure.include: "health, metrics"
```

### Endpoint 경로 설정

- `management.endpoint.web.base-path` (기본값 `/actuator`)를 수정하여 base-path 를 변경할 수 있습니다.
- `management.endpoint.web.path-mapping.<id>` 값을 수정하여, 특정 id 의 endpoint 의 경로를 수정할 수 있습니다.

### CORS

`spring-boot-actuator` 는 기본적으로 클라우드 환경에서 관리자가 애플리케이션 상태를 확인하기 쉽도록 되어 있습니다. 때문에 필요한 경우 외부 도메인명을 가진 Application 에서 각각 서비스의 상태를 확인하기 위해 정보를 요청할 수 있습니다. 그럴 경우 CORS 를 설정해서 사용할 수 있습니다.

```yaml
management.endpoints.web.cors.allowed-origins: http://other-domain.com
management.endpoints.web.cors.allowed-methods: GET,POST
```

우선 이 기록에서는 `Actuator` 가 무슨 기능을 가지고 있는지 확인해봤습니다. 추후에 기능을 추가하거나 적용할 때 별도로 기록할 예정입니다.
