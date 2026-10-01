# Obsidian 로그 블로그 작성 목록

2026-10-01 기준 번호 로그 47개를 대조했습니다. 기존 글로 대응한 로그는 7개이며, 나머지 40개 로그를 새 글 39편으로 작성했습니다. 카탈로그 정제 로그 21·28은 한 글로 통합했습니다.

새 글은 모두 `draft: false`이며 `pubDatetime`은 원본 로그의 본문 작업일 기준입니다. 작업 기간은 시작일, 통합 글은 가장 이른 작업일을 사용합니다. 실제 시각은 기록되어 있지 않아 00:00 KST로 통일했습니다. 랭킹 집계 글은 작업 월(2026-06)만 기록되어 2026-06-01을 대표일로 사용하며 정확한 일자는 미확인입니다. 이 문서는 저장소에 작성한 결과를 기록합니다. 실제 사이트 배포 상태는 GitHub Actions의 `Deploy to GitHub Pages` 실행 결과에서 확인합니다. 원본의 PR 상태·테스트·측정은 기록 당시의 근거로 설명하고, 운영 실측이나 완료로 확대하지 않았습니다. 원본 로그는 수정하지 않았습니다.

## 새 글 39편

| 원본 번호 | 발행 날짜 (KST) | 글 |
| --- | --- | --- |
| 04 | 2026-03-24 | [DRF 에러 모니터링 진입점을 두 곳에서 한 곳으로 줄이기](../src/content/posts/drf-exception-monitoring-decorator.md) |
| 05 | 2026-05-19 | [전화번호 인증을 서버로 옮기며 시도 횟수와 구버전 호환을 나누기](../src/content/posts/phone-verification-server-policy.md) |
| 07 | 2026-05-27 | [Celery와 Scheduler 오류 알림을 같은 흐름으로 읽게 만들기](../src/content/posts/celery-scheduler-error-notifications.md) |
| 08 | 2026-05-27 | [광고에서 본 상품을 랜딩 화면에서도 유지하기](../src/content/posts/ad-landing-pinned-product.md) |
| 09 | 2026-05-26 | [신규 유저 첫 구매 TOP 상품을 요청마다 집계하지 않기](../src/content/posts/new-user-first-purchase-ranking.md) |
| 10 | 2026-05-26 | [장바구니 정렬에서 담기와 수량 변경의 의도를 나누기](../src/content/posts/cart-sort-preserve-user-context.md) |
| 11 | 2026-04-06 | [CRM 발송 도구를 옮길 때 유지해야 하는 계약](../src/content/posts/crm-provider-migration-contract.md) |
| 12 | 2026-04-24 | [코딩 에이전트를 6주 운영하며 구현과 리뷰를 나누기](../src/content/posts/coding-agent-harness-six-weeks.md) |
| 13 | 2026-05-28 | [홈 콘텐츠 API를 줄이고 캐시 무효화 시점을 맞추기](../src/content/posts/home-content-cache-invalidation.md) |
| 14 | 2026-06-02 | [비로그인 장바구니를 서버에 저장하지 않기로 한 이유](../src/content/posts/guest-cart-stateless-merge.md) |
| 18 | 2026-06-12 | [푸시 API는 성공했는데 알림이 오지 않을 때](../src/content/posts/push-delivery-three-boundaries.md) |
| 19 | 2026-06-01 (월 기준 대표일) | [상품 랭킹을 만들다 집계 쿼리가 DB 부하가 되었을 때](../src/content/posts/buyer-ranking-batch-query-plan.md) |
| 20 | 2026-06-23 | [앱 설치 여부를 유효 쿠폰으로 판단하던 CRM 버그](../src/content/posts/crm-segment-coupon-history.md) |
| 21·28 | 2026-06-11 | [색상과 사이즈를 정제해 카탈로그에서 빠지는 상품을 줄이기](../src/content/posts/catalog-color-size-normalization.md) |
| 22 | 2026-06-17 | [상품 태그 엑셀 업로드에서 실패 행과 매핑 이력을 남기기](../src/content/posts/product-tag-bulk-upload-history.md) |
| 23 | 2026-06-18 | [리뷰 정렬에 도움돼요를 붙이다 JOIN 곱을 피하기](../src/content/posts/review-sort-subquery-aggregation.md) |
| 24 | 2026-06-24 | [브랜드 목록 N+1을 고치며 공유 Serializer의 계약을 맞추기](../src/content/posts/seller-brand-serializer-query-contract.md) |
| 25 | 2026-06-24 | [브랜드 운영 메타를 제외 정책과 랭킹 감점으로 나누기](../src/content/posts/brand-metadata-ranking-policy.md) |
| 26 | 2026-06-24 | [prefetch를 추가해도 주문 상세의 exists 쿼리가 남는 이유](../src/content/posts/order-detail-prefetch-exists.md) |
| 27 | 2026-07-01 | [OpenSearch 동의어 반영에서 재시도와 재색인의 책임을 나누기](../src/content/posts/opensearch-synonym-package-reindex.md) |
| 29 | 2026-07-02 | [인기검색어 갱신 중 빈 목록을 만들지 않기](../src/content/posts/popular-search-batch-fallback.md) |
| 30 | 2026-07-07 | [자동 생성 댓글이 경품 대상에 섞이지 않도록 경계를 찾기](../src/content/posts/automated-comments-reward-boundary.md) |
| 31 | 2026-07-31 | [Django 테스트 DB를 세션마다 격리된 MySQL로 준비하기](../src/content/posts/django-testcontainers-isolation.md) |
| 32 | 2026-07-27 | [무료교환 안내와 혜택 확정을 별도 판단으로 두기](../src/content/posts/first-exchange-benefit-ledger.md) |
| 33 | 2026-07-29 | [상품 카드의 리뷰 한 건을 위해 전체 리뷰를 읽고 있었다](../src/content/posts/product-list-remove-review-hydration.md) |
| 34 | 2026-08-21 | [페이지를 복제했는데 필터는 원본을 보고 있었다](../src/content/posts/page-copy-reference-remapping.md) |
| 35 | 2026-08-19 | [상품 옵션 조합의 상한과 표시 순서를 함께 관리하기](../src/content/posts/product-option-limit-order.md) |
| 36 | 2026-08-24 | [리뷰 복제와 이동을 나누고 실행 계획을 다시 검증하기](../src/content/posts/review-copy-split-move-plan.md) |
| 37 | 2026-08-25 | [검색 실험이 끝나자 이전 정렬로 돌아간 이유](../src/content/posts/search-experiment-winner-baseline.md) |
| 38 | 2026-08-25 | [당일배송 정보를 조회하는 것과 실험에 배정하는 것을 나누기](../src/content/posts/delivery-experiment-read-assignment.md) |
| 39 | 2026-09-01 | [결제 응답이 유실됐을 때 무조건 재시도하지 않기](../src/content/posts/escrow-return-fee-uncertain-result.md) |
| 40 | 2026-09-17 | [안내 화면이 결제 검증용 전역 JSON 조회를 쓰고 있었다](../src/content/posts/escrow-display-json-query-scope.md) |
| 41 | 2026-09-10 | [장바구니 쿠폰의 최대 할인과 사용자의 선택을 나누기](../src/content/posts/cart-single-coupon-selection.md) |
| 42 | 2026-09-15 | [최근 본 상품 저장의 중복키 충돌만 복구하기](../src/content/posts/recent-view-concurrent-insert-recovery.md) |
| 43 | 2026-09-16 | [주문 ID가 존재해도 문의의 상품이 그 주문 소속인지는 다르다](../src/content/posts/seller-inquiry-order-membership.md) |
| 44 | 2026-09-28 | [셀러·브랜드 쿠폰의 범위를 결제와 복원까지 유지하기](../src/content/posts/seller-brand-coupon-scope-settlement.md) |
| 45 | 2026-09-04 | [리뷰 규칙 문서가 실제 코드 경로에 적용되는지 검증하기](../src/content/posts/review-rules-ast-regression.md) |
| 46 | 2026-09-02 | [가을인데 여름 추천이 남은 원인은 카테고리 이름이었다](../src/content/posts/seasonal-candidates-catalog-name.md) |
| 47 | 2026-09-21 | [브랜드 찜 수를 일괄 집계하고 표시 기준을 맞추기](../src/content/posts/brand-wish-count-batch-contract.md) |

