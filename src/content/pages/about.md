---
title: About
description: Kotlin·Spring과 Python·Django로 일하는 백엔드 개발자 함경재(Luca)의 경력과 문제 해결 사례입니다.
---

안녕하세요, 백엔드 개발자 **함경재 (Luca)** 입니다. Kotlin·Spring으로 주문과 외부 연동을 다뤘고, 현재는 Python·Django 기반 커머스에서 조회 성능과 주문·혜택의 정합성을 개선하고 있습니다.

## 먼저 읽어볼 작업

- [주문 상세에서 반복 쿼리를 줄인 과정](/posts/order-detail-prefetch-exists/): 응답에 필요한 정보부터 정하고, 항목 수가 늘어도 옵션 조회가 반복되지 않도록 바꿨습니다.
- [첫 무료교환 혜택을 주문별로 추적하기](/posts/first-exchange-benefit-ledger/): 취소와 재사용이 엇갈릴 때 다른 주문의 혜택을 복원하지 않도록 사용 이력을 나눴습니다.
- [앱 푸시가 도착하지 않는 원인 찾기](/posts/push-delivery-three-boundaries/): 토큰, 수신 권한, 발송 시나리오를 나눠 조사하고 iOS 실제 수신까지 확인했습니다.
- [영상 변환과 공개 상태 분리](/posts/athlog-video-hls-redesign/): 2026년 5월 BIND의 athlog에 ffmpeg·Celery 기반 HLS 변환을 구현하고 테스트 서버에서 검증했습니다. 첫 재생 1초 이내는 목표이며 실측 성과로 제시하지 않습니다.

## Experience

### BIND — 백엔드 · 2026.01 ~ 재직중

- **스택** Python · Django 3.2 · DRF · Celery · MySQL · Redis · AWS (ECS Fargate · OpenSearch · ElastiCache) · Kotlin · Spring Boot
- **Celery 안정화** 특정 시간대 워커 부하를 추적하고 rate limit · 실행 시간 분산 · 오토스케일링 설계
- **Queue 분리** 단일 default → `high` / `default` / `low` 3-Queue + ECS Service 독립 스케일링
- **Ephemeral 환경** PR 단위 `pr-{n}.dev` 자동 배포·정리 (Fargate Spot + ACM + 동적 ALB)
- **관측성 재설계** Sentry 4xx 필터링 + 전역 `EXCEPTION_HANDLER` + 구조화 로깅 (4개 PR 단계화)
- **Kotlin 이전 도커화** jlink와 다단계 빌드로 런타임 이미지 구성
- **athlog 영상 변환** S3 · CloudFront · ffmpeg · Celery 기반 비동기 처리와 공개 상태 관리

### 위밋모빌리티 — 백엔드 주임 · 2024.10 ~ 2026.01

- **스택** Kotlin · Spring Boot 3 · MySQL · Querydsl · MongoDB · Redis · K6 · Kubernetes · AWS
- **성능** 대용량 주문 등록의 배치 처리 · 쿼리 분할과 페이지네이션 · 테스트 병렬 실행 개선
- **부하 대응** K6 부하 테스트를 바탕으로 Pod 리소스와 수 조정
- **사내 표준화** `ObjectMapper` 라이브러리화 · Querydsl `@QueryProjection` 통일 · RestDocs KotlinDSL

### 라이너스 — 백엔드 선임 · 2023.07 ~ 2024.09

- **스택** Kotlin · Spring Boot 3 · Spring Batch · JPA · Jenkins · Ansible · Canvas LMS
- **솔루션 도입** 금오공과대 · 한일장신대 · 차의과학대 · 경복대 · 대덕대 등 다수 대학
- **성능·신뢰성** 외부 API 연동의 병렬 처리와 사전 집계 · 테스트 실행 개선 · 출결 처리 모듈 분리
- **아키텍처** JWT 다중 컨테이너 로그인 · 멀티 모듈 분리 · 단방향 의존
- **인프라** Jenkins + Ansible Playbook CI/CD 파이프라인 구축

### 레인보우8 — 백엔드 · 2021.12 ~ 2022.11

- Java · Spring Framework · React
- PHP 회사 홈페이지 3개를 Java/Spring + React 로 마이그레이션
- Google reCAPTCHA를 도입해 스팸 요청 차단

### 쿠돈 — 백엔드 · 2021.07 ~ 2021.10

- 1회성 쿠폰 발행 흐름 설계 + 매일 20시 알림톡 구매확정 안내 잡

### 빅스텝에듀케이션 — 백엔드 인턴 · 2021.05 ~ 2021.06

- 한 달 MVP — PDF 솔루션 구독료 연 300만원을 S3 직접 서빙으로 대체

## Tech Stack

| 영역          | 도구                                                                                                               |
| ------------- | ------------------------------------------------------------------------------------------------------------------ |
| **Languages** | Kotlin · Java · TypeScript · Python (Django/DRF)                                                                   |
| **Backend**   | Spring Boot · Spring Batch · JPA · Querydsl · Nest.js · Celery                                                     |
| **Datastore** | MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ                                                                    |
| **Infra**     | AWS (S3 · CloudFront · SQS · RDS · ECS · OpenSearch · ElastiCache · EKS) · Docker · Kubernetes · Jenkins · Ansible |
| **Testing**   | JUnit5 · MockK · Kotest · RestDocs (KotlinDSL) · K6                                                                |
| **Learning**  | Rust + Axum                                                                                                        |

## Contact

- GitHub — [@gyungjae-ham](https://github.com/gyungjae-ham)
- Email — gyeongjae.h.dev@gmail.com
