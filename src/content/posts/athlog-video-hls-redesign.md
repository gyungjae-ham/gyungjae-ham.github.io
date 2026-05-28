---
author: "luca"
pubDatetime: 2026-05-22T17:00:00+09:00
title: "athlog 영상 100MB mp4 → 2MB 미만 HLS segment: MediaConvert 를 포기하고 ffmpeg + Celery 로 간 회고"
slug: "athlog-video-hls-redesign"
featured: true
draft: false
tags: ["hls", "ffmpeg", "celery", "video-streaming", "aws", "django", "architecture"]
description: "DAU 13만 / MAU 180만 athlog 영상이 첫 청크부터 100MB 를 다운로드받던 구조를 6초 HLS segment 로 자른 회고. 처음엔 MediaConvert + EventBridge 를 설계했지만 ffmpeg + Celery indexing 큐로 돌아선 이유까지."
---

> **TL;DR.** athlog 영상이 모바일에서 첫 청크부터 100MB 를 통째로 받던 구조를, 6초 HLS segment (개별 2MB 미만) 로 잘랐습니다. 설계 문서에는 AWS MediaConvert + EventBridge 로 그렸지만, 구현 직전에 결정을 뒤집어 `ffmpeg` + Celery indexing 큐로 갔습니다. 영상이 60초 내외라는 사실에 매니지드는 명백히 과했습니다. 새 워커 클러스터 0개, 비용 0원, mp4 노출 사고 0건으로 머지했습니다.

2026-05 에 백엔드 1인으로 단독 설계·구현·머지까지 끝낸 athlog 영상 변환 파이프라인 회고입니다. 1인칭으로 결정 과정을 풀고, 늦었던 자리도 같이 적습니다.

## 배경

- **서비스** athlog — 인스타그램 스타일의 콘텐츠 지면. 인스타 자동 동기화 + 어드민 직접 업로드 두 경로로 영상이 들어옵니다.
- **규모** DAU 13만 / MAU 180만. 인스타 → athlog → 상품 PDP 로 이어지는 구매 전환 깔때기의 톱오브퍼널.
- **역할** 백엔드 1인 단독 설계·구현. FE 1명과 협업하되 인프라까지 본인이 통제.
- **선행 상태** presigned 업로드로 mp4 가 S3 에 올라가고, 그 mp4 URL 이 그대로 CDN 으로 노출되던 구조.

영상 자체는 60초 내외로 짧습니다. 다만 100MB 한 덩어리가 통째로 다운로드되니, 모바일 LTE 환경에서 사용자는 첫 프레임 전 5초 검은 화면을 봅니다.

## "용량" 이 아니라 "재생 시작" 이 문제였다

운영 후 다음 세 이슈가 쌓였습니다.

- **첫 프레임 5초+ 검은 화면** — FHD 단일 비트레이트 원본을 통째로 받느라 모바일 LTE 에서 재생 시작 지연이 심각했습니다.
- **화질 적응 부재** — 네트워크가 약해지면 그대로 끊겼고 자동 다운시프트가 없었습니다.
- **일부 모바일 기기 튕김** — 100MB 단일 다운로드의 메모리 부담으로 구형 기기에서 앱·브라우저 크래시가 발생했습니다.

처음엔 "용량을 줄이면 풀리겠다" 고 보고 FE 압축을 만지작거렸지만, 이게 잘못된 진단이었습니다. 첫 프레임 5초는 용량의 문제가 아니라 **적응형 스트리밍 부재가 원인** 입니다. 영상이 짧아도 단일 mp4 는 전체 파일이 어느 정도 버퍼링되어야 재생이 시작됩니다. "잘게 자르고 점진적으로 다운로드" 라는 방향이 옳았습니다.

| 요구사항 | 내용 |
|---|---|
| **성능** | 첫 프레임 1초 이내 |
| **호환성** | 안드로이드 · 웹 · iOS 모두 정상 재생 (특히 타겟 35세+ 남성·40대 구형 폰) |
| **신뢰성** | 일부 기기 튕김 0건, 변환 중 mp4 노출 0건 |
| **운영 제약** | 백엔드 1인이 dev·stg·prod 인프라까지 통제 |
| **시간** | 1주 내 prod 전 검증 가능한 단순성 |

