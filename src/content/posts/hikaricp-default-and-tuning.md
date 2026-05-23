---
author: "luca"
pubDatetime: 2024-12-25T15:29:58+09:00
modDatetime: 2026-05-23T00:00:00+09:00
title: "왜 기본으로 HikariCP 를 선택하는가 — 그리고 풀 크기는 옵션 표가 아니라 Little's Law 에서 나옵니다"
slug: "hikaricp-default-and-tuning"
featured: false
draft: false
tags:
  - spring-boot
  - hikaricp
  - connection-pool
  - jpa
  - performance
  - mysql
description: "Spring Boot 가 HikariCP 를 기본 선택하는 이유와, 자주 따라 쓰던 (CPU × 2) + 디스크 룰이 어디서 흔들리는지. Little's Law 로 풀 크기 추정하기 · Micrometer 지표로 풀 모자람·과잉 신호 읽기 · idleTimeout 과 DB wait_timeout 의 짝까지 5~6년차 시각으로 다시 정리합니다."
---

> Spring 공식 문서는 데이터 소스 선택을 네 단계로 정리합니다.
>
> 1. 성능과 동시성 면에서 HikariCP 를 선호한다. HikariCP 를 사용할 수 있다면 항상 HikariCP 를 선택한다.
> 2. HikariCP 를 사용할 수 없다면 Tomcat pooling DataSource 를 선택한다.
> 3. 그렇지 않다면 Commons DBCP2 를 사용한다.
> 4. 이마저도 사용할 수 없다면 Oracle UCP 를 사용한다.

2024-12 에 정리한 tistory 글을 다시 손봅니다. 그때는 "옵션 권장값 표를 외워두자" 가 결론이었는데, 지금 다시 들여다보면 같은 자리에서 묻는 질문이 바뀌어 있습니다. `maximum-pool-size = (CPU × 2) + 디스크 스핀들` 같은 룰을 적어두는 것보다, **내 서비스의 query latency × 동시 요청 수** 를 곱해 보는 게 먼저 와야 했다는 게 운영을 거치고 보면 분명합니다. 풀 크기는 옵션 표가 아니라 측정에서 나오고, 측정의 출발점은 Little's Law 입니다.

## 풀 크기는 Little's Law 로 시작합니다

옛 글에는 `(CPU 코어 수 × 2) + 디스크` 룰을 그대로 옮겨 적었는데, 이 룰은 DB 서버의 처지에서 본 상한입니다. 애플리케이션 처지에서는 **Little's Law** 가 출발점입니다.

> 필요 풀 크기 ≈ 동시 요청 수 × query latency (초)

예를 들어 query p99 가 50ms 인 API 에 초당 200 RPS 가 들어오면, 200 × 0.05 = 10 으로 풀 10 개가 출발점입니다. 같은 200 RPS 라도 query p99 가 500ms 면 200 × 0.5 = 100 으로 필요한 풀이 자릿수 단위로 늘어납니다. 동시 요청은 같은데 query 가 한 커넥션을 얼마나 오래 잡고 있는가가 결정의 진짜 변수입니다.

여기서 한 번 더 들여다보면 풀을 너무 크게 잡는 것도 비용입니다. 동시 요청이 100 인데 풀을 100 개로 잡아 두면, DB 측 메모리·컨텍스트가 그만큼 묶입니다. DB 는 한가한데 풀만 부풀어 있는 상태가 됩니다. **풀이 모자라는 것만큼 풀이 큰 것도 사고의 자리** 라는 게 운영의 결입니다.

## 풀이 모자라거나 너무 클 때 나오는 신호

풀이 모자랄 때와 너무 클 때 보이는 증상은 결이 다릅니다. 두 자리 모두 Micrometer 의 HikariCP 지표에서 떠오릅니다.

- **`hikaricp_connections_active`** — 현재 사용 중인 커넥션 수
- **`hikaricp_connections_pending`** — 커넥션을 기다리는 스레드 수
- **`hikaricp_connections_acquire_seconds`** — 커넥션을 받기까지 걸린 시간 분포

풀이 모자란 자리의 신호는 명확합니다. `active` 가 max 에 붙고 `pending` 이 0 이 아닌 채로 지속됩니다. 그러고는 `SQLTransientConnectionException: HikariPool-1 - Connection is not available, request timed out after 5000ms` 가 로그에 떨어집니다. 이때 풀 크기를 키워서 증상은 가라앉아도, **`active` 가 풀에 머무는 시간이 왜 긴가** 를 묻지 않으면 같은 사고가 다음 spike 에서 다시 옵니다.

반대로 풀이 너무 큰 자리의 신호는 DB 쪽에서 옵니다. `SHOW PROCESSLIST` 나 `pg_stat_activity` 로 보면 활성 세션은 적은데 idle 세션이 풀 max 만큼 떠 있고, DB 의 CPU·메모리가 idle 세션의 컨텍스트 유지 비용으로 야금야금 올라갑니다. 풀 크기는 DB 와 애플리케이션 양쪽 지표를 같이 보는 자리라는 사실이 여기서 명확해집니다.

## HikariCP 가 빠른 진짜 이유

권장값을 외우기 전에 왜 HikariCP 가 자릿수 단위로 빠른가를 한 번 짚고 가야 옵션의 결이 보입니다. 핵심은 한 줄로 "JVM 과 CPU 가 좋아하는 모양으로 줄여놓았다" 입니다.

- **바이트코드 수준 최적화** — 핵심 루틴을 JIT 인라인 임계값 이하로 유지해 메서드 호출 오버헤드 제거
- **`FastList` 자료구조** — `ArrayList` 의 범위 체크를 제거하고 제거 스캔 방향을 head → tail 로 고정
- **캐시 라인 의식** — L1·L2 캐시에 머무를 수 있도록 명령어 수 최소화. 컨텍스트 스위치 후의 캐시 미스 비용까지 의식
- **`ConcurrentBag`** — 커넥션 대여·반환 경로를 락 경합 최소화하도록 재설계한 자체 자료구조

