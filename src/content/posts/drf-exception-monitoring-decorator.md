---
author: "luca"
pubDatetime: 2026-03-24T00:00:00+09:00
modDatetime: 2026-10-13T15:07:35+09:00
title: "DRF 예외 처리와 모니터링 코드 분리하기"
featured: true
draft: false
tags: ["Django", "DRF", "Sentry", "refactoring"]
description: "기존 API 응답을 유지하면서 Sentry 기록과 Slack 알림을 한곳으로 모았습니다. DRF의 예외 처리 위치와 테스트에서 교체한 함수가 호출되지 않던 이유를 살펴봅니다."
---

운영 API에서 예외가 발생하면 앱에는 정해진 오류 응답을 보내고, 개발자에게는 조사할 수 있는 기록을 남겨야 합니다. 작업하던 Django REST Framework(DRF) 서버는 Sentry에 예외를 기록하고 서버 오류를 Slack으로 알리고 있었습니다.

API마다 알림을 직접 보내던 방식에서 공통 처리를 도입했지만, 코드를 다시 보니 같은 예외를 처리하는 곳이 여전히 두 군데였습니다. 한쪽에서 알림을 보내면 다른 쪽은 이미 처리했는지 확인하고 건너뛰었습니다. 적용된 View가 245개라 각 API를 다시 수정하기보다 공통 처리의 역할을 정리할 필요가 있었습니다.

## 예외를 어느 위치에서 볼 수 있을까

DRF는 View의 예외를 잡아 오류 응답으로 바꿉니다. 예를 들어 View 안에서 DB 예외가 발생해도 DRF가 500 응답으로 처리하면, 바깥의 Django 미들웨어에는 원래 예외가 전달되지 않을 수 있습니다. 상태 코드만 보고는 어느 줄에서 어떤 예외가 났는지 알 수 없습니다.

기존에는 View의 Mixin에 있는 `handle_exception()`과 전역 예외 핸들러가 모두 모니터링을 담당했습니다. 전역 핸들러의 `isinstance` 검사는 같은 예외를 두 번 보내지 않기 위한 코드였습니다.

응답을 만들 핸들러를 선택하는 `get_exception_handler()`에서 공통 모니터링을 붙이도록 바꿨습니다. `with_monitoring(handler)`가 기존 핸들러를 감싸 예외 기록과 알림을 처리하고, Mixin에는 각 API에 맞는 응답 형식을 고르는 역할만 남겼습니다. View의 기존 상속 선언을 유지해 245개 호출부를 수정하지 않아도 됐습니다.

## mock으로 바꿨는데 원래 함수가 실행되는 문제

구조를 옮긴 뒤 테스트에서 기본 핸들러를 mock으로 바꿨지만 mock이 호출되지 않았습니다. 래퍼를 만드는 시점을 확인해 보니 모듈 import 시점의 함수 참조를 이미 저장하고 있었습니다.

아래 두 코드는 그 차이를 설명하기 위한 축약 예시입니다.

```python
# 래퍼를 만드는 시점의 함수를 저장합니다.
monitored_handler = with_monitoring(default_handler)

# 함수가 실행될 때 default_handler를 찾습니다.
@with_monitoring
def monitored_handler(exc, context):
    return default_handler(exc, context)
```

첫 번째는 나중에 `default_handler`라는 이름이 가리키는 대상을 교체해도 래퍼 안의 참조가 그대로입니다. 두 번째는 함수 본문이 실행될 때 그 이름을 찾으므로 테스트에서 교체한 함수가 호출됩니다. 데코레이터 문법 자체보다 참조를 조회하는 시점이 달라진 것입니다.

기존 단위·통합 테스트 31건으로 응답 본문, 상태 코드, 헤더가 유지되는지 확인했습니다. 모니터링을 래퍼로 모으면서 중복 방지용 `isinstance` 검사도 제거했습니다. 이제 응답 형식을 추가할 때는 해당 핸들러에 같은 래퍼를 적용하면 됩니다.
