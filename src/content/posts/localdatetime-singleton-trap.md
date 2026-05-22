---
author: "luca"
pubDatetime: 2024-12-17T16:32:21+09:00
modDatetime: 2026-05-23T00:00:00+09:00
title: "LocalDateTime 이 항상 같은 값을 반환하던 버그 — 시간은 상태가 아니라 함수의 결과입니다"
slug: "localdatetime-singleton-trap"
featured: false
draft: false
tags: ["retrospective", "java", "spring", "debugging"]
description: "Util 클래스에 final + @Component 로 묶어두었더니 LocalDateTime 이 나노초까지 고정되었던 사고. 5~6년차 시각으로는 '시간·랜덤·외부 자원은 항상 함수의 결과여야 한다' 는 결론으로 요약됩니다."
---

> 2024-12 tistory 회고를 5~6년차 시각으로 다시 손본 글입니다. 그때는 `final` 이 문제구나 → Bean 으로 등록하자 라는 디버깅 흐름을 탔지만, 지금 보면 **"시간은 인스턴스가 들고 있는 상태가 아니라 메서드 호출의 결과여야 한다"** 한 줄로 정리됩니다.

활동 스트림을 최근 3일로 요약하는 탭에서, 도커 컨테이너가 시동되는 시점의 시간이 영원히 반환되던 버그였습니다. 나노초까지 똑같았습니다.

## 디버깅의 곁가지 — 컨테이너 시간만 의심했습니다

처음 의심은 컨테이너 시간이었습니다. 호스트는 KST, 컨테이너는 UTC. 다음 순서로 손을 댔습니다.

- `/etc/localtime` 마운트 → 효과 없음
- `/etc/timezone` 권장 따라 변경 → 여전히 UTC
- Dockerfile 에서 `tzdata` 설치 + 명시적 zoneinfo 복사

```dockerfile
ENV TZ=Asia/Seoul
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone
```

컨테이너 시간은 맞아졌습니다. **하지만 API 응답의 시간은 여전히 고정** 이었습니다. `LocalDateTime.now()` 가 고정된 값을 반환할 리는 없었습니다.

## 진짜 원인 — Util 클래스의 final 필드

한 번 더 보니, 프로젝트 전체에서 쓰던 `DateUtils` 의 시간 변수가 `final` 로 선언되어 있었습니다. 클래스 로딩 시점의 값을 그대로 들고 있었던 셈입니다.

`final` 만 떼고 `@Component` 로 Bean 에 등록했더니, **이번에는 싱글톤 인스턴스의 필드가 같은 값을 들고 있었습니다.** 결과는 동일했습니다. 한 줄을 손볼 때마다 같은 결과가 나오는 게 더 무서웠습니다.

| 시도 | 동작 | 왜 실패했는가 |
|---|---|---|
| `static final` 으로 한 번 계산 | 컨테이너 시동 시각 고정 | 시간이 상수가 됨 |
| Bean 등록 + 인스턴스 필드 | 컨테이너 시동 시각 고정 | 싱글톤 + 인스턴스 필드 = 사실상 상수 |
| 일반 클래스 + 사용 지점에서 호출 | 매번 새 값 | 시간을 메서드 호출의 결과로 받음 |

## 그래서 어떻게 시작하는가

테스트에서는 정상이고 운영에서만 나노초까지 똑같이 고정되어 나온다면, **그 값은 "메서드 호출의 결과" 가 아니라 "인스턴스가 들고 있는 상태" 라는 신호 입니다.** 시간·랜덤·외부 자원은 항상 함수 호출의 결과로 받아야 합니다.
