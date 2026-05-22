---
title: About
description: 5-6년차 Kotlin/Spring 백엔드 개발자 함경재(Luca). 대용량 트래픽 처리와 시스템 최적화 중심의 경력 요약입니다.
---

> 안녕하세요, 백엔드 개발자 **함경재 (Luca)** 입니다. Kotlin · Spring Boot 위에서 일하며, 느린 코드의 진짜 병목을 찾아 수치로 끌어내리는 일을 좋아합니다.

## 임팩트가 컸던 일들

| 수치 | 무엇을 | 어디서 |
|---|---|---|
| **60초 → 3~5초** (92% ↓) | 1,000건 주문 등록 — SQS 비동기 → API 직접 전환 + 임시 테이블 제거 + Batch Insert | 위밋모빌리티 / athlog |
| **42초 → 20ms** | 외부 API 통합 3단계 — 반복문 정리 → Coroutine `async` → Spring Batch + MongoDB | 라이너스 / LMS |
| **1,200ms → 55ms** | Slow Query — Grafana로 다운 시점 특정 → 쿼리 분할 → 페이지네이션 | 위밋모빌리티 |
| **3분 20초 → 21초** | 테스트 실행 — 병렬 + 라이프사이클 + 모듈별 `SAME_THREAD` 분리 | 위밋모빌리티 |
| **분실율 0%** | 출결 데이터 — 줌 webhook · 동영상 · 출결 계산 별도 서버 분리 | 라이너스 |
| **5초+ → 1초 이내** (목표) | athlog 영상 첫 프레임 — HLS 적응형 + EventBridge 비동기 파이프라인 | 위밋모빌리티 / athlog |

## 경력

### 위밋모빌리티 — 백엔드 주임 · 2024.10 ~ 재직중

- **스택** Kotlin / Spring Boot 3 / MySQL / Querydsl / MongoDB / Redis / K6 / Kubernetes / AWS
- **성능** 대용량 주문 92% ↓ · Slow Query 95% ↓ · 테스트 속도 90% ↓
- **부하 대응** K6 부하 테스트로 Pod 리소스·수 재조정 → 피크 시점 timeout 0
- **사내 표준화** `ObjectMapper` 라이브러리화, Querydsl `@QueryProjection` 통일, RestDocs KotlinDSL 개선
- **athlog 영상 파이프라인** S3 + MediaConvert + CloudFront + EventBridge 단독 설계

### 라이너스 — 백엔드 선임 · 2023.07 ~ 2024.09

- **스택** Kotlin / Spring Boot 3 / Spring Batch / JPA / Querydsl / Jenkins / Ansible / Canvas LMS
- **솔루션 도입** 금오공과대 · 한일장신대 · 차의과학대 · 경복대 · 대덕대 등 다수 대학 LMS
- **성능·신뢰성** 외부 API 통합 42초 → 20ms, 테스트 3분 → 25초, 모듈 분리로 데이터 분실 0%
- **아키텍처** JWT 다중 컨테이너 로그인, 멀티 모듈 분리, 의존 방향 단방향 정리
- **인프라** Jenkins + Ansible Playbook 기반 CI/CD 파이프라인 구축

### 레인보우8 — 백엔드 · 2021.12 ~ 2022.11

- Java / Spring Framework / React
- PHP 회사 홈페이지 3개를 Java/Spring + React 로 마이그레이션
- Google reCAPTCHA 도입으로 일일 스팸 메일 100건 차단

### 쿠돈 — 백엔드 · 2021.07 ~ 2021.10

- 1회성 쿠폰 발행 흐름 설계, 매일 20시 알림톡 구매확정 안내 잡

### 빅스텝에듀케이션 — 백엔드 인턴 · 2021.05 ~ 2021.06

- 한 달 MVP — PDF 솔루션 구독료 연 300만원을 S3 직접 서빙 + 프론트 보안 처리로 대체

## 기술 스택

| 영역 | 도구 |
|---|---|
| **언어** | Kotlin · Java · TypeScript · Python (Django/DRF) |
| **백엔드** | Spring Boot · Spring Batch · Spring Security · JPA · Querydsl · Nest.js |
| **저장소** | MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ |
| **인프라** | AWS (S3 · CloudFront · MediaConvert · EventBridge · SQS · RDS · EKS) · Docker · Kubernetes · Jenkins · Ansible |
| **테스트·문서** | JUnit5 · MockK · Kotest · RestDocs (KotlinDSL) · K6 |
| **학습 중** | Rust + Axum |

## 글쓰기 원칙

- **수치 우선** — Before / After 를 가능한 한 정량으로 (추정·실측 구분 표기)
- **트레이드오프 기록** — 채택한 후보뿐 아니라 기각한 후보와 그 이유까지
- **운영 관점** — 좀비 행 · 재시동 · 실패 처리 · 관측 디테일까지

## 연락

- GitHub — [@gyeongjae-ham](https://github.com/gyeongjae-ham)
- Email — gyeongjae.h.dev@gmail.com
- 이전 블로그 — [velog @hiyeeluca](https://velog.io/@hiyeeluca/posts)
