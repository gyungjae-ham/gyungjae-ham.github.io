---
author: "luca"
pubDatetime: 2026-05-28T16:44:37+09:00
title: "어드민의 손을 떼게 만든 athlog 인스타그램 자동 동기화 파이프라인"
featured: false
draft: false
tags: ["Django", "Celery", "S3", "Instagram", "athlog", "backend"]
description: "어드민이 매일 손으로 옮기던 athlog 인스타 게시물 등록을 자동 수집으로 바꾸며 마주친 결정들 — presigned 우회, requests stream + boto3 multipart, Redis 분산 락, S3 Lifecycle Rule 부수 이득까지."
---

> **TL;DR.** 어드민이 매일 1~2건씩 athlog 인스타 게시물을 손으로 옮겨 적던 운영 부하를, 매일 새벽 한 번 도는 Celery 잡으로 0건까지 끌어내렸습니다. presigned 우회 / `requests stream=True` + `boto3 upload_fileobj` 멀티파트 / Redis 분산 락 / 어드민 흐름과 동일한 `temp → move` S3 키 컨벤션으로 단일 잡 1회 69건 무중단 수집(실패 0건)을 검증했습니다.

## 어드민의 손이 매일 깎이는 일

athlog는 athler.official 인스타그램 게시물을 큐레이션해 앱 피드에 노출하는 채널입니다. 자동화 전에는 어드민 한 명이 인스타에서 게시물을 보고 백오피스에 손으로 옮겨 등록했습니다. 텍스트 복사, 미디어 다운로드, presigned 업로드, 메타데이터 입력까지 한 건당 적지 않은 시간이 들었고, 일 1~2건이 누적되며 신규 게시물 노출까지 평균 1~2일이 지연되고 있었습니다.

이 일을 0으로 만드는 게 목표였습니다. 인스타그램 Graph API로 미디어를 직접 받아오면 어드민 입력 없이 athlog 피드까지 자동 적재가 가능하다는 판단으로 단일 스프린트 안에 단독으로 설계·구현하기로 결정했습니다.

요구사항을 정리하면 이렇습니다.

- 매일 정해진 시각에 자동 수집 (KST 04:00 결정)
- IMAGE / VIDEO / CAROUSEL_ALBUM 3종 미디어 타입 모두 처리
- 이미 수집된 게시물은 재적재 금지 (멱등)
- 사진만 있는 게시물은 즉시 노출, 영상 포함은 어드민 검수 후 노출
- 인스타 토큰(60일 만료)을 코드에 박지 말고 운영팀이 동적 변경 가능
- 영상 100MB 이상이 들어와도 워커 메모리가 폭발하지 않을 것
- 외부 API/S3 일시 장애에는 자동 재시도, 인증 만료에는 즉시 알림

## presigned 우회 — 백엔드 잡이 직접 올린다

첫 번째 갈림길은 S3 업로드 방식이었습니다. 어드민 수동 등록은 presigned URL을 발급해 FE가 직접 올리는 패턴을 씁니다. 그대로 재사용할지, 아니면 백엔드 잡이 직접 받아 올리는 방식으로 바꿀지를 골라야 했습니다.

| 후보 | 장점 | 단점 |
|------|------|------|
| **A. presigned URL** | 기존 코드 재사용, 검증된 패턴 | FE 개입 전제 — 백엔드 잡에서는 의미가 없고 결국 서버가 받아 다시 올려야 함 |
| **B. 서버사이드 직접 업로드** | Celery 워커가 인스타 CDN → S3 직접 전송, FE 없이 동작 | 메모리·네트워크 모두 워커가 책임 |

**B로 결정했습니다.** presigned는 본질적으로 FE의 nginx `client_max_body_size 5MB` 제한을 우회하기 위한 패턴입니다. 그 제한은 inbound에만 걸리고 워커→S3 outbound와는 무관하므로, 백엔드 잡에는 presigned가 줄 이득이 없습니다. 검증된 패턴이라는 이유로 잘못된 도구를 가져오는 건 손해라고 봤습니다.

## 영상 100MB도 워커 메모리 한 자리수 MB로

두 번째 결정은 영상 다운로드·업로드 방식이었습니다. 100MB 넘는 영상이 들어와도 워커 메모리가 폭발하지 않아야 했습니다.

