---
author: "luca"
pubDatetime: 2026-06-12T10:19:37+09:00
title: "CRM 발송 트래픽을 예약형 오토스케일링으로 자동화하기"
featured: false
draft: false
tags: ["AWS", "ECS", "오토스케일링", "서버리스", "EventBridge", "인프라"]
description: "주 5회 넘게 손으로 ECS를 증설하고 발송이 끝나면 다시 줄이던 CRM 발송 대응을, Slack 모달 입력 한 번으로 발송 시점에 맞춰 자동 증설·복귀하는 예약형 오토스케일링으로 바꾼 기록입니다."
---

> 주 5회 넘게, 발송 때마다 개발자가 콘솔에 들어가 ECS 태스크를 늘리고 발송이 끝나면 다시 줄였습니다. Slack 모달 입력 한 번으로 발송 시점에 맞춰 자동 증설·복귀하도록 바꿨고, 여기에 묶여 있던 개발자 시간을 0으로 만들었습니다.

## 매일 손으로 ECS를 늘리고 줄였다

CRM 발송은 카카오 플러스친구, 앱푸시처럼 한 번에 수만에서 수십만 명에게 메시지를 보냅니다. 발송 직후 짧은 시간에 트래픽이 몰리기 때문에, 그 시점에 맞춰 API 서버의 ECS 태스크를 미리 늘려두지 않으면 응답이 느려지거나 장애로 이어집니다. 반대로 발송이 끝났는데 늘린 채로 두면 쓰지도 않는 태스크에 비용이 나갑니다.

그래서 발송이 잡힐 때마다 개발팀이 손으로 처리하고 있었습니다.

- 발송 직전 콘솔에서 ECS Min/Max를 올린다
- 발송이 끝나면 원래 값으로 되돌린다
- 발송 모수(타깃 수)를 보고 얼마나 올릴지 직접 판단한다
- 발송 시각(밤·새벽 포함)에 맞춰 대기하며 지켜본다

빈도는 **주 5회를 넘었고**, 한 번에 **1시간 이상** 걸렸습니다. 단순 계산으로도 월 20시간 넘는 개발자 시간이 여기 묶여 있었습니다. 더 큰 문제는 사람이 한다는 것 자체였습니다. 바쁘면 **증설을 통째로 깜빡하는** 사고가 실제로 났고, 그러면 발송 시점에 서버가 맨몸으로 노출됐습니다.

목표는 분명했습니다. 발송 정보만 입력하면 개발자가 손대지 않아도 시점에 맞춰 알아서 늘었다 줄어드는 구조를 만드는 것.

## 메트릭 기반 오토스케일링은 왜 접었나

가장 먼저 떠오르는 답은 CloudWatch 메트릭 기반 동적 오토스케일링입니다. CPU나 요청 수가 올라가면 알아서 스케일 아웃하는 방식이라, 발송을 몰라도 대응합니다. 그런데 이 워크로드에는 맞지 않는다고 봤습니다.

| 방식 | 장점 | 단점 |
|---|---|---|
| 메트릭 기반 동적 스케일 | 발송을 몰라도 자동 대응, 입력 불필요 | 발송 트래픽은 순간 스파이크 — 스케일 아웃이 따라붙는 사이 응답 지연·장애. 시점을 미리 아는데 늦게 반응하는 셈 |
| 매번 수동 스케줄 등록 | 예약형이라 사전 증설 가능 | 결국 사람이 매번 등록 — 수동의 연장, 누락 위험 그대로 |
| 발송 공지를 트리거로 예약 액션 자동 등록 | 시점을 미리 알기에 무인 사전 증설, 입력 한 번으로 끝 | 트리거·정책·등록 파이프라인을 직접 만들어야 함 |

핵심은 **발송 시점은 사람이 미리 알고 있다**는 점입니다. 미래에 트래픽이 언제 몰릴지 아는데 메트릭이 올라가길 기다렸다가 그제야 반응하는 건 손해입니다. 스파이크가 순식간이라 스케일 아웃이 따라붙기 전에 피크가 지나갑니다.

그래서 세 번째 방식을 택했습니다. CRM 발송 공지를 등록하는 순간, 발송 5분 전 증설(Scale Out)과 발송 한참 뒤 복귀(Scale In)를 **1회성 예약 액션으로 미리 박아두는** 구조입니다. 사내에는 이미 Slack 이벤트를 받아 처리하는 서버리스 라우터가 있었으니, 그 위에 얹었습니다.

