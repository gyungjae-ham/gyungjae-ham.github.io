---
title: About
description: 5-6년차 Kotlin/Spring·Python/Django 백엔드 개발자 함경재(Luca). 대용량 트래픽 처리와 시스템 최적화 중심의 경력 요약입니다.
---

> 안녕하세요, 백엔드 개발자 **함경재 (Luca)** 입니다. Kotlin · Spring Boot · Python · Django 위에서 일하며, 느린 코드의 진짜 병목을 찾아 수치로 끌어내리는 일을 좋아합니다.

## Highlights

| 수치 | 무엇을 | 어디서 |
|---|---|---|
| **60초 → 3~5초** | 1,000건 주문 등록 92% 단축 — SQS 비동기 → API 직접 + Batch Insert | 위밋모빌리티 |
| **42초 → 20ms** | 외부 API 통합 3단계 — Coroutine `async` + Spring Batch + MongoDB | 라이너스 |
| **1,200ms → 55ms** | Slow Query — 쿼리 분할 + 페이지네이션 | 위밋모빌리티 |
| **3분 20초 → 21초** | 테스트 실행 — 병렬 + 모듈별 `SAME_THREAD` 분리 | 위밋모빌리티 |
| **분실율 0%** | 출결 데이터 — 줌 webhook · 동영상 · 집계 별도 서버 분리 | 라이너스 |
| **5초+ → 1초 이내** | athlog 영상 첫 프레임 — HLS + EventBridge 비동기 파이프라인 | 위밋모빌리티 |
| **600MB → 135MB** | Athler API Kotlin 이전 — jlink + Alpine 3-stage 이미지 | BIND |

## Experience

### BIND — 백엔드 · 2026.01 ~ 재직중

- **스택** Python · Django · DRF · Celery · PostgreSQL · Redis · AWS (ECS Fargate · OpenSearch · ElastiCache) · Kotlin · Spring Boot 4
- **Celery 안정화** 매일 09:00 Worker CPU 70~80% 급증 추적 → rate limit · 시간대 분산 · 메트릭 기반 오토스케일링 설계
- **Queue 분리** 단일 default → `high` / `default` / `low` 3-Queue + ECS Service 독립 스케일링
- **Ephemeral 환경** PR 단위 `pr-{n}.dev` 자동 배포·정리 (Fargate Spot + ACM + 동적 ALB)
- **관측성 재설계** Sentry 4xx 필터링 + 전역 `EXCEPTION_HANDLER` + 구조화 로깅 (4개 PR 단계화)
- **Kotlin 이전 도커화** Spring Boot 4 + jlink + Alpine 3-stage → 이미지 600MB → 135MB

### 위밋모빌리티 — 백엔드 주임 · 2024.10 ~ 2026.01

- **스택** Kotlin · Spring Boot 3 · MySQL · Querydsl · MongoDB · Redis · K6 · Kubernetes · AWS
- **성능** 대용량 주문 92% ↓ · Slow Query 95% ↓ · 테스트 속도 90% ↓
- **부하 대응** K6 부하 테스트로 Pod 리소스·수 재조정 → 피크 timeout 0
- **사내 표준화** `ObjectMapper` 라이브러리화 · Querydsl `@QueryProjection` 통일 · RestDocs KotlinDSL
- **athlog 영상 파이프라인** S3 + MediaConvert + CloudFront + EventBridge 단독 설계

### 라이너스 — 백엔드 선임 · 2023.07 ~ 2024.09

- **스택** Kotlin · Spring Boot 3 · Spring Batch · JPA · Jenkins · Ansible · Canvas LMS
- **솔루션 도입** 금오공과대 · 한일장신대 · 차의과학대 · 경복대 · 대덕대 등 다수 대학
- **성능·신뢰성** API 42초 → 20ms · 테스트 3분 → 25초 · 모듈 분리로 데이터 분실 0%
- **아키텍처** JWT 다중 컨테이너 로그인 · 멀티 모듈 분리 · 단방향 의존
- **인프라** Jenkins + Ansible Playbook CI/CD 파이프라인 구축

### 레인보우8 — 백엔드 · 2021.12 ~ 2022.11

- Java · Spring Framework · React
- PHP 회사 홈페이지 3개를 Java/Spring + React 로 마이그레이션
- Google reCAPTCHA 도입으로 일일 스팸 100건 차단

### 쿠돈 — 백엔드 · 2021.07 ~ 2021.10

- 1회성 쿠폰 발행 흐름 설계 + 매일 20시 알림톡 구매확정 안내 잡

### 빅스텝에듀케이션 — 백엔드 인턴 · 2021.05 ~ 2021.06

- 한 달 MVP — PDF 솔루션 구독료 연 300만원을 S3 직접 서빙으로 대체

## Tech Stack

| 영역 | 도구 |
|---|---|
| **Languages** | Kotlin · Java · TypeScript · Python (Django/DRF) |
| **Backend** | Spring Boot · Spring Batch · JPA · Querydsl · Nest.js · Celery |
| **Datastore** | MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ |
| **Infra** | AWS (S3 · CloudFront · MediaConvert · EventBridge · SQS · RDS · ECS · OpenSearch · ElastiCache · EKS) · Docker · Kubernetes · Jenkins · Ansible |
| **Testing** | JUnit5 · MockK · Kotest · RestDocs (KotlinDSL) · K6 |
| **Learning** | Rust + Axum |

## Contact

- GitHub — [@gyeongjae-ham](https://github.com/gyeongjae-ham)
- Email — gyeongjae.h.dev@gmail.com