## 기존 글과 대응한 로그

| 원본 번호 | 대응 글 |
| --- | --- |
| 01·06 | [athlog HLS 재설계](../src/content/posts/athlog-video-hls-redesign.md) — 01의 초기 MediaConvert 설계는 기존 글에서 최종 변경 이유와 함께 다루므로 별도 중복 글을 만들지 않았습니다. |
| 02 | [인스타그램 자동 동기화](../src/content/posts/instagram-content-sync-pipeline.md) |
| 03 | [집중 브랜드 RemoteConfig 이관](../src/content/posts/focus-brand-hardcode-to-remoteconfig.md) |
| 15 | [홈 상품 구좌 개인화](../src/content/posts/personalized-home-product-list.md) |
| 16 | [카테고리 연령대 개인화](../src/content/posts/age-based-category-personalization.md) |
| 17 | [CRM 예약형 오토스케일링](../src/content/posts/crm-traffic-scheduled-autoscaling.md) |

## 발행 이력 연결

[발행 대응표](../scripts/blog-publication-map.json)에 로그 번호·원본 해시·블로그 파일을 기록했습니다. `existing_in_repository`와 `ready_in_repository`는 저장소 기준 상태입니다. 사이트 배포 확인을 대신하지 않습니다. 원본 해시가 변경되어도 같은 주제의 새 글로 자동 재발행하지 않고 기존 글의 수정 필요 여부를 검토해야 합니다.

번호 없는 인덱스·핵심가치 기준·면접 답변 모음은 작업 로그를 재정리한 보조 문서이므로 별도 블로그 글로 생성하지 않았습니다.

## 검증 결과

- `npm run check`: 오류·경고·hint 0건.
- `npm run build`: 정적 사이트 생성과 검색 인덱싱 성공, 전체 92편 인덱싱.
- 새 글 39편: 정적 HTML 생성·RSS 포함·사극체 및 원본 비공개 식별자 검사 통과.
- 번호 로그 47개: 중복 없는 대응표 검증 통과.
- 새 글·기존 글 전체 92편·대응표·이 문서의 Prettier 검사 통과. 기존 26편의 형식 경고는 2026-10-01에 수정했습니다.
