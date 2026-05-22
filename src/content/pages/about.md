---
title: About
description: 5-6년차 Kotlin/Spring 백엔드 개발자 함경재(Luca). 대용량 트래픽 처리와 시스템 최적화 중심의 경력 요약입니다.
---

> 안녕하세요, 백엔드 개발자 **함경재 (Luca)** 입니다. 안정적이고 확장 가능한 서버 아키텍처에 관심이 있으며, **대용량 트래픽 처리와 시스템 최적화로 사용자 경험을 끌어올리는 일**에 집중하고 있습니다.

5년차 백엔드 개발자입니다. Kotlin · Spring Boot · JPA 위에서 일하며, 가장 큰 즐거움은 느린 코드의 진짜 병목을 찾아내 수치로 끌어내리는 일입니다. 이 블로그에는 설계 결정의 트레이드오프와 실측 수치를 함께 남깁니다.

## 임팩트가 컸던 일들

- **1,000건 주문 등록 60초 → 3~5초 (92% 단축)** — SQS 비동기 처리를 API 서버 직접 처리로 전환하고, 중간 임시 테이블을 제거하며, HashMap 기반 O(1) 중복 검사 + Batch Insert 까지 함께 적용했습니다. *(위밋모빌리티 / athlog 백엔드)*
- **외부 API 통합 42초 → 20ms** — 비효율 반복문 정리로 1차 42초 → 10초, Kotlin Coroutine `async` 병렬·비동기 호출로 2차 10초 → 3초, Spring Batch + MongoDB 적재로 3차 3초 → 20ms 까지 3단계 개선했습니다. *(라이너스 / LMS)*
- **Slow Query 1,200ms → 55ms** — Grafana · CloudWatch로 다운 시점 특정, 쿼리 분할로 1차 1,200ms → 150ms, 페이지네이션 도입으로 2차 150ms → 55ms. 주기적 서버 다운 이슈도 함께 해결했습니다. *(위밋모빌리티)*
- **테스트 실행 3분 20초 → 21초** — 병렬 실행 + 테스트 인스턴스 라이프사이클 단위 조정 + 모듈별 `SAME_THREAD` 분리. githooks 속도가 회복되어 팀 배포 빈도가 늘었습니다. *(위밋모빌리티)*
- **모듈 분리로 데이터 분실율 0%** — 줌 webhook · 동영상 출석 적재 · 출결 계산을 별도 서버로 분리해, 백엔드 재배포가 출결에 영향을 주지 않게 했습니다. *(라이너스)*
- **JWT + 분산 컨테이너 환경 로그인 유지** — Canvas LMS 등 다중 컨테이너 라운드로빈 환경에서 세션이 끊기지 않도록 `AccessToken` 자체 검증 + `RefreshToken` Redis 저장 구조를 도입했습니다. *(라이너스)*
- **athlog 영상 첫 프레임 5초+ → 1초 이내(목표)** — S3 presigned 업로드 + AWS MediaConvert HLS 적응형 트랜스코딩 + CloudFront + EventBridge 비동기 알림 파이프라인을 단독 설계했습니다. *(위밋모빌리티 / athlog)*

## 경력 한눈에

### 위밋모빌리티 — 백엔드 주임 (2024.10 ~ 재직중)

- **스택:** Kotlin 1.9 / Spring Boot 3 / MySQL 8 / Querydsl / MongoDB / Redis / K6 / Kubernetes / AWS
- **성능 개선:** 대용량 주문 92% 단축, Slow Query 95% 단축, 테스트 속도 90% 단축
- **부하 대응:** K6 부하 테스트로 Pod 리소스·수 재조정 → 피크 시점 timeout 0 달성
- **사내 표준 작업:** `ObjectMapper` 라이브러리화, Querydsl 사용 통일(`@QueryProjection`), RestDocs KotlinDSL 가독성 개선
- **athlog 영상 파이프라인:** S3 + MediaConvert + CloudFront + EventBridge 단독 설계·도입

### (주)라이너스 — 백엔드 선임 (2023.07 ~ 2024.09)

- **스택:** JDK 17/21 / Kotlin / Spring Boot 3 / Spring Batch / Spring Security / JPA / Querydsl / Docker / Jenkins / Ansible / Canvas LMS
- **솔루션 도입처:** 금오공과대학교 · 한일장신대학교 · 주안대학원학교 · 차의과학대학교 · 경복대학교 · 대덕대학교 등
- **성과:** 외부 API 통합 42초 → 20ms (3단계), 테스트 코드 실행 3분 → 25초, 모듈 분리 데이터 분실 0%
- **아키텍처:** JWT 다중 컨테이너 로그인, 멀티 모듈 분리, 의존 방향 단방향 정리
- **인프라:** Jenkins + Ansible Playbook 기반 CI/CD 파이프라인 구축

### (주)레인보우8 — 백엔드 (2021.12 ~ 2022.11)

- **스택:** Java / Spring Framework / React
- PHP 회사 홈페이지 3개를 Java/Spring + React 구조로 마이그레이션 (보안 취약 해소)
- Google reCAPTCHA 도입으로 일일 스팸 메일 100건 차단
- 사내 배너 관리 도구 개발로 배포 없이 공지 변경 가능

### (주)쿠돈 — 백엔드 (2021.07 ~ 2021.10)

- 1회성 쿠폰 발행 흐름 설계 (사용 여부를 쿠폰 테이블 유저 PK로 판별)
- 매일 20:00 알림톡 구매확정 안내 잡으로 CS 대응 부담 감소

### 빅스텝에듀케이션 — 백엔드 인턴 (2021.05 ~ 2021.06)

- PDF 솔루션 구독료 연 300만원을 S3 직접 서빙 + 프론트 보안 처리로 대체
- 한 달 인턴 팀(FE 2 · BE 3)으로 멘토링 플랫폼 MVP 출시

## 기술 스택

- **언어:** Kotlin · Java · TypeScript · Python (Django/DRF)
- **백엔드:** Spring Boot · Spring Batch · Spring Security · JPA · Querydsl · Nest.js · Celery
- **저장소:** MySQL · PostgreSQL · MongoDB · Redis · RabbitMQ
- **인프라:** AWS (S3 · CloudFront · MediaConvert · EventBridge · SQS · RDS · ElastiCache · EKS) · Docker · Kubernetes · Jenkins · Ansible · NCP
- **테스트·문서:** JUnit5 · MockK · Kotest · RestDocs (KotlinDSL) · K6 · Postman
- **학습 중:** Rust + Axum

## 글쓰기 원칙

이 블로그의 글은 다음 원칙으로 쓰여집니다.

- **수치 우선** — Before/After 를 가능한 한 정량으로 기록합니다. 추정과 실측을 구분해 표기합니다.
- **트레이드오프 기록** — 채택한 후보뿐 아니라 기각한 후보와 그 이유를 함께 남깁니다.
- **운영 관점** — 설계만큼이나 좀비 행·재시동·실패 처리·관측 같은 운영 디테일을 다룹니다.

## 연락

- GitHub: [@gyeongjae-ham](https://github.com/gyeongjae-ham)
- Email: gyeongjae.h.dev@gmail.com
- 이전 블로그: [velog @hiyeeluca](https://velog.io/@hiyeeluca/posts)
