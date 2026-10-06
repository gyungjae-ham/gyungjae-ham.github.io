---
author: "luca"
pubDatetime: 2024-12-17T16:32:21+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "현재 시간이 계속 같았던 이유: 계산 결과를 singleton 필드에 보관했다"
slug: "localdatetime-singleton-trap"
featured: false
draft: false
tags: ["학습노트", "retrospective", "java", "spring", "debugging"]
description: "매번 필요한 현재 시각을 객체 생성 때 한 번 계산했던 문제를 살펴봅니다. 시간대와 값의 수명을 구분하고 Clock으로 경계를 테스트합니다."
---

최근 3일의 활동을 보여주는 기능에서 기준 시간이 계속 같게 나왔습니다. 시간대가 몇 시간 어긋나는 수준이 아니라 나노초까지 같은 값이 반복됐습니다. 이 경우에는 시간대 설정과 함께 현재 시간을 어디서 계산하는지 확인해야 합니다.

원인은 시간을 계산한 결과를 유틸리티의 필드에 보관한 데 있었습니다. 다음은 문제를 단순화한 예시입니다.

```java
@Component
class DateUtils {
    private final LocalDateTime now = LocalDateTime.now();

    LocalDateTime now() {
        return now;
    }
}
```

인스턴스 필드는 **객체가 생성될 때** 한 번 초기화됩니다. `static` 필드라면 클래스 초기화 시점에 계산됩니다. 기본 singleton 빈은 여러 요청에서 같은 객체를 사용하므로, getter를 다시 불러도 시간이 새로 계산되지 않습니다. `final`을 제거해도 필드 값을 다시 대입하지 않으면 결과는 같습니다.

## 매 요청의 기준 시간이 필요했다

활동 조회 시점의 최근 3일이 목적이라면 메서드 실행 중 현재 시간을 구해야 합니다. singleton 자체를 제거할 필요는 없습니다.

```kotlin
class ActivityPeriod(private val clock: Clock) {
    fun recentThreeDays(): Pair<LocalDateTime, LocalDateTime> {
        val now = LocalDateTime.now(clock)
        return now.minusDays(3) to now
    }
}
```

위 예시는 `java.time.Clock`과 `LocalDateTime`을 사용합니다. 한 번의 조회에서 시작·종료 기준은 같은 `now`를 공유합니다. 테스트에서는 Clock을 고정해 정확한 기간을 검사할 수 있습니다. ‘3일’이 72시간인지 서비스 시간대의 달력 기준인지도 정책에 맞춰 선택해야 합니다.

시간을 필드에 보관하는 것이 모두 잘못은 아닙니다. 이벤트 발생 시각이나 객체 생성 시각처럼 한 번 정해져야 하는 값은 저장하는 것이 맞습니다. 문제는 매번 새로 계산해야 하는 현재 시각을 더 오래 사는 객체의 상태로 취급한 것입니다.

컨테이너 시간대는 별도로 맞춰야 하지만, 시간대 변경은 이미 저장된 값이 갱신되지 않는 문제를 해결하지 않습니다. 값이 몇 시간 어긋나는지, 아예 변하지 않는지를 먼저 나눠 보면 조사 범위를 줄일 수 있습니다.
