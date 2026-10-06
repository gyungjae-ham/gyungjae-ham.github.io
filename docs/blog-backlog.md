# Obsidian 로그 블로그 편집 기록

2026-10-01에 작성·발행한 39편을 이직용 사례 글로 다시 검토했습니다. 36편은 본문·제목·소개를 다시 썼고, 1편은 관련 글에 통합했으며, 2편은 공개 목록에서 보류했습니다. 당시 공개 글은 기존 53편과 합쳐 89편이었습니다. 10월 3일 주간 발행 1편이 추가되어 현재 공개 글은 90편입니다.

## 편집 기준

문제 상황에서 시작해 선택 이유·변경 과정·검증 결과가 이어지도록 고쳤습니다. 생성 과정의 안내와 반복된 보고서 문구를 제거하고 원본에 있는 판단과 시행착오를 살렸습니다. 원본에 없는 감정·사전 검토·운영 성과는 추가하지 않았습니다. 짧은 사례는 길이를 억지로 늘리지 않았습니다.

발행일은 원본 작업일을 유지하며 모든 공개 글은 `draft: false`입니다. 로그 19는 월만 확인돼 6월 1일을 대표일로 사용합니다. 로그 24·47 통합 글은 가장 이른 작업일인 6월 24일이며, 본문에서 9월 후속 작업을 구분합니다.

## 다시 쓴 공개 글

| 원본 로그 | 발행일                 | 글                                                                                                                             | 대표 글 |
| --------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------- |
| 4         | 2026-03-24             | [245개 View를 건드리지 않고 예외 모니터링을 한곳으로 모으기](../src/content/posts/drf-exception-monitoring-decorator.md)       |         |
| 5         | 2026-05-19             | [인증번호를 서버로 옮기는 일보다 어려웠던 구버전 앱과의 공존](../src/content/posts/phone-verification-server-policy.md)        |         |
| 7         | 2026-05-27             | [새벽 오류 알림에서 디버깅을 시작할 수 있게 만들기](../src/content/posts/celery-scheduler-error-notifications.md)              |         |
| 8         | 2026-05-27             | [광고에서 본 상품을 보여주는 API에 캐시를 넣지 않은 이유](../src/content/posts/ad-landing-pinned-product.md)                   |         |
| 9         | 2026-05-26             | [첫 구매 TOP 20을 만들었는데 응답에는 15개만 남았다](../src/content/posts/new-user-first-purchase-ranking.md)                  |         |
| 10        | 2026-05-26             | [수량만 바꿨는데 장바구니가 재정렬된다면](../src/content/posts/cart-sort-preserve-user-context.md)                             |         |
| 12        | 2026-04-24             | [코딩 에이전트를 6주 쓰며 구현과 리뷰를 분리한 이유](../src/content/posts/coding-agent-harness-six-weeks.md)                   | 대표    |
| 13        | 2026-05-28             | [홈 API 하나에 47개 파일이 바뀌어서 설계를 되돌렸다](../src/content/posts/home-content-cache-invalidation.md)                  | 대표    |
| 14        | 2026-06-02             | [비로그인 장바구니의 DB 설계를 버리고 서버를 계산기로 남겼다](../src/content/posts/guest-cart-stateless-merge.md)              | 대표    |
| 18        | 2026-06-12             | [푸시 발송은 성공인데 알림이 오지 않았다](../src/content/posts/push-delivery-three-boundaries.md)                              | 대표    |
| 19        | 2026-06-01 (월 대표일) | [랭킹을 만들다 주문 집계가 DB 부하가 됐다](../src/content/posts/buyer-ranking-batch-query-plan.md)                             | 대표    |
| 20        | 2026-06-23             | [앱을 설치한 사람에게 설치 쿠폰을 약속하고 있었다](../src/content/posts/crm-segment-coupon-history.md)                         |         |
| 21·28     | 2026-06-11             | [색상 정제기를 고치다 카탈로그에서 빠진 상품을 찾았다](../src/content/posts/catalog-color-size-normalization.md)               |         |
| 22        | 2026-06-17             | [엑셀 업로드의 실패를 운영자가 다시 처리할 수 있게 만들기](../src/content/posts/product-tag-bulk-upload-history.md)            |         |
| 23        | 2026-06-18             | [리뷰에 도움돼요 정렬을 더했더니 JOIN이 곱으로 늘어났다](../src/content/posts/review-sort-subquery-aggregation.md)             |         |
| 24·47     | 2026-06-24             | [브랜드 N+1을 고치려다 공유 Serializer의 모든 호출부를 바꿨다](../src/content/posts/seller-brand-serializer-query-contract.md) |         |
| 25        | 2026-06-24             | [랭킹에 감점을 넣기 전에 점수의 소비처부터 따라갔다](../src/content/posts/brand-metadata-ranking-policy.md)                    |         |
| 26        | 2026-06-24             | [prefetch를 넣었는데 exists 쿼리는 그대로였다](../src/content/posts/order-detail-prefetch-exists.md)                           |         |
| 27        | 2026-07-01             | [동의어 반영을 재시도했더니 새 버전만 늘어났다](../src/content/posts/opensearch-synonym-package-reindex.md)                    | 대표    |
| 29        | 2026-07-02             | [인기검색어를 자동 갱신하되 빈 목록은 내보내지 않기](../src/content/posts/popular-search-batch-fallback.md)                    |         |
| 31        | 2026-07-31             | [테스트가 어느 MySQL에 붙을지 환경변수에 맡기지 않기로 했다](../src/content/posts/django-testcontainers-isolation.md)          |         |
| 32        | 2026-07-27             | [무료교환을 0원 결제로 만들지 않은 이유](../src/content/posts/first-exchange-benefit-ledger.md)                                |         |
| 33        | 2026-07-29             | [상품 카드의 리뷰 한 건 때문에 전체 리뷰를 읽고 있었다](../src/content/posts/product-list-remove-review-hydration.md)          |         |
| 34        | 2026-08-21             | [페이지는 복제됐는데 필터는 원본을 보고 있었다](../src/content/posts/page-copy-reference-remapping.md)                         |         |
| 35        | 2026-08-19             | [옵션 500개 제한을 넣어도 기존 상품은 수정할 수 있어야 했다](../src/content/posts/product-option-limit-order.md)               |         |
| 36        | 2026-08-24             | [리뷰를 나누어 옮길 때 미리보기 결과를 그대로 믿지 않았다](../src/content/posts/review-copy-split-move-plan.md)                |         |
| 37        | 2026-08-25             | [검색 실험에서 이긴 동작이 실험 종료와 함께 사라졌다](../src/content/posts/search-experiment-winner-baseline.md)               |         |
| 38        | 2026-08-25             | [장바구니에서 배송 안내를 읽었다고 실험에 배정되면 안 됐다](../src/content/posts/delivery-experiment-read-assignment.md)       |         |
| 39        | 2026-09-01             | [결제 timeout을 실패로 저장하면 재시도가 위험해진다](../src/content/posts/escrow-return-fee-uncertain-result.md)               |         |
| 40        | 2026-09-17             | [결제 안내의 SELECT는 열 번인데 한 SQL이 전체를 읽고 있었다](../src/content/posts/escrow-display-json-query-scope.md)          |         |
| 41        | 2026-09-10             | [최대 할인 쿠폰 하나가 사용자의 선택을 대신할 수는 없었다](../src/content/posts/cart-single-coupon-selection.md)               |         |
| 42        | 2026-09-15             | [중복키를 잡되 다른 데이터 오류까지 숨기지는 않기](../src/content/posts/recent-view-concurrent-insert-recovery.md)             |         |
| 43        | 2026-09-16             | [주문과 상품이 각각 존재해도 올바른 문의는 아니었다](../src/content/posts/seller-inquiry-order-membership.md)                  |         |
| 44        | 2026-09-28             | [브랜드 쿠폰의 조건을 결제·복원·정산까지 따라가기](../src/content/posts/seller-brand-coupon-scope-settlement.md)               |         |
| 45        | 2026-09-04             | [리뷰 규칙을 문서에 적었는데 실제 코드에는 적용되지 않았다](../src/content/posts/review-rules-ast-regression.md)               |         |
| 46        | 2026-09-02             | [가을 추천에 여름 상품이 남았는데 배치는 정상 완료였다](../src/content/posts/seasonal-candidates-catalog-name.md)              |         |

