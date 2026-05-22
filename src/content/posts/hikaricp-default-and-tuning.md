---
author: "luca"
pubDatetime: 2024-12-25T15:29:58+09:00
modDatetime: 2026-05-23T00:00:00+09:00
title: "왜 기본으로 HikariCP 를 선택하는가 — 그리고 운영 옵션은 옵션 표가 아니라 측정에서 나옵니다"
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
description: "Spring Boot 가 HikariCP 를 기본 선택하는 이유와, 자주 따라 쓰던 권장값들이 어디서 흔들리는지. 풀 크기와 옵션은 룰이 아니라 측정에서 결정한다는 시각으로 다시 정리합니다."
---

> Spring 공식 문서는 데이터 소스 선택을 네 단계로 정리합니다.
>
> 1. 성능과 동시성 면에서 HikariCP 를 선호한다. HikariCP 를 사용할 수 있다면 항상 HikariCP 를 선택한다.
> 2. HikariCP 를 사용할 수 없다면 Tomcat pooling DataSource 를 선택한다.
> 3. 그렇지 않다면 Commons DBCP2 를 사용한다.
> 4. 이마저도 사용할 수 없다면 Oracle UCP 를 사용한다.
>
> 그때는 "HikariCP 의 옵션 권장값 표를 외워두자" 정도로 끝났습니다. 지금은 `maximum-pool-size = (CPU × 2) + 디스크` 같은 룰보다, *내 서비스의 query latency × 동시 요청* 을 곱한 추정이 먼저 라고 봅니다. 풀 크기 결정은 옵션 표가 아니라 측정에서 나옵니다.

## 커넥션 풀이 왜 필요한가

JDBC 로 DB 에 직접 연결할 때마다 만들어지는 단계는 짧지 않습니다. 매 요청마다 이걸 반복하면 응답 시간의 상당량이 연결 셋업에만 쓰입니다.

- TCP/IP 3-way handshake 로 소켓을 엽니다.
- 드라이버가 ID · PW · 부가 정보를 전송합니다.
- DB 가 인증을 끝내고 내부 세션을 만듭니다.
- 커넥션 객체가 반환됩니다.

커넥션 풀은 이 과정을 미리 끝내두고 객체만 빌려 줍니다. 그래서 풀의 가치는 "물리 커넥션의 생성 비용을 요청 경로 밖으로 빼낸다" 한 줄로 압축됩니다.

## HikariCP 가 빠른 이유

HikariCP 의 벤치마크에서 두 번째 자리(Vibur)와의 격차는 자릿수 단위입니다. 비결을 한 줄로 줄이기 어렵지만, 핵심은 "JVM 과 CPU 가 좋아하는 모양으로 줄여놓았다" 입니다.

- **바이트코드 수준 최적화** — 핵심 루틴을 JIT 인라인 임계값 이하로 유지해 메서드 호출 오버헤드를 제거.
- **`FastList` 자료구조** — `ArrayList` 의 범위 체크를 제거하고, 제거 스캔 방향을 head → tail 로 고정.
- **캐시 친화적 설계** — L1 · L2 캐시에 머무를 수 있도록 명령어 수를 최소화. 컨텍스트 스위치 이후 캐시 미스 비용까지 의식한 설계.
- **`ConcurrentBag`** — 커넥션 대여 · 반환 경로를 락 경합 최소화하도록 재설계.

결과적으로 "수백만 번 호출돼도 밀리초 단위" 라는 표현이 과장이 아닌 모양이 됩니다.

## MySQL 운영 옵션 — 권장값과 함정

MySQL 을 쓸 때 HikariCP 의 `data-source-properties` 에 자주 얹는 옵션을 표로 정리합니다. 권장값은 출발점일 뿐이고, 옆 칸의 "함정" 을 같이 봐야 합니다.