```
Slack 모달 제출 (발송 유형·일시·모수 입력)
   │
   ▼
SlackReceiver  ──►  EventBridge 'crm_notice' 발행
   (Slack 3초 응답 제한을 비동기 발행으로 회피)
   │
   ▼
CRM Worker (Lambda)
   ├─ 발송 공지를 사내 문서 DB에 기록
   └─ 카카오 발송이면:
        ① 현재 ECS Min/Max 조회 (baseline)
        ② 모수별 증설량 결정
        ③ 발송 5분 전 Scale Out / 발송 1시간 40분 후 Scale In 예약
        ④ Slack 스레드에 처리 결과 회신
   │
   ▼
Application Auto Scaling
   발송 5분 전 증설 ─► 발송 ─► 1시간 40분 후 원래대로 복귀
```

## 증설량은 "지금 값" 기준으로 잡았다

얼마나 늘릴지 정하는 데 두 갈래가 있었습니다. 환경변수에 Min/Max 절대값을 박아두는 방법, 그리고 발송 등록 시점에 현재 값을 조회해서 거기에 더하는 방법.

절대값은 단순하지만 인프라 baseline이 바뀌면 코드도 같이 고쳐야 합니다. 인프라 쪽에서 평소 태스크 수를 조정하면 자동화가 엉뚱한 값을 쓰게 됩니다. 그래서 **현재 등록된 ScalableTarget을 실시간 조회해서 거기에 모수별 증분을 더하는** 방식으로 정했습니다.

정책은 부수효과 없는 순수 함수로 떼어냈습니다. 입력은 모수와 현재 baseline, 출력은 증설·복귀 캐파시티뿐이라 테스트하기 쉽습니다.

```typescript
// 모수(만 명)와 현재 baseline에 따라 증설/복귀 캐파시티를 결정한다.
export const determineScalingForPopulation = (
  population: string,
  baseline: ScaleCapacity
): ScalingDecision => {
  const popInWan = parseFloat(population);
  if (!Number.isFinite(popInWan) || popInWan < 10) {
    return { needsScheduling: false }; // 10만 미만은 증설하지 않는다
  }
  const minIncrement = popInWan >= 15 ? 20 : 10;
  return {
    needsScheduling: true,
    outCapacity: {
      minCapacity: baseline.minCapacity + minIncrement, // 현재 값 + 증분
      maxCapacity: baseline.maxCapacity,
    },
    inCapacity: { ...baseline }, // 복귀는 처음 조회한 baseline 그대로
  };
};
```

- **10만 미만**은 증설하지 않고 기존 인프라로 둡니다.
- **10~15만**은 Min에 +10, **15만 이상**은 +20을 더합니다. Max는 baseline을 유지합니다.
- 복귀값은 늘 처음 조회한 baseline입니다. "원래 어디였는지"를 코드가 기억하므로 사람이 외울 필요가 없습니다.

현재 값을 더하기의 기준으로 삼은 덕분에, 인프라 기본값이 바뀌어도 이 코드는 그대로 따라갑니다.

## 증설과 복귀를 한 번에 예약했다

수동 운영에서 가장 잦은 실수는 늘리고 줄이는 걸 깜빡하는 것이었습니다. 특히 복귀는 발송이 끝난 한참 뒤라 더 잊기 쉬웠습니다.

이건 다짐으로 막을 문제가 아니라고 봤습니다. 그래서 증설 액션과 복귀 액션을 **공지 등록 시점에 한꺼번에 예약**했습니다. 발송 5분 전 Scale Out, 발송 1시간 40분 후 Scale In, 두 개를 동시에 등록하면 복귀를 잊는 경로 자체가 사라집니다.

```typescript
// 발송 5분 전 증설
await putEcsScheduledAction({
  scheduledActionName: buildScheduleName(dt.date, dt.time, 'out'),
  clusterName, serviceName,
  scheduleAt: calculateScaleOutTime(dt.date, dt.time),
  minCapacity: decision.outCapacity.minCapacity,
  maxCapacity: decision.outCapacity.maxCapacity,
});
// 발송 1시간 40분 후 복귀 — 같은 흐름에서 함께 등록
await putEcsScheduledAction({
  scheduledActionName: buildScheduleName(dt.date, dt.time, 'in'),
  clusterName, serviceName,
  scheduleAt: calculateScaleInTime(dt.date, dt.time),
  minCapacity: decision.inCapacity.minCapacity,
  maxCapacity: decision.inCapacity.maxCapacity,
});
```