| 후보 | 메모리 점유 | 구현 복잡도 |
|------|------------|------------|
| **A. `BytesIO` 통째 적재** | 영상 1건 = 100MB+ 워커 메모리 점유 | 단순 |
| **B. `SpooledTemporaryFile`** | ~10MB까지 메모리, 초과 시 디스크 스풀 | 중간 |
| **C. `requests stream=True` + `boto3 s3.upload_fileobj`** | ~8MB 청크 자동 멀티파트 | 표준 패턴, 7~8줄 |

**C로 결정했습니다.** boto3 `upload_fileobj`가 파일 객체를 받으면 내부적으로 자동 멀티파트를 처리하므로 코드 부담 없이 영상 100MB+에서도 워커 메모리가 chunk 단위로만 점유됩니다. `content-length` 헤더 가드를 함께 둬 이미지 20MB / 영상 200MB 상한을 넘는 비정상 미디어는 단건 skip 했습니다.

실제 구현은 이렇게 생겼습니다.

```python
# libs/aws_s3/s3_uploader.py — upload_from_url 핵심부
response = requests.get(url, stream=True, timeout=60, allow_redirects=False)
response.raise_for_status()

content_length_header = response.headers.get("Content-Length")
if content_length_header:
    actual_bytes = int(content_length_header)
    max_bytes = max_size_mb * 1024 * 1024
    if actual_bytes > max_bytes:
        raise MediaTooLargeError(actual_bytes=actual_bytes, max_bytes=max_bytes)

response.raw.decode_content = True
self.s3_client.upload_fileobj(
    response.raw,
    Bucket=self.bucket_name,
    Key=file_path,
    ExtraArgs={"ContentType": resolved_content_type},
)
```

- `stream=True` 로 받기 시작한 응답의 `raw` 파일 객체를 `upload_fileobj` 에 그대로 흘려보냅니다. boto3 가 자동으로 멀티파트로 끊어 올립니다.
- `content-length` 가드는 응답 직후 한 번만 검사하면 됩니다. 이미 받기 시작한 데이터가 상한을 넘어가는 시나리오는 일어나지 않습니다.
- `allow_redirects=False` 는 인스타그램 CDN 리다이렉트를 막아 내부 IP로의 재유도를 차단하는 SSRF 보강입니다 (이 부분은 뒤에서 다시 다룹니다).

## 어드민 더블클릭 + cron 동시 트리거 — Redis 분산 락

수집 잡에 어드민 트리거 API도 함께 달았습니다. 운영자가 정기 시각을 기다리지 않고 즉시 실행할 수 있도록요. 그러자 한 가지 시나리오가 떠올랐습니다. 어드민이 트리거 버튼을 더블클릭하거나, 어드민 트리거 직후 정시 cron이 또 돌면 같은 인스타 게시물이 동시에 두 잡으로 들어가 S3 업로드와 DB INSERT가 경쟁 상태에 빠지는 경우입니다.

해법은 Redis 분산 락이었습니다. `cache.add` 가 django_redis 백엔드에서 `SET NX EX` 로 동작하는 점을 이용해 동시 실행을 원자적으로 차단했습니다.

```python
# athlog/tasks/instagram_sync_task.py
@shared_task(
    name="sync_instagram_contents_task",
    bind=True,
    max_retries=3,
    autoretry_for=RETRY_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def sync_instagram_contents_task(self) -> dict:
    if not cache.add(
        INSTAGRAM_SYNC_LOCK_KEY,
        "1",
        timeout=INSTAGRAM_SYNC_LOCK_TIMEOUT,  # 600s
    ):
        logger.info("인스타그램 수집 태스크 락 보유 중 — 동시 실행 스킵")
        return {"fetched": 0, "created": 0, "skipped": 0, "failed": 0, "locked": True}

    try:
        result = sync_instagram_contents()
    finally:
        cache.delete(INSTAGRAM_SYNC_LOCK_KEY)
```

