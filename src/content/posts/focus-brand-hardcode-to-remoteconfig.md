---
author: "luca"
pubDatetime: 2026-05-28T17:03:48+09:00
title: "팀의 30분을 매번 깎던 하드코딩 한 줄 — 자발적 RemoteConfig 이관"
featured: false
draft: false
tags: ["Django", "RemoteConfig", "refactoring", "DX", "ownership"]
description: "마케팅 캠페인 때마다 개발자 손이 들어가던 PDP 포커스 브랜드명을 RemoteConfig 동적 조회로 옮긴 자발적 개선 — 30분 → 1분, 연 15건의 의미 없는 배포 제거, 캐시·fallback·공백 방어 결정까지."
---

> **TL;DR.** 누가 시키지 않았지만 분기마다 같은 PR을 만들고 있는 자신을 발견했습니다. PDP 포커스 브랜드명이 `products/constants.py` 안에 하드코딩되어 있어 3~4주마다 30분짜리 PR·배포·QA가 반복되던 일이었습니다. 회사가 이미 운영 중이던 RemoteConfig 인프라로 옮겨 운영팀이 1분 안에 직접 바꾸도록 했고, 그 결과 연 7.5시간과 의미 없는 PR 15건이 사라졌습니다.

## 분기마다 같은 PR을 만들고 있었다

마케팅 캠페인은 3~4주마다 PDP의 "포커스 브랜드" 영역을 새 브랜드로 교체합니다. 그런데 그 브랜드명이 코드 안에 박혀 있었습니다.

```python
# products/constants.py — Before
FOCUS_BRAND_NAME = "로웬"
```

캠페인이 바뀔 때마다 개발자 한 명이 이 한 줄을 고치고, PR을 올리고, 코드리뷰를 받고, 머지 후 배포 파이프라인을 통과시키고, QA가 PDP를 들어가 새 브랜드가 노출되는지 확인했습니다. 1회 30분, 분기당 4번 정도, 연 15건쯤 되는 의미 없는 PR이 쌓이고 있었습니다.

저한테 떨어진 티켓이 아니었습니다. 다만 같은 PR을 또 만들고 있는 자신을 본 어느 날, 이 일이 "분기마다 누군가는 해야 하는 의식" 처럼 되어 있다는 게 보였습니다. 작업 자체는 30분이라 누구도 큰 비용으로 느끼지 못했지만, 누적되면 팀의 시간이고 운영팀은 매번 개발자 호출을 기다려야 했습니다. 캠페인 변경이 야간이나 주말에 잡히는 날엔 배포 파이프라인을 잠에서 깨워야 했고요.

기술부채라고 부르기엔 너무 작고, 방치하기엔 매번 같은 자리에서 시간을 깎아먹는 패턴이었습니다. 자발적으로 개선 제안을 올렸습니다.

## 30분이면 자동화 가치가 있는가

작업 시간이 짧으면 자동화 가치가 의심받습니다. 한 번 30분이면 자동화 코드 짤 시간에 그냥 처리하는 게 빠르다는 반론이 늘 따라옵니다. 그래서 결정 근거를 세 가지로 정리해 PR 본문에 박았습니다.

- **빈도 × 단가:** 30분 × 월 1.3회 × 12개월 = 연 7.5시간. 게다가 PR·리뷰·배포·QA에 든 동료들의 시간을 합치면 실제 비용은 더 큽니다.
- **책임 재배치:** 마케팅 캠페인 도메인 값을 개발자가 책임지는 구조 자체가 어색합니다. 이 결정은 운영팀이 가장 잘 알고, 가장 빨리 실행할 수 있는 사람입니다.
- **장애 표면:** 변경이 코드 배포 파이프라인을 매번 통과하는 한, 무관한 코드 변경이 함께 들어와 PDP에 영향을 줄 가능성이 작지만 존재합니다.

## 신규 인프라 없이 — 회사가 이미 가진 패턴을 본다

해법 후보는 세 가지였습니다.

| 후보 | 장점 | 단점 |
|------|------|------|
| **A. 그대로 두기** | 추가 작업 0 | 매 3~4주마다 의미 없는 PR·배포 반복, 운영팀이 개발자에게 매번 의존 |
| **B. 어드민에 전용 모델·화면 신규 구축** | 도메인 특화 UI 제공 | 새 테이블·새 화면·새 권한 정의 비용 큼. 항목 하나 위해 과한 인프라 |
| **C. RemoteConfig 동적 조회** | `time-deal-page` / `review-carousel` 이 이미 같은 패턴으로 동작 중 — 학습·운영 비용 0, 어드민 화면 재사용 | 캐시 TTL·fallback 정책을 명확히 정해야 함 |

