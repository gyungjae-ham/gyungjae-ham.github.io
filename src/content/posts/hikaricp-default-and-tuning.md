---
author: "luca"
pubDatetime: 2024-12-25T15:29:58+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "HikariCP 풀 크기를 정하기 전에 커넥션 점유 시간을 본다"
slug: "hikaricp-default-and-tuning"
featured: false
draft: false
tags:
  - 학습노트
  - spring-boot
  - hikaricp
  - connection-pool
  - jpa
  - performance
  - mysql
description: "Little’s Law의 평균 점유량과 최대 풀 크기를 구분하고, HikariCP의 획득 대기·유휴 연결·수명 설정을 DB 부하와 함께 확인합니다."
---

DB 쿼리가 느려졌을 때 커넥션 풀을 늘리면 나아질 때도 있고, DB가 더 바빠질 때도 있습니다. 커넥션은 동시에 DB 작업을 수행할 수 있는 통로이기 때문입니다. 이 글에서는 HikariCP의 설정을 외우기보다, 애플리케이션이 커넥션을 얼마나 오래 점유하는지부터 살펴봅니다.

Spring Boot는 HikariCP가 사용 가능하면 기본 풀로 선택합니다. 풀 구현의 대여·반환 비용이 작더라도 느린 SQL이나 긴 트랜잭션까지 해결해 주지는 않습니다.

## 평균 점유량을 먼저 계산한다

Little’s Law의 관계는 `L = λ × W`입니다. 커넥션 점유를 대상으로 잡으면 `λ`는 초당 커넥션 대여 횟수, `W`는 대여부터 반환까지의 **평균 점유 시간**, `L`은 평균 사용 중인 커넥션 수입니다. [MIT의 Little’s Law 설명](https://web.mit.edu/6.02/www/s2012/handouts/16.pdf)

가령 애플리케이션 인스턴스 하나에서 초당 200번 대여하고 평균 0.05초 뒤 반환한다면 평균 점유량은 10개입니다. 이것은 설명용 계산이며, 최대 풀 크기를 반드시 10으로 정하라는 뜻은 아닙니다. 변동과 긴 요청이 있는 환경에서는 대기가 생길 수 있습니다.

여기에는 세 가지 구분이 필요합니다.

- HTTP 요청 수와 커넥션 대여 횟수는 같지 않을 수 있습니다.
- SQL 실행 시간과 커넥션 점유 시간은 다릅니다. 트랜잭션 중 외부 호출을 기다리면 그 시간도 포함될 수 있습니다.
- p99를 평균 대신 넣은 값은 Little’s Law의 평균 점유량이 아닙니다. 여유 용량을 정하기 위한 별도의 가정으로 다뤄야 합니다.

여러 인스턴스의 풀을 합친 연결 수가 DB 한도를 넘지 않는지도 봐야 합니다. 평균 점유량은 출발점이고, 최종 크기는 목표 부하에서 획득 대기와 DB 처리량을 보며 결정합니다.

## 풀 대기와 DB 과부하를 구분한다

사용 중인 연결이 최대치에 붙고 획득 대기가 늘면 풀에서 요청이 기다린다는 뜻입니다. 원인은 연결 누수, 느린 SQL, 긴 트랜잭션, DB의 처리 한계 등으로 나뉩니다. HikariCP의 active·pending·acquire time과 DB의 실행 중인 쿼리·락 대기·CPU를 함께 확인합니다. 지표 이름은 수집기와 내보내기 형식에 따라 달라집니다.

DB가 이미 포화라면 연결을 늘려 더 많은 쿼리를 동시에 실행시키는 것이 악화 요인이 될 수 있습니다. 반대로 DB에 여유가 있고 커넥션 획득 대기만 길다면 풀 크기를 조금씩 바꾸며 비교할 수 있습니다. 유휴 연결이 있다는 사실만으로 풀이 과도하다고 판단하지는 않습니다.

## 유휴 시간과 연결 수명은 다른 설정이다

`connectionTimeout`은 애플리케이션이 연결을 빌리려고 기다리는 시간입니다. `idleTimeout`은 유휴 연결을 줄이는 설정이고, **`minimumIdle < maximumPoolSize`일 때만 적용**됩니다. `minimumIdle`의 기본값은 최대 풀 크기와 같습니다.

`maxLifetime`은 연결의 최대 수명입니다. 사용 중인 연결을 시간이 됐다고 강제로 끊지는 않으며, 반환된 뒤 교체합니다. DB뿐 아니라 프록시·방화벽의 연결 제한도 확인해야 합니다. 특정 부등식 하나로 모든 연결 단절을 예방할 수는 없습니다. [HikariCP 설정 문서](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)

아래 값은 유휴 연결을 줄이는 구성을 설명하기 위한 예시입니다. 운영 권장값으로 복사하기 전에 실제 네트워크와 DB 제한을 확인해야 합니다.

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      minimum-idle: 2
      connection-timeout: 5000
      idle-timeout: 300000
      max-lifetime: 1200000
```

MySQL의 `cachePrepStmts`, `useServerPrepStmts`, `rewriteBatchedStatements`는 JDBC 드라이버 설정입니다. 풀 크기와 별개로 드라이버 버전, SQL 길이, 배치 형태에 맞춰 검토합니다. 모든 INSERT·UPDATE가 같은 방식으로 재작성되거나, 옵션을 켜면 항상 빨라지는 것은 아닙니다.

풀 튜닝의 전후 비교에서는 동일한 요청 부하와 인스턴스 수를 유지합니다. 평균 응답만 줄었는지, 긴 요청의 지연과 DB 부하는 어떤지까지 보면 풀을 늘린 효과와 병목을 다른 곳으로 옮긴 효과를 구분할 수 있습니다.
