---
author: "luca"
pubDatetime: 2023-05-18T11:58:54+09:00
modDatetime: 2026-10-13T15:37:14+09:00
title: "Spring Boot Actuator로 상태 확인 API 열기"
slug: "springboot-actuator-basics"
featured: false
draft: false
tags: ["학습노트", "spring-boot", "actuator", "monitoring", "health"]
description: "로드밸런서의 상태 확인과 운영 지표 조회에 Actuator를 사용할 수 있습니다. 경로를 노출하는 설정과 접근 권한 설정의 차이를 예제로 확인합니다."
---

서버 프로세스가 떠 있다는 사실만으로 요청을 정상 처리할 수 있는지는 알기 어렵습니다. 로드밸런서가 상태를 확인할 API가 필요하고, 운영 중에는 메모리나 DB 커넥션 풀 지표도 확인해야 합니다. Spring Boot에서는 Actuator로 이런 관리 기능을 제공할 수 있습니다.

아래는 Spring Boot 3.x에서 HTTP로 health와 metrics를 열어 보는 예시입니다. Actuator는 JMX도 지원하지만 여기서는 웹 경로 설정에 집중합니다.

## 필요한 endpoint와 URL 지정하기

의존성에 `spring-boot-starter-actuator`를 추가한 뒤 필요한 endpoint를 노출합니다. 다음 설정은 health와 metrics를 열고, health의 URL을 `/manage/ready`로 바꿉니다. 이름을 ready로 바꾸는 것만으로 readiness 전용 검사 정책이 생기는 것은 아닙니다.

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

## 관리 화면에서 접근하는 경우

예를 들어 관리 화면은 `https://admin.example.com`, API는 다른 출처에서 제공한다고 해보겠습니다. 브라우저에서 Actuator를 호출해야 한다면 Actuator용 CORS를 설정할 수 있습니다.

```yaml
management:
  endpoints:
    web:
      cors:
        allowed-origins: https://admin.example.com
        allowed-methods: GET
```

이 설정은 지정한 출처의 브라우저 요청을 허용하는 정책입니다. 관리 API에 로그인하지 않은 사람이 접근하는 것까지 막아 주지는 않습니다. 관리 화면에서 GET이 성공하는지 확인한 뒤, 자격 증명 없는 직접 요청은 의도대로 거절되는지도 확인해야 합니다.