그 결을 압축하면 HikariCP 는 대여·반환의 hot path 가 CPU 캐시 안에서 끝나도록 잡혀 있는 풀입니다. 옵션을 만지기 전에 이 사실을 기억해 두면, "옵션 하나로 자릿수 단위 개선" 같은 기대를 부풀리지 않게 됩니다. 큰 이득은 이미 라이브러리 기본값이 가져가 두었습니다.

## MySQL 옵션은 표 하나로 압축합니다

MySQL 을 쓸 때 HikariCP 의 `data-source-properties` 에 자주 얹는 옵션을 한 표로 압축합니다. 권장값은 출발점일 뿐이고, 옆 칸의 함정을 같이 보는 게 본 의도입니다.

| 옵션 | 권장값 | 효과 · 함정 |
|---|---|---|
| `cachePrepStmts` | `true` | PreparedStatement 캐싱 활성화. 이게 `false` 면 아래 캐시 옵션이 전부 무시 |
| `prepStmtCacheSize` | 250 | 커넥션당 캐시할 Statement 수. 기본 25 는 ORM 환경에 너무 작음 |
| `prepStmtCacheSqlLimit` | 2048 | 캐시할 SQL 길이 상한. 기본 256 이면 Hibernate 쿼리 대부분이 캐시 미스 |
| `useServerPrepStmts` | `true` | 서버 측 PreparedStatement. 템플릿은 서버에 두고 파라미터만 전송 |
| `rewriteBatchedStatements` | `true` | 배치 INSERT/UPDATE 를 단일 멀티 row 구문으로 재작성 |

이 다섯 개가 MySQL + HikariCP 조합에서 거의 항상 켜두는 옵션입니다. PostgreSQL 도 같은 결로 `max_connections`·`idle_in_transaction_session_timeout` 을 함께 손봅니다. DB 서버 측 설정과 풀 옵션은 늘 짝으로 움직입니다.

## idleTimeout · maxLifetime — DB 쪽 타임아웃과의 짝

풀 크기 못지않게 자주 사고가 나는 자리가 커넥션 수명의 짝 설정입니다. 가장 자주 보는 사고는 `idleTimeout` 또는 `maxLifetime` 이 **DB 쪽 `wait_timeout` 보다 길게 잡혀 있는** 경우입니다. MySQL 의 기본 `wait_timeout` 은 8 시간이고 AWS RDS default parameter group 도 같은 값이지만, L4 로드밸런서나 방화벽이 중간에 끼면 idle TCP 세션을 350 초쯤에 끊어 버리는 경우도 있습니다.

이 짝이 어긋나면 풀은 커넥션이 살아 있다고 믿고 빌려주는데 실제로는 DB 쪽에서 이미 끊긴 좀비 커넥션입니다. 첫 쿼리에서 `CommunicationsException` 이나 `Connection has been closed` 가 떨어지고, 그 사고가 매일 새벽 같은 시간대에 반복되는 패턴이 보입니다. **`idleTimeout` < `maxLifetime` < DB 쪽 `wait_timeout`** 한 줄 룰로 이 사고는 거의 다 막힙니다.

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      connection-timeout: 5000
      idle-timeout: 300000      # 5분
      max-lifetime: 1200000     # 20분, DB wait_timeout 보다 짧게
      data-source-properties:
        cachePrepStmts: true
        prepStmtCacheSize: 250
        prepStmtCacheSqlLimit: 2048
        useServerPrepStmts: true
        rewriteBatchedStatements: true
```

이 yaml 도 정답이 아니라 출발점입니다. `maximum-pool-size: 10` 이라는 숫자는 "Little's Law 로 추정한 첫 값을 두고, 부하 테스트에서 `hikaricp_connections_pending` 과 DB active connection 을 같이 보겠다" 라는 선언입니다.

## 같은 결의 다른 풀들

HikariCP 의 결정 트리는 다른 connection pool 에도 같은 결로 적용됩니다. DBCP2·Tomcat JDBC·c3p0 어느 쪽을 쓰든 Little's Law 로 풀 크기 추정, 풀 모자람·과잉 양쪽 신호, 수명 타임아웃의 짝이라는 흐름은 동일합니다. Tomcat JDBC 는 `maxActive`·`maxWait`·`removeAbandonedTimeout`, DBCP2 는 `maxTotal`·`maxWaitMillis`·`softMinEvictableIdleTimeMillis` — 옵션 이름만 바뀝니다. HikariCP 를 고르는 건 핫 패스가 캐시 친화적이기 때문이지만, **어떤 풀을 골랐든 풀 크기와 수명을 결정하는 자리의 사고는 같다** 는 게 본 글의 결입니다.

## 정리

`maximum-pool-size` 한 줄을 적기 전에 query p99 와 동시 요청 수를 곱해 봐야 합니다. 그 추정값을 출발점으로 두고 `hikaricp_connections_active`·`pending` 과 DB 의 active connection 양쪽을 보면서 조정하는 게 본 작업의 결이고, `idleTimeout` < `maxLifetime` < DB `wait_timeout` 의 짝까지 묶어두면 새벽 좀비 커넥션 사고는 거의 안 납니다. DB 는 한가한데 서비스만 느려진다면 그건 풀이 모자라거나 너무 길게 잡혀 있다는 신호이고, 옵션 표를 외우는 것보다 양쪽 지표를 같이 보는 것 — 그게 풀 크기 결정의 마지막 결재자가 측정이라는 사실의 진짜 의미입니다.