- 락은 `try / finally` 가 아니라 잡 종료 시점에 무조건 해제합니다. Celery `autoretry_for` 가 작동해도 동일 태스크가 락을 새로 잡아 재시도해야 정합성이 유지되기 때문입니다.
- `retry_backoff` + `retry_jitter` 조합으로 일시 장애에서는 자동 복구되도록 두되, 인증 오류·설정 누락 같은 즉시 실패 예외는 `Notification.error` 로 Slack 즉시 알림 후 raise 합니다.
- `RETRY_EXCEPTIONS` 는 `HttpException`, `InstagramGraphRateLimitError`, `InstagramGraphServerError` 3종으로 좁혔습니다. 인증 만료(`InstagramGraphAuthError`)는 재시도해도 같은 결과라 즉시 실패 분류로 뺐습니다.

분산 락은 노트 초안에는 빠져 있던 디테일이었는데, 어드민 트리거 API가 추가되면서 비로소 필요해진 것이었습니다. 운영 단계에서 시나리오가 늘어날 때마다 잡 자체의 안전망이 한 겹씩 두꺼워지는 게 보였습니다.

## 어드민 흐름과 같은 S3 키 컨벤션 — 부수 이득은 청소까지 무료

1차 구현에선 인스타 전용 키 컨벤션(`athlog/content/instagram/{external_id}/{uuid}.{ext}`)을 만들었습니다. external_id 기반이라 Content pk 없이도 트랜잭션 밖에서 끝낼 수 있다는 게 매력이었습니다. 그런데 PR 리뷰 단계에서 운영자 입장의 혼동이 보였습니다. 어드민 수동 등록 콘텐츠는 `contents/{content_id}/...` 에 있고, 자동 수집 콘텐츠는 `athlog/content/instagram/{external_id}/...` 에 있다면 S3 콘솔에서 콘텐츠 한 건을 찾으려는 운영자는 두 패턴을 모두 알아야 합니다.

키 컨벤션을 어드민 흐름과 동일하게 재설계했습니다. `temp/uploads/{uuid}.{ext}` 로 먼저 올린 뒤 Content INSERT 후 `contents/{content_id}/{images|videos}/...` 로 move 하는 패턴입니다. 트랜잭션 안에 `move_file` 외부 호출이 들어가지만, multipart 업로드는 이미 끝난 상태에서 metadata copy만 발생하므로 락 점유 시간은 무시할 수준이었습니다.

기대 못 한 부수 이득이 따라왔습니다. `temp/uploads/` prefix 에는 이미 S3 Lifecycle Rule이 24시간 후 자동 청소를 걸어두고 있었습니다. DB 적재 중간에 실패해 고아 파일이 남아도 별도 cleanup 잡 없이 자동으로 사라집니다. 일관성을 위한 결정이 청소 비용 0이라는 인프라 이득까지 가져왔습니다.

처리 흐름은 트랜잭션 경계를 의식해 세 단계로 잘랐습니다.

```python
# athlog/services/instagram_sync_services.py — _process_item 발췌
try:
    media_payloads = _build_media_payloads(item=item, client=client, s3=s3)
except Exception:
    return 0, 0, 1  # temp 까지의 실패 — Lifecycle 이 24h 후 자동 청소

try:
    content = create_instagram_content_shell(input_data=input_data)
except IntegrityError:
    return 0, 1, 0  # 동시 실행에서 살아남은 중복

try:
    final_specs = _move_to_final_keys(content_id=content.id, payloads=media_payloads, s3=s3)
    bulk_create_instagram_media(content=content, media_specs=final_specs)
except Exception:
    soft_delete_content_with_media(content=content)  # 빈 Content 행 정리
    return 0, 0, 1
```

- 1단계(`_build_media_payloads`) 는 트랜잭션 외부. 외부 HTTP 와 S3 업로드가 끝날 때까지 DB 커넥션을 잡지 않습니다.
- 2단계(`create_instagram_content_shell`) 는 단일 행 INSERT 만 atomic 으로 처리. 외부 호출 없이 끝납니다.
- 3단계(`_move_to_final_keys` + `bulk_create_instagram_media`) 는 트랜잭션 외부에서 move 후 atomic bulk_create. 중간 실패 시 2단계의 빈 Content 행을 `soft_delete_content_with_media` 로 정리합니다.

이 분리가 없으면 외부 I/O 가 트랜잭션 안에 묶여 워커 한 명이 DB 커넥션을 수십 초 점유하는 패턴이 됩니다.

## 인스타 CDN을 함부로 믿지 않는다 — SSRF / Stored XSS 가드

`upload_from_url` 안에는 보안 가드 두 겹이 더 들어가 있습니다.

