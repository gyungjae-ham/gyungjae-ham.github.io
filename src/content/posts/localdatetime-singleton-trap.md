---
author: "luca"
pubDatetime: 2024-12-17T16:32:21+09:00
modDatetime: 2026-10-13T15:39:22+09:00
title: "LocalDateTime.now()가 같은 시간을 반환한 이유"
slug: "localdatetime-singleton-trap"
featured: false
draft: false
tags: ["학습노트", "retrospective", "java", "spring", "debugging"]
description: "컨테이너 시간대를 고쳤는데도 최근 활동 조회의 기준 시각은 그대로였습니다. 현재 시간을 계산한 위치와 객체의 수명을 잘못 이해한 실수였습니다."
---

최근 3일의 활동을 보여주는 기능을 만들다가 조회 기준 시간이 계속 같은 문제를 만났습니다. 시간이 몇 시간 어긋나는 정도가 아니라 나노초까지 같은 값이 나왔습니다. 값은 컨테이너가 시작된 시점에 머물러 있었습니다.

처음에는 Docker의 시간대 문제라고 생각했습니다. 호스트는 한국 시간이었고 컨테이너는 UTC였기 때문입니다. 시간대 설정을 바꿔 보고 `tzdata`도 설치했습니다. 컨테이너에서 확인하는 시간은 맞아졌지만, API의 기준 시각은 여전히 바뀌지 않았습니다.

## 시간대가 아니라 계산 시점의 문제

원인은 날짜 유틸리티에 있었습니다. 현재 시간을 필드에서 한 번 계산한 뒤 그 값을 계속 사용하고 있었습니다. `final`을 제거하고 `@Component`로 등록해도 문제가 남았습니다. 필드 초기화가 메서드를 호출할 때마다 다시 일어나는 것은 아니기 때문입니다.

아래는 문제를 단순화한 예시입니다.

```java
@Component
class DateUtils {
    private final LocalDateTime now = LocalDateTime.now();

    LocalDateTime now() {
        return now;
    }
}
```

`LocalDateTime.now()`는 이 객체를 만들 때 호출됩니다. 그 뒤 `now()` 메서드를 몇 번 불러도 반환하는 것은 필드에 저장해 둔 같은 값입니다. 기본 singleton 빈은 여러 요청에서 같은 객체를 사용하므로 새 요청이 와도 초기화되지 않습니다. `final`을 지우는 것만으로 값이 갱신되지 않는 이유도 같습니다.

당시에는 일반 클래스를 사용하고 필요한 시점에 초기화하도록 수정한 뒤, 테스트와 개발 서버 API에서 시간이 갱신되는 것을 확인했습니다. 다만 지금 다시 보면 singleton을 없애는 것 자체가 필요한 수정은 아닙니다. 매번 달라져야 하는 값을 호출 시점에 계산하면 됩니다.

## 현재 시간을 구하는 위치를 메서드 안으로

아래는 당시 코드 그대로가 아니라, 시간을 주입해 테스트하기 쉽게 표현한 예시입니다.

```kotlin
class ActivityPeriod(private val clock: Clock) {
    fun recentThreeDays(): Pair<LocalDateTime, LocalDateTime> {
        val now = LocalDateTime.now(clock)
        return now.minusDays(3) to now
    }
}
```

`java.time.Clock`과 `LocalDateTime`을 사용합니다. 메서드가 실행될 때 현재 시각을 구하고, 한 번의 조회에서는 시작과 끝이 같은 `now`를 기준으로 계산됩니다. 테스트에서는 고정된 Clock을 전달하면 기간을 예측할 수 있습니다. 서비스에서 말하는 3일이 정확한 72시간인지 달력 기준인지는 별도 정책으로 정해야 합니다.

생성 시각처럼 한 번 정해져야 하는 값은 필드에 저장해도 됩니다. 제가 잘못 다룬 것은 매번 새로 필요한 현재 시각이었습니다. 시간대가 다르면 시각이 일정하게 어긋날 수 있지만, 나노초까지 같은 값이 반복된다면 언제 계산하고 어디에 보관했는지도 확인해야 합니다. 컨테이너 설정만 보고 있던 동안 놓친 부분이었습니다.