**C로 결정했습니다.** 같은 그룹(`client_config`) 안에 두 개의 호출부가 이미 같은 방식으로 돌고 있었습니다. 운영팀은 그 화면을 이미 매주 쓰고 있었고요. row 하나만 추가하면 인프라·UI·권한·교육 비용이 0이 된다는 게 결정적이었습니다.

조직이 이미 가지고 있는 패턴을 한 번 더 활용한다는 건 단순한 게으름이 아니라 **다음 사람의 학습 비용까지 낮추는 결정**이라고 봤습니다. 다음에 또 비슷한 "자주 바뀌는 도메인 값"이 등장할 때, 같은 패턴으로 5분 안에 처리할 수 있는 기반이 됩니다.

## 조회 함수는 한 파일 — 두 호출부가 같은 함수만 부른다

조회 로직은 `products/queries/focus_brand_queries.py` 한 파일에만 두고, 그 함수를 두 호출부가 함께 부르도록 했습니다.

```python
# products/queries/focus_brand_queries.py
from products.constants import DEFAULT_FOCUS_BRAND_NAME
from products.constants import FOCUS_BRAND_REMOTE_CONFIG_GROUP
from products.constants import FOCUS_BRAND_REMOTE_CONFIG_NAME
from utils.remote_config_util import get_remote_config_value


def get_focus_brand_name() -> str:
    """RemoteConfig(client_config / focus-brand-name)에서 포커스 브랜드명을 조회한다.

    값이 없거나 조회 실패 시 DEFAULT_FOCUS_BRAND_NAME("로웬")로 fallback.
    """
    try:
        value = get_remote_config_value(
            group_name=FOCUS_BRAND_REMOTE_CONFIG_GROUP,
            name=FOCUS_BRAND_REMOTE_CONFIG_NAME,
        )
    except ValueError:
        return DEFAULT_FOCUS_BRAND_NAME

    normalized_value = str(value).strip()
    if not normalized_value:
        return DEFAULT_FOCUS_BRAND_NAME
    return normalized_value
```

- `get_remote_config_value` 는 항목 미존재 시 `ValueError` 를 던집니다. fallback 분기는 `try/except` 한 곳에서 처리합니다.
- 값이 존재하더라도 `str(value).strip()` 후 빈 문자열인지 한 번 더 검사합니다. 운영팀이 실수로 공백만 입력해도 OpenSearch 에 빈 brand 가 들어가 검색이 깨지는 시나리오를 막기 위한 가드입니다.
- 호출부가 이 한 함수를 부르도록 강제했습니다 — PDP 응답을 만드는 view 와 OpenSearch 검색을 도는 service 두 곳입니다.

```python
# pages/views/page_view_set.py
@decorators.action(detail=False, methods=["get"])
def focuses(self, request, *args, **kwargs):
    """현재 활성화된 focus 브랜드 이름을 반환합니다 (2~3주마다 변경)."""
    return Response(
        {"name": get_focus_brand_name()},
        status=status.HTTP_200_OK,
    )

# products/services/product_suggest_service.py
params = OpenSearchParamsDto(
    query_type=QueryType.LISTING,
    sort=SortType.POPULAR,
    brands=[hotfix if hotfix else get_focus_brand_name()],
    ...
)
```

두 호출부가 각자 RemoteConfig 를 직접 부르는 게 아니라 `get_focus_brand_name()` 한 함수만 거치게 했습니다. 다음에 캐시·로깅·fallback 정책이 바뀔 때 이 한 파일만 고치면 두 호출부가 함께 따라옵니다.

## 캐시는 기본값이 아니다 — 옆 코드 따라가다 한 번 헛디뎠다

여기서 작은 실수가 있었습니다. 같은 그룹에서 동작 중인 `time-deal-page`·`review-carousel` 이 모두 `use_cache=True` (1시간 TTL) 로 호출하고 있어, 처음에는 그대로 따라가서 켰습니다. 그런데 운영팀이 변경을 누른 직후 PDP 를 확인했을 때 이전 브랜드가 그대로 나오는 현상이 발생했습니다.