## 통합·보류

| 기존 글                                                                        | 결정              | 이유                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [브랜드 찜 수](blog-editorial-archive/brand-wish-count-batch-contract.md)      | 로그 24 글에 통합 | 공유 조회 계약과 표시 기준의 후속 사례로 연결했습니다.                                                                                                                                                                                                       |
| [CRM 도구 이관](blog-editorial-archive/crm-provider-migration-contract.md)     | 보류              | 결정 이유·검증 결과·협업 범위가 대부분 미확인인 원본 초안입니다. 사실을 보강하기 전에는 독립된 이직용 사례로 공개하지 않습니다.                                                                                                                              |
| [자동 댓글·경품](blog-editorial-archive/automated-comments-reward-boundary.md) | 보류              | 핵심 사례가 생성 댓글 운영이며, 기술 설명은 예약 실행과 경품 제외 흐름에 집중돼 있습니다. 이직용 대표 경험으로는 결제·혜택·실험 사례가 더 적합해 이번 공개 목록에서 제외합니다. 다시 쓰려면 생성 콘텐츠의 표시·운영 정책과 실제 결과를 함께 확인해야 합니다. |

이전 원고는 공개 콘텐츠 경로 밖에 보관했습니다. 통합 글의 기존 URL은 합친 글로, 보류 글의 기존 URL은 글 목록으로 연결합니다.

## 기존 글과 대응한 로그