- **SSRF 방어:** 다운로드 URL의 호스트를 화이트리스트(`_TRUSTED_DOWNLOAD_HOST_SUFFIXES`)로 검증합니다. 인스타그램 CDN 도메인만 허용하고 그 외엔 `UntrustedHostError` 로 단건 skip 합니다. 추가로 `allow_redirects=False` 로 리다이렉트도 막아, CDN 응답이 내부 IP로 재유도되는 시나리오를 차단했습니다.
- **Stored XSS 방어:** 호출자가 기대한 Content-Type 카테고리(`image/*` vs `video/*`)와 응답의 실제 Content-Type 이 카테고리 수준에서 일치하는지 확인합니다. SVG 나 HTML 이 `.jpg` 키로 올라가 CDN 에서 실행되는 시나리오를 막기 위함입니다. 카테고리 불일치 시 `ContentTypeMismatchError` 로 단건 skip 합니다.

외부에서 받은 미디어를 우리 도메인으로 다시 서빙하는 파이프라인이라, "받은 그대로" 라는 단순함이 곧 공격면이 된다고 봤습니다.

## 검수 부담은 영상에만 — status 정책으로 절반 이하

마지막 결정은 신규 콘텐츠의 초기 status 였습니다. 모두 `HIDDEN` 으로 두고 어드민이 검수 후 `PUBLISHED` 로 전환하면 안전하지만, 그 경우 자동화의 절반이 다시 어드민 손으로 돌아옵니다.

운영팀과 합의해 사진만 있는 게시물은 즉시 `PUBLISHED`, 영상 포함 게시물만 `HIDDEN` 로 들어가게 했습니다. 사진 게시물은 인스타 원본과 동일한 안전성을 가지므로 즉시 노출이 안전하다고 본 운영 판단이었고, 영상은 길이·내용 검토 필요성이 있어 어드민 게이트를 유지했습니다. 검수 큐 진입 비율은 100% 에서 영상 포함 게시물 비율로 줄었고, 어드민 검수 일감도 그만큼 압축됐습니다.

영상 포함 콘텐츠가 들어오면 같은 잡 안에서 HLS 변환 태스크를 enqueue 해 백그라운드로 변환 → `PUBLISHED` 전환까지 이어집니다. 어드민 입력 없이 변환 완료 후 즉시 노출이 default 의도입니다.

## 결과와 남은 측정

| 지표 | Before | After |
|------|--------|-------|
| 어드민 인스타 게시물 수동 등록 | 일 1~2건 | 0건 |
| 신규 게시물 노출까지 lead time | 평균 1~2일 | 최대 24시간 (어드민 트리거 시 즉시) |
| 자동 수집 처리량 | n/a | 단일 잡 1회 69건 무중단 수집 (실패 0건) |
| 영상 미디어 메모리 점유 | n/a | 워커당 청크 단위 (100MB+ 영상 OOM 0) |
| 검수 큐 진입 비율 | 100% | 영상 포함 게시물 비율로 축소 |

운영 1주 후로 미뤄둔 측정도 있습니다.

- 일평균 신규 게시물 수 (CloudWatch 로그 카운트)
- 검수 큐 진입 비율 실측 (영상 포함 % vs 사진만 %)
- 잡 1회 수행 평균 시간 (page 순회 수, 미디어 다운로드/업로드 합산)
- `MAX_PAGES=4` 적정성 (실제 도달 빈도)

설계 단계에서 추정한 수치들이 실측과 얼마나 어긋나는지 확인하는 게 다음 작업입니다.

## 결정들의 합

자동화 한 줄로 요약되는 결과 뒤에는 작은 결정들이 켜켜이 쌓여 있었습니다. presigned 패턴을 재사용하지 않기로 한 결정 하나가 메모리·SSRF·XSS 가드를 직접 책임지는 길로 이어졌고, 어드민 흐름과 키 컨벤션을 통일하기로 한 결정 하나가 Lifecycle Rule 무료 청소까지 따라오게 했습니다. 검증된 패턴이라는 이유만으로 들고 오는 도구는 잡 자체의 제약과 맞지 않을 수 있다는 점, 그리고 일관성을 위한 결정이 인프라 이득까지 가져올 수 있다는 점을 이번에 다시 본 셈입니다.