복기해 보니 "즉시 반영" 이 이 도메인의 핵심 요구였습니다. 캠페인이 바뀌었는데 최대 1시간 동안 옛 브랜드가 노출되는 건 도메인 의도와 어긋났습니다. focuses API 호출 빈도가 낮고 RemoteConfig 는 작은 테이블의 인덱스 조회라 캐시 미사용으로 인한 QPS 부담은 무시할 수준이었기에, 후속 PR 로 `use_cache=False` 로 전환했습니다.

이번 일로 캐시 정책 결정을 한 줄로 정리했습니다 — **"운영팀이 바꾸자마자 보여야 하는가?"** 이 질문이 yes 면 캐시 끄기, no 면 TTL 설정. 옆 코드가 캐시를 켰다는 이유만으로 따라가는 건 도메인을 보지 않은 결정이었다고 봅니다.

## 동료 리뷰가 잡아준 가드 — `not value` 로는 부족하다

PR 단계에서 동료 리뷰(coderabbit)가 한 가지를 지적했습니다. 처음 구현에는 `if not value: return DEFAULT_FOCUS_BRAND_NAME` 만 있었습니다. 운영팀이 공백 문자열(`"   "`) 을 실수로 넣으면 `not value` 는 truthy 라 통과해 OpenSearch 에 공백 brand 가 들어갈 수 있었습니다.

지적 받자마자 `str(value).strip()` 후 빈값 검사로 보강했습니다. 외부 입력(운영팀 입력값) 을 받을 때는 `not value` 만으로는 부족하다는 걸 일반 룰로 셀프 체크 목록에 추가했습니다. 다음에 비슷한 외부 입력 코드를 짤 때 자동으로 떠올리게 하기 위해서요.

## 결과

| 지표 | Before | After |
|------|--------|-------|
| 1회 브랜드 교체 처리 시간 | 30분 (수정+PR+리뷰+배포+QA) | 1분 이내 (운영팀 RemoteConfig 화면 클릭→저장) |
| 변경 반영 latency | 30분 (배포 파이프라인 통과) | 1분 미만 (DB write 즉시) |
| 의미 없는 PR/배포 건수 | 연 약 15~17건 | 0건 |
| 운영팀의 개발자 의존도 | 100% (매 변경마다 개발자 필요) | 0% (운영팀 단독) |
| 연간 절감 시간 | — | 약 7.5시간 |

야간·주말 캠페인 변경이 잡혀도 배포 파이프라인을 깨우지 않게 됐고, 같은 패턴이 다음 도메인 값에 그대로 재사용 가능한 상태가 됐습니다.

## 후속 과제 — 패턴이 더 안전해지려면

작업이 끝난 뒤 보이지 않던 결함 두 개가 보였습니다. 둘 다 별도 티켓으로 분리해 제안했습니다.

- **RemoteConfig 자동 캐시 무효화 부재.** `time-deal-page` / `review-carousel` 처럼 `use_cache=True` 인 다른 호출부들은 여전히 "운영팀이 바꿔도 최대 TTL 동안 옛값" 한계를 안고 있습니다. RemoteConfig 모델에 `post_save` signal 을 달아 변경 시 자동으로 관련 캐시 키를 무효화하면 캐시 호출부 전체가 같은 안전망 위에 올라갑니다.
- **운영팀이 직접 쓸 캐시 flush API 부재.** 자동 무효화가 어떤 이유로든 동작하지 않을 때 운영팀이 스스로 캐시를 비울 방법이 없습니다. `experiments` 앱에 이미 비슷한 패턴(`experiment_cache_view`) 이 있었기에, 일반화한 RemoteConfig flush 엔드포인트를 만드는 작업이 가능합니다.

이 둘은 제 작업 범위를 넘지만, 같은 인프라를 쓰는 다른 영역이 같은 한계를 안고 있다는 신호라 식별해 두는 게 다음 사람에게 의미가 있다고 봤습니다.

## 하드코딩 한 줄에서 시작한 것

큰 리팩터링이 아니었습니다. 줄 수로 따지면 신규 함수 한 개와 호출부 두 줄 교체가 전부였습니다. 그런데 그 변경 하나가 분기마다 누군가의 30분, 야간 배포의 부담, 운영팀의 개발자 의존을 같이 가져갔습니다. 시키지 않은 일이라도 같은 자리에서 시간을 깎아먹는 패턴이 보이면 한 번 손대볼 가치가 있다고 — 이 PR 이후로 그렇게 보고 있습니다.