| 옵션 | 권장값 | 효과 | 함정 |
|---|---|---|---|
| `cachePrepStmts` | `true` | JDBC 드라이버 측 PreparedStatement 캐싱 활성화. 이게 `false` 면 아래 캐시 옵션이 전부 무시. | 켜는 게 거의 정답. |
| `prepStmtCacheSize` | 250 | 커넥션당 캐시할 Statement 수. 기본 25 는 ORM 환경에 너무 작음. | 너무 크면 메모리 점유 상승. |
| `prepStmtCacheSqlLimit` | 2048 | 캐시할 SQL 길이 상한. Hibernate 가 생성하는 긴 SQL 을 담으려면 필수. | 기본 256 으로 두면 ORM 쿼리 대부분이 캐시 미스. |
| `useServerPrepStmts` | `true` | 서버 측 PreparedStatement 사용. 템플릿을 서버에 두고 파라미터만 전송. 네트워크 · CPU 모두 이득. | 구버전 MySQL 호환 이슈 있는 환경에서만 확인. |
| `useLocalSessionState` | `true` | 세션 상태를 로컬에서 추적해 불필요한 서버 round-trip 제거. | 트랜잭션 격리 변경을 자주 하는 코드는 동작 차이 확인 필요. |
| `rewriteBatchedStatements` | `true` | 배치 INSERT/UPDATE 를 단일 멀티 row 구문으로 재작성. 배치 성능이 자릿수 단위로 향상. | JDBC URL 에도 함께 켜야 효과가 일관됨. |
| `cacheResultSetMetadata` | `true` | ResultSet 메타데이터 캐싱. 반복 쿼리에서 이득. | 스키마가 자주 바뀌는 환경은 검증 필요. |
| `cacheServerConfiguration` | `true` | 커넥션 초기화 시 서버 설정 조회 횟수 감소. | DB 설정 핫리로드를 자주 하는 환경은 주의. |
| `elideSetAutoCommits` | `true` | 불필요한 `setAutoCommit` 호출 제거. | 거의 항상 켜도 안전. |
| `maintainTimeStats` | `false` 권장이라지만 — | 시간 측정 오버헤드 제거. | **끄기 전에 두 번 더 생각.** 풀 동작 모니터링이 어두워지므로, 모니터링 인프라가 따로 잘 갖춰진 경우에만. |

PostgreSQL 도 같은 결로 `max_connections` · `idle_in_transaction_session_timeout` 을 함께 손봅니다. DB 서버 측 설정과 풀 옵션은 짝으로 움직여야 합니다.

## 풀 크기는 룰이 아니라 측정

옛 글에는 `maximum-pool-size = (CPU 코어 수 × 2) + 디스크 스핀들 수` 를 그대로 옮겨 적었습니다. 그런데 이 룰은 DB 서버의 처지에서 본 상한입니다. 애플리케이션 입장에서는 다른 변수가 먼저입니다.

- 한 요청당 평균 쿼리 시간이 5 ms 라면, 커넥션 한 개가 초당 약 200 요청을 처리합니다. 동시 요청 1,000 이면 풀 5 개로도 이론상 충분합니다.
- 같은 동시 요청 1,000 이라도 쿼리 시간이 100 ms 면 필요한 풀은 약 100 개로 확 늘어납니다.
- 동시 요청이 100 인데 풀을 100 개로 잡아두면, 그만큼 DB 측 메모리 · 컨텍스트가 같이 묶입니다. DB 는 한가한데 풀만 부풀어 있는 상태가 됩니다.

운영 옵션 세 개는 같이 묶어서 봅니다.

- `connectionTimeout` — 풀에서 커넥션을 못 받을 때 얼마나 기다릴지. 웹 요청 타임아웃보다 작게.
- `idleTimeout` — 유휴 커넥션을 풀에서 거둬들이는 시간.
- `maxLifetime` — DB · L4 · 방화벽의 idle disconnect 보다 짧게. 안 짧으면 "끊긴 커넥션을 빌려주는" 사고가 납니다.

```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 10
      connection-timeout: 5000
      idle-timeout: 300000
      max-lifetime: 1200000
      data-source-properties:
        cachePrepStmts: true
        prepStmtCacheSize: 250
        prepStmtCacheSqlLimit: 2048
        useServerPrepStmts: true
        rewriteBatchedStatements: true
```

이 yaml 도 정답이 아니라 출발점입니다. `maximum-pool-size: 10` 이라는 숫자는 "이만큼 두고 부하 테스트에서 풀 사용률 · DB active connection · p99 latency 를 보겠다" 라는 선언입니다.

## 그래서 어떻게 시작하는가

풀 크기와 옵션은 항상 같이 움직입니다.

- 옵션 표를 외우는 것보다 한 번 측정해 보는 것이 빠릅니다.
- HikariCP 의 `HikariCP.PoolName` Micrometer 메트릭으로 `pending threads`, `active connections`, `acquire time` 을 같이 봅니다.
- DB 쪽에서는 `SHOW PROCESSLIST` 또는 `pg_stat_activity` 로 실제 동시 active 가 얼마인지 같이 봅니다.

DB 는 한가한데 서비스만 느려진다면, 그건 풀이 모자라거나 너무 길게 잡혀 있다는 신호 입니다. 양쪽 지표를 같이 보지 않고 옵션만 만지는 것은 어둠 속에서 칼을 휘두르는 것에 가깝습니다.

권장값은 시작점일 뿐, 운영 환경의 풀 크기는 항상 측정이 마지막 결재자입니다.
