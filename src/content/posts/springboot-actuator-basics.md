---
author: "luca"
pubDatetime: 2023-05-18T11:58:54+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "SpringBoot Actuator"
slug: "springboot-actuator-basics"
featured: false
draft: false
tags: ["학습노트", "spring-boot", "actuator", "monitoring", "health"]
description: "Spring Boot Actuator 의 역할과 endpoint 노출·경로·CORS 설정을 짧게 훑는 학습 노트입니다."
---

Actuator는 Spring Boot 애플리케이션의 상태와 지표를 HTTP나 JMX로 확인하게 해 줍니다. 예를 들어 로드밸런서는 health 응답을 확인하고, 운영자는 metrics로 요청·메모리·커넥션 풀 상태를 살펴볼 수 있습니다. 이 글은 Spring Boot 3.x의 HTTP 설정을 기준으로 합니다.

의존성에 `spring-boot-starter-actuator`를 추가한 뒤 필요한 endpoint만 노출합니다. 다음은 health와 metrics를 열고, health의 경로를 `/manage/ready`로 바꾸는 예시입니다.

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,metrics
      base-path: /manage
      path-mapping:
        health: ready
```

공통 웹 설정은 `management.endpoints.web`처럼 **endpoints가 복수형**입니다. 개별 endpoint의 설정인 `management.endpoint.health`와 구분합니다. 서버를 시작한 뒤 `/manage/ready`와 `/manage/metrics`가 의도한 인증 조건에서 응답하는지 확인합니다. [Actuator HTTP API](https://docs.spring.io/spring-boot/api/rest/actuator/)

`include: "*"`는 모든 endpoint를 노출하는 설정입니다. 상태 확인만 필요한 서비스라면 위 예시처럼 범위를 좁히고, 노출 여부와 접근 권한을 별도로 설정합니다. 특히 자체 `SecurityFilterChain`을 등록했다면 관리 경로가 어떻게 보호되는지 확인해야 합니다.

다른 출처의 관리 화면에서 호출해야 한다면 Actuator용 CORS를 설정할 수 있습니다.

```yaml
management:
  endpoints:
    web:
      cors:
        allowed-origins: https://admin.example.com
        allowed-methods: GET
```

CORS는 브라우저의 교차 출처 접근 정책입니다. 인증이나 네트워크 접근 제한을 대신하지 않으므로, 관리 화면에서 호출이 된다는 사실과 권한 없는 요청이 거부된다는 사실을 각각 확인합니다.