## 후보 셋, 그리고 매니지드를 일찍 의심한 이유

DAU 13만 / MAU 180만이라는 규모만 보면 매니지드를 깔고 싶어집니다. 다만 영상 자체가 60초 내외라는 점이 결정의 축이 됐습니다. 세 후보만 진지하게 봤습니다.

| 후보 | 핵심 아이디어 | 장점 | 단점 |
|---|---|---|---|
| **A. AWS MediaConvert (매니지드)** | S3 원본 → MediaConvert HLS 변환 → CloudFront → EventBridge 비동기 알림 | 안정성·확장성, AWS 가 SLA 책임, job queue 자동 관리 | IAM·job queue·webhook 구성 부담, dev/test 환경에 띄우기 복잡, 분당 과금, **영상 60초 내외에 매니지드는 명백히 과함** |
| **B. ffmpeg + Celery 자체 변환** | 기존 Celery 인프라 + `ffmpeg` 컨테이너로 자체 HLS 변환 | 기존 인프라 재사용 (Celery + S3), 비용 0, dev 환경 복잡도 0, 코드 일관성 | `ffmpeg` 컨테이너 추가 필요, OOM·hang 책임을 자체 부담 |
| **C. 동기 변환** | 요청 응답 안에서 `ffmpeg` 호출 | 단순 구현 | nginx·Django 워커 점유, 사용자 체감 latency 큼, **100MB 변환을 동기로 처리 부적합** |

Elastic Transcoder · GCP Transcoder · Cloudflare Stream · MUX 같은 다른 매니지드도 후보에 올릴 수 있었지만, 영상 길이·트래픽 규모에 비해 명백히 과한 인프라라 일찍 기각했습니다. "큰 서비스니까 무거운 도구" 가 아니라 "문제의 모양에 맞는 도구" 가 기준이었습니다.

## 어쩌다 설계가 뒤집혔나

Notion 설계 문서에는 처음 **A 후보 (MediaConvert + EventBridge → SQS → Celery)** 로 그림이 그려져 있었습니다. 매니지드의 안정성 + EventBridge 의 즉시성이라는 그럴듯한 청사진이었습니다.

다만 구현 직전 한 번 더 멈춰 보니 다음 셋이 동시에 떠올랐습니다.

- 영상이 60초 내외인데 MediaConvert 의 IAM·job queue·webhook·dev 환경 구성을 다 깔 가치가 있는가
- 백엔드 1인이 dev·stg·prod 다 챙겨야 하는 상황에서 매니지드 외부 의존이 늘어남
- 테스트 트래픽 기준 월 $수십의 비용 — 작은 수치지만 "그만큼이라도 안 쓸 수 있으면 안 쓰자"

설계를 뒤집어 **B 후보 (`ffmpeg` + Celery indexing 큐)** 로 갔습니다. 이게 옳았습니다. 매니지드가 답이라는 관성에 의존하지 않고 한 번 더 의심한 결정입니다. 다만 솔직히 말하면 결정 자체가 늦었습니다. 설계 문서 단계에서 영상 길이를 기준으로 후보를 잘랐어야 했고, 구현 직전에 뒤집은 건 1주의 일정을 까먹은 자리입니다.

단독 설계라는 건 외로운 만큼 자기 결정을 누가 검증해 주지 않는다는 의미이기도 합니다. "MediaConvert 가 답이라 적어둔 설계 문서를 내가 직접 뒤집어도 되는가" 를 한참 망설였습니다. 이 망설임을 짧게 끊는 게 다음 라운드의 숙제입니다.

## HLS 비트레이트 래더와 segment 길이 결정

세 단계 (1080p / 720p / 480p) 로 잡았습니다. 화질을 포기할 수 없었던 게 1차 이유입니다. athlog 콘텐츠는 인스타 → 상품 PDP 로 이어지는 톱오브퍼널이라 화질이 콘텐츠의 신뢰도와 직결됩니다.

- **1080p** — 데스크톱·고사양 모바일의 기본
- **720p** — LTE 환경의 fallback
- **480p** — 40대 구형 폰·약 네트워크의 마지막 보루