- Application Auto Scaling의 1회성 예약 액션이라, 실행되고 나면 알아서 사라집니다. 따로 정리할 게 없습니다.
- 실행 시각은 `Asia/Seoul` 타임존 파라미터로 넘겨서, KST 변환을 직접 하지 않고 AWS가 해석하게 했습니다.

## 실패는 조용히 넘어가지 않게

자동화에서 가장 위험한 건 실패했는데 아무도 모르는 상황입니다. 여기서 두 가지를 신경 썼습니다.

첫째, baseline 조회가 실패하면 스케일링을 건너뛰되 **예외를 위로 던지지 않습니다.** 처음엔 그냥 throw하려 했는데, 그러면 핸들러 전체가 실패해 Lambda 비동기 재시도가 돌고, 그때마다 사내 문서 DB에 같은 공지가 중복 생성되는 문제가 있었습니다.

```typescript
let baseline: EcsScalableTargetCapacity | null = null;
try {
  baseline = await describeEcsScalableTarget(clusterName, serviceName);
} catch (err) {
  console.error('현재 ECS ScalableTarget 조회 중 오류:', err);
}

if (!baseline) {
  // 자동 증설을 못 했으니 담당자가 수동 확인하도록 Slack 스레드에 알린다
  await postMessage(slackBotToken, channelId, '인프라 설정 조회 실패 — 수동 확인 필요', {
    threadTs: messageTs,
  });
  return;
}
```

둘째, 처리 결과는 발송 공지가 올라온 Slack 스레드에 그대로 댓글로 답니다. "발송 5분 전 최소 N대로 증설하겠습니다", "10만 미만이라 기존 인프라로 두겠습니다" 같은 문장으로요. 담당자는 자기가 등록한 발송이 어떻게 처리됐는지 그 자리에서 확인합니다.

## 결과

| 항목 | 전 | 후 |
|---|---|---|
| 개발자 수동 운영 시간 | 주 5회+ × 1시간+ ≈ 월 20시간+ | 0 (개발자 개입 없음) |
| 발송 1건당 개발자 개입 | 1시간 이상 | 0분 (담당자 모달 입력 수 분으로 이관) |
| 증설 누락 사고 | 발생 이력 있음 | 0건 |
| 발송 후 복귀 누락 | 사람 기억에 의존 | 구조적으로 불가 (증설·복귀 동시 예약) |
| baseline 변경 대응 | 코드 수정 필요 | 코드 수정 0 (실시간 조회) |

수치는 발송 빈도(주 5회 초과)와 1회 소요(1시간 이상)에 기반한 추정입니다. 절대 태스크 수와 비용 같은 회사 내부 수치는 옮기지 않았습니다.

정량 못지않게 컸던 건 운영 감각의 변화였습니다. 밤·새벽 발송에 사람이 대기하던 부담이 사라졌고, 개발팀이 쥐고 있던 인프라 증설 권한이 발송 담당자의 Slack 입력으로 넘어가면서 병목이 풀렸습니다. 발송별 ECS 메트릭은 발송 1시간 뒤 자동 수집해 문서에 쌓아두니, 증설량이 적절했는지 데이터로 되짚을 수 있게 됐습니다.

## 남은 것

지금도 모수는 사람이 모달에 입력합니다. CRM 시스템에서 발송 대상 수를 직접 가져오면 이 입력마저 없앨 수 있습니다. 증분(+10/+20)도 지금은 제가 정한 고정 규칙인데, 쌓이는 메트릭을 보면 발송 규모 대비 실제 사용량이 드러나므로 데이터 기반으로 자동 조정하는 게 다음 작업입니다.

솔직히 인정할 부분도 있습니다. "장애 위험을 줄였다"는 말은 아직 정성 판단에 가깝습니다. 발송 시점의 CPU와 응답시간을 자동화 전후로 같은 기준에서 측정해 비교한 지표를 아직 만들지 못했고, 이게 남은 숙제입니다.