| 원본 로그 | 기존 글                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------- |
| log:01    | [athlog-video-hls-redesign](../src/content/posts/athlog-video-hls-redesign.md)                       |
| log:02    | [instagram-content-sync-pipeline](../src/content/posts/instagram-content-sync-pipeline.md)           |
| log:03    | [focus-brand-hardcode-to-remoteconfig](../src/content/posts/focus-brand-hardcode-to-remoteconfig.md) |
| log:06    | [athlog-video-hls-redesign](../src/content/posts/athlog-video-hls-redesign.md)                       |
| log:15    | [personalized-home-product-list](../src/content/posts/personalized-home-product-list.md)             |
| log:16    | [age-based-category-personalization](../src/content/posts/age-based-category-personalization.md)     |
| log:17    | [crm-traffic-scheduled-autoscaling](../src/content/posts/crm-traffic-scheduled-autoscaling.md)       |

## 다음 자동 발행에서 확인할 것

[발행 대응표](../scripts/blog-publication-map.json)는 47개 번호 로그를 모두 연결합니다. `withheld_editorially`는 근거 보강 전 재발행하지 않을 상태이며, `merged_follow_up`은 이미 관련 글에 통합된 내용입니다. 해시 변경 시에는 기존 글 보완 필요 여부를 검토합니다. 번호 없는 인덱스·핵심가치·면접 자료는 별도 글로 생성하지 않습니다.

실제 배포 결과는 GitHub Actions의 `Deploy to GitHub Pages` 실행에서 확인합니다. 아래 검증 결과는 이 편집본의 로컬 검증입니다.

## 검증

- `npm run check`: 오류·경고·hint 0건.
- `npm run lint`: 통과.
- `npm run build`: 정적 사이트 생성 성공, 검색에 공개 글 89편 인덱싱.
- 편집 대상 39편: 36편 재작성·1편 통합·2편 보류 대응 검증.
- 재작성 36편: 발행일 유지, `draft: false`, HTML·RSS 포함, 내부 글 링크 확인.
- 제외 3편: RSS·검색에서 제거, 이전 주소의 정적 리다이렉트 확인.
- 원본 로그 47개: 해시 불변·중복 없는 대응표·대응 글 존재 검증.
- Prettier와 `git diff --check`: 통과.

## 2026-10-06 독자 맥락과 가독성 재편집

앞서 공개한 사례 글 36편과 10월 3일 자동 발행한 로그 48 글 1편, 총 37편의 본문을 다시 썼습니다. 나머지 기존 글 53편과 보류 원고는 이번 수정 범위에 포함하지 않았습니다.

- 원본 로그의 서비스 배경과 사용자 행동을 확인해 도입을 보완했습니다. 낯선 용어를 필요한 곳에서 설명하고 구체적 사례에서 구현 이유로 연결했습니다.
- 짧은 결론과 소제목의 반복, 과한 강조, 일반적인 마무리를 줄였습니다. 테스트 개수보다 확인한 동작을 설명하되 실제 측정 범위·리뷰 중·미병합 종료·검증 실패는 유지했습니다.
- 무료교환은 취소 후 재사용 사례를 중심으로 구성하고 별도 실험 배정 논점은 덜었습니다. 랭킹 글의 월 대표일 설명은 공개 본문에서 빼고 이 문서와 대응표에 유지했습니다.
- 기존 URL·작업일·대표 글·공개 상태와 통합·보류 결정을 유지했습니다. 로그 21·28 및 24·47의 통합 관계도 동일합니다.
- `.claude/voice-guide.md`에서 충돌하는 과거 고정 형식 규칙을 현재 기준으로 정리했습니다. 주간 운영 문서와 Paseo 예약 `62a0002b`에도 모든 글의 독자 관점 재독을 포함하도록 갱신하고 저장 상태를 재조회해 확인했습니다.

이번 글 수정은 원본 시스템 코드를 바꾸거나 당시의 테스트·운영 성과를 새로 측정한 작업이 아닙니다. 글에 남은 수치와 상태는 각 작업 기록의 확인 범위를 뜻합니다. 검증은 블로그의 날짜·범위·내용·형식·빌드와 실제 공개 반영에 대해 수행합니다.

### 이번 편집 검증

- 37편 본문·소개 수정, 나머지 53편 동일. 전체 90편의 발행일·URL·제목·태그·대표 글·`draft: false` 유지.
- 로그 48개 대응 관계와 통합·보류 상태 유지. 수정 글 내부 링크와 지침 참조 링크 확인.
- 변경 범위 Prettier, `git diff --check`, `npm run check`(오류·경고·힌트 0), `npm run lint`, `npm run build` 통과.
- 수정 37편의 생성 HTML 본문과 RSS 소개문 확인, RSS·검색 색인 90편 확인.
- Paseo 예약은 active, `0 10 * * 6`·`Asia/Seoul` 유지. 지시문 저장 후 재조회로 독자 관점 검토 기준 반영 확인. 다음 실행은 2026-10-10 10:00 KST이며 변경된 규칙으로 예약 작업을 즉시 실행하지는 않았습니다.