360p · 240p 는 화질이 너무 떨어져 콘텐츠의 톱오브퍼널 역할을 약화시킬 위험이 있어 제외했습니다.

segment 길이는 **6초** 로 잡았습니다. Apple HLS Authoring Specification 의 권장값을 그대로 따랐습니다.

- [Apple — HLS Authoring Specification for Apple Devices](https://developer.apple.com/documentation/http-live-streaming/hls-authoring-specification-for-apple-devices) — "**Use a target duration of 6 seconds**."
- [RFC 8216 — HTTP Live Streaming](https://datatracker.ietf.org/doc/html/rfc8216) — segment duration 권장 범위 정의
- [Mux 가이드 — Low-latency HLS Handbook](https://www.mux.com/blog/the-low-latency-hls-handbook) — VOD 에서 5~6초 segment 가 일반적

HLS 개별 segment 가 **2MB 미만** 으로 잘립니다. 100MB 한 덩어리를 50배 이상 경량화한 첫 청크입니다.

## 데이터 파이프라인

```
[FE] presigned 업로드
  │
  ▼
[S3] temp/uploads/{uuid}.mp4
  │ 콘텐츠 등록 API → S3 mover(`move_file`) 로 정식 키 이동
  │ + HeadObject 사후 검증
  ▼
[S3] athlog/{content_id}/videos/{ts}_{uuid8}.mp4 (원본 보존)
  │ Celery: transcode_to_hls.apply_async(queue="indexing")
  ▼
[Celery indexing worker]
  │ ffmpeg → 1080p / 720p / 480p HLS (6초 segment)
  │ FFMPEG_TIMEOUT_SECONDS = 600
  ▼
[S3] athlog/{content_id}/hls/{media_id}/{1080p,720p,480p}/*.ts + master.m3u8
  │ playlist.m3u8 sentinel 검증 → ContentMedia.status = READY
  │ desired_status 복원 (옵션 B 상태 캡처)
  ▼
[CloudFront] <자체 CDN 도메인>/hls/{content_id}/{media_id}/master.m3u8
  ▼
[클라이언트 hls.js / iOS native HLS / Android ExoPlayer] 적응형 재생
```

## 핵심 패턴 6개

### 1) presigned + S3 mover — 임시 → 정식 경로 분리

presigned 는 `temp/uploads/{uuid}` 에 올리고, 콘텐츠 등록 트랜잭션 안에서 `S3Mover.move_file()` 로 정식 키 (`athlog/{content_id}/videos/{ts}_{uuid8}.mp4`) 로 이동합니다.

- **HeadObject 사후 검증** — presigned 정책만으로 부족한 `Content-Type`·용량 정합성을 BE 에서 한 번 더 검증.
- **destructive S3 path 가드** — `move_file` 은 복사 후 삭제이므로 임시 경로가 아닌 정식 키가 들어오면 원본 영구 손실. 단건/벌크 양쪽 진입점에 공통 헬퍼 `validate_thumbnail_temp_key` 강제.

### 2) 옵션 B (상태 캡처) — 변환 중 mp4 노출 0 보장

처음엔 변환 완료 시 자동 PUBLISHED 로 가려 했지만, 운영자가 의도적으로 HIDDEN 으로 등록한 케이스가 무시되어 자동 공개되는 문제를 발견했습니다.

해결은 단순합니다. 영상 포함 콘텐츠는 등록 시 무조건 HIDDEN 으로 INSERT 하고, 운영자가 입력한 status 는 `desired_status` 라는 태스크 인자로 캡처해 들고 갑니다. 변환 완료 시 그 `desired_status` 로 복원합니다.

| 항목 | 옵션 A (자동 PUBLISHED) | 옵션 B (상태 캡처) — 채택 |
|---|---|---|
| 변환 완료 후 status | 무조건 PUBLISHED | 운영자가 입력한 status (PUBLISHED / HIDDEN) |
| 운영자 의도 보존 | ❌ | ✅ |
| race condition | 동시 변환 시 PUBLISHED 중복 발화 | `has_pending_hls_video_for_content` 가드로 마지막 태스크만 status 복원 |
| 변환 실패 시 | PUBLISHED 가 안 됨, mp4 노출 위험 | HIDDEN 유지, mp4 노출 0 |

### 3) Celery indexing 큐에 변환 task 동거 — 새 워커 없이 자원 확보

이게 가장 만족스러운 결정이었습니다. 새 워커 클러스터를 띄우는 대신 기존 OpenSearch 상품 indexing 큐가 대부분 idle 한 점을 활용했습니다.

- **기존 indexing 워커** — 상품 정보를 OpenSearch 에 indexing 하는 CPU light · 대부분 idle 한 워커.
- **새 작업** — `ffmpeg` 영상 변환 (CPU bound). general 큐에 넣으면 일반 요청을 막을 위험.
- **결정** — `IndexingTask` base 를 상속해 영상 변환 task 도 indexing 큐에 동거.

운영 결과 vCPU 2GB 기준 변환 task 가 **61% CPU 안정 수준**, indexing 큐의 idle 시간을 활용하니 영상 변환 부하가 일반 워커에 영향 0 인 구조가 됐습니다. 새 워커 클러스터 비용 0, 운영 부담 0.

### 4) 멱등 가드 — race 발생해도 status 깨지지 않음

같은 콘텐츠에 여러 영상이 있을 때 동시 변환 완료 시 status 전환이 중복 발화할 위험이 있습니다.

```python
def on_transcode_done(content_id, media_id, desired_status):
    ContentMedia.objects.filter(id=media_id).update(status="READY")
    if not has_pending_hls_video_for_content(content_id):
        # 마지막 태스크만 desired_status 복원
        Content.objects.filter(id=content_id).update(status=desired_status)
```

"마지막 태스크가 책임" 패턴 — `has_pending_hls_video_for_content` 검사 후 변경하므로 어느 task 가 마지막이든 결과가 결정적입니다.

### 5) SSRF 화이트리스트 — 첫 운영 사고

영상 다운로드 단계에서 `requests` 로 외부 URL 을 받는 자리가 있습니다. SSRF 방어로 화이트리스트 + `allow_redirects=False` 를 적용했는데, 인스타 CDN 만 허용했더니 어드민 업로드의 자체 CDN 다운로드가 차단됐습니다.

운영 배포 후 첫 실패로 발각된 사고입니다. 해결은 `PUBLIC_ASSET_URL` secret 에서 host suffix 를 동적 합성하도록 보강한 것입니다.

부끄러운 실수입니다. SSRF 화이트리스트는 처음부터 "신뢰하는 모든 출처" 를 빠짐없이 포함해야 하는데, 인스타 CDN 만 보고 자체 CDN 을 누락한 게 직접적 원인입니다. 다음에는 `_get_self_cdn_host_suffix` 류의 동적 합성을 설계 단계에서부터 깝니다.

### 6) 단건/벌크 진입점 가드 일원화

같은 작업이라도 단건 등록 흐름과 벌크 등록 흐름이 코드가 분리되어 있으면 가드가 한쪽에만 적용되는 비대칭이 반복됩니다. 이번 PR 에서만 다음 4건이 발견됐습니다.

- `_validate_thumbnail_temp_key` — 단건만 있고 벌크에 누락.
- destructive path 보상 삭제 — 단건만.
- `max_length` 검증 — 한쪽만.
- 인스타 sync 시 thumbnail 처리 — 단건만.

`validate_thumbnail_temp_key` 같은 공통 헬퍼로 추출해 두 흐름이 공유하도록 묶었습니다. 본 작업에서 도출된 규칙 `service/multi-entrypoint-parity.md` 를 사내 docs 에 승격해, 후속 PR 에서 자가 점검 가능하도록 했습니다.

## CloudFront · cache 정책 — 굳이 캐시를 안 한 이유

CloudFront 의 cache TTL 은 굳이 길게 잡지 않았습니다. athlog 의 콘텐츠 뷰가 cursor pagination 기반이고, 사용자가 한 콘텐츠를 보면 앞뒤 콘텐츠가 미리 당겨진 상태로 로드되는 흐름이라 같은 영상에 대한 반복 히트가 적습니다.

cache 정책은 기본값을 유지하고, OAC (Origin Access Control) 로 S3 직접 접근을 막는 보안 기본만 적용했습니다.

- **OAC 적용** — S3 bucket 은 CloudFront 만 origin 으로 인정.
- **signed URL / geo-restriction / WAF** — 본 작업 범위에서는 적용하지 않음 (다음 라운드 검토 후보).

## 결과

### 정량

| 지표 | Before | After | 변화 |
|---|---|---|---|
| **영상 1건 단위 다운로드 부담** | 100MB mp4 일괄 | HLS segment 당 **2MB 미만** (6초) | **첫 청크 50배+ 경량화** |
| **단건 미디어 추가 시 큐잉 대상** | 콘텐츠 내 모든 video 재큐잉 | 신규 영상만 큐잉 (`media_ids` 옵션) | **기존 영상 중복 트랜스코딩 0건** |
| **general 워커 영향** | (잠재) CPU bound 작업 혼재 | indexing 큐로 격리 | **0** |
| **indexing 워커 CPU** | 평소 idle | 변환 task 동시 처리 시 **61%** | bounded · 안정 수준 |
| **`ffmpeg` hang 최대 점유** | 무제한 | **10분 timeout** 후 강제 종료 | bounded |
| **mp4 노출 사고** | 변환 중 노출 위험 | 옵션 B 상태 캡처로 **0건** | 신뢰성 확보 |

수치 신뢰에 대해 한 가지 솔직하게 적습니다. 위 표는 prod 배포 직후의 단발 관측이고, 첫 재생 시작 latency (LCP) · 변환 task 95p 소요 시간 · 변환 실패율의 시계열 대시보드는 아직 없습니다. 측정 인프라 부족은 인정하는 자리입니다.

### 정성

- **호환성** — 안드로이드 · 웹 · iOS 세 클라이언트에서 정상 재생 확인.
- **운영 안정성** — 변환 실패 시 콘텐츠는 HIDDEN 유지 + Slack 알림. mp4 노출 사고 가능성 0.
- **재사용성** — 본 작업으로 도출된 규칙 2건 (`service/multi-entrypoint-parity.md`, `security/s3-destructive-path-guard.md`) 이 사내 docs 에 승격.
- **타 도메인 확장** — 동일 패턴 (presigned → 정식 키 이동 → 비동기 후처리) 이 상품 영상·배너 영상 등 다른 도메인으로 확장 가능.

## 다시 한다면

- **측정 인프라를 처음부터 같이 깐다** — LCP, 변환 task 평균·95p 소요 시간, 변환 실패율을 처음부터 대시보드로 묶었어야 했습니다. 설계는 잘 풀렸으나 정량 입증이 늦었습니다.
- **dev/test 환경에 indexing 워커 deploy workflow 를 같이** — 현재는 prod 만 있어 dev 에서 변환 task 검증이 불완전합니다.
- **변환 task 실패 시 retriable 마커 컬럼** — 현재는 Slack warning 후 운영자가 수동으로 재발사. cron 회수로 옮길 여지가 있습니다.
- **SSRF 화이트리스트는 동적 합성으로 처음부터** — 인스타 CDN 만 보고 시작했다가 첫 운영 사고로 자체 CDN 누락이 발각된 자리, 같은 실수를 또 하지 않습니다.

## 회고

이 작업의 핵심은 "매니지드가 답이라는 관성" 을 한 번 더 의심한 것입니다. 영상이 60초라는 사실을 다시 봤고, 그 사실이 결정의 축이 되었습니다. 운이 좋았던 부분도 있습니다. 기존 indexing 큐가 마침 idle 했기에 새 워커 클러스터 없이 자원을 확보할 수 있었습니다. 만약 indexing 큐가 이미 포화 상태였다면 같은 결정을 내리지 못했을 것이고, 그때는 B 가 정답이 아니었을 겁니다.

다음 라운드에서는 측정 인프라부터 깐 뒤 비트레이트 래더·segment 길이를 실측 LCP 기반으로 다시 잡습니다. 이번 회고에서 가장 늦었던 자리가 측정이었습니다.
