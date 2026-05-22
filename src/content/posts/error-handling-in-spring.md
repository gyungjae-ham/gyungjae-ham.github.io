---
author: "luca"
pubDatetime: 2023-08-16T22:18:56+09:00
title: "Spring 에서 Error 응답을 일관되게 다루는 방법"
slug: "error-handling-in-spring"
featured: false
draft: false
tags: ["error-handling", "spring", "dto", "rest-api", "kotlin"]
description: "Spring 의 예외를 한 곳에서 받아 일관된 ErrorResponse 로 내려주는 패턴과, 5-6년차 시각에서 본 ErrorCode 의 함정·운영 관점 보강."
---

> 2023-08 에 velog 에 정리한 글을 5-6년차 백엔드 시각으로 다시 손본 글입니다. 그때는 "그냥 이렇게 쓰면 되는 것" 으로 적었던 부분에, 지금은 보이는 운영상의 함정을 함께 적었습니다.

프론트와 서버가 에러 응답 포맷을 두고 매번 핑퐁을 친 적이 있습니다. 어떤 API 는 `{"error": "..."}` 를 내려주고, 어떤 API 는 `{"message": "..."}` 를 내려주고, 어떤 API 는 그냥 500 만 뱉는 식이었습니다. 클라이언트는 매 API 마다 분기 처리를 하느라 지치고, 서버 코드는 `try-catch` 가 컨트롤러마다 흩어져 있었습니다. 이건 단순히 "에러 처리 코드가 부족하다" 가 아니라 **에러 응답이 도메인 경계를 못 가졌다는 신호**입니다.

## 목표 — 모든 에러가 같은 모양으로 내려간다

Spring 에서 에러 응답을 일관되게 만드는 출발점은 다음 네 가지입니다.

- 클라이언트가 어떤 API 든 같은 스키마로 에러를 받습니다 — `ErrorResponse` 라는 단일 DTO.
- 컨트롤러는 예외 처리 코드를 가지지 않습니다 — `@RestControllerAdvice` 한 군데로 모읍니다.
- 비즈니스 규칙 위반은 `BusinessException` 으로 모입니다 — 표준 자바 예외와 구분합니다.
- 에러 식별자는 `ErrorCode` enum 으로 관리합니다 — 메시지, HTTP status, 코드 문자열을 한 곳에서.

이 네 가지를 갖춰두면 새 API 가 추가되어도 에러 응답은 같은 결로 따라옵니다.

## ErrorCode — 모든 에러의 단일 출처

`ErrorCode` 는 enum 으로 정의합니다. HTTP status, 코드 문자열, 메시지를 하나로 묶는 것이 핵심입니다.

```kotlin
enum class ErrorCode(
    val httpStatus: HttpStatus,
    val code: String,
    val message: String,
) {
    // 공통
    INVALID_INPUT_VALUE(HttpStatus.BAD_REQUEST, "C001", "유효하지 않은 입력입니다"),
    METHOD_NOT_ALLOWED(HttpStatus.METHOD_NOT_ALLOWED, "C002", "허용되지 않은 메서드입니다"),
    INTERNAL_SERVER_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "C999", "서버 에러가 발생했습니다"),

    // 도메인 — User
    USER_NOT_FOUND(HttpStatus.NOT_FOUND, "U001", "사용자를 찾을 수 없습니다"),
    DUPLICATE_EMAIL(HttpStatus.CONFLICT, "U002", "이미 사용 중인 이메일입니다"),

    // 도메인 — Order
    OUT_OF_STOCK(HttpStatus.CONFLICT, "O001", "재고가 부족합니다"),
    PAYMENT_FAILED(HttpStatus.PAYMENT_REQUIRED, "O002", "결제에 실패했습니다"),
}
```

- **prefix 로 도메인 구분** — `C` (공통), `U` (User), `O` (Order) 식으로 코드 prefix 를 도메인별로 두면, 클라이언트가 어디서 발생한 에러인지 즉시 파악합니다.
- **번호 자릿수 통일** — `C001` 같이 3자리 숫자로 통일해야 정렬·로그 grep 이 편합니다.
- **메시지는 사용자 친화적으로** — `ErrorCode` 의 `message` 는 그대로 클라이언트에 노출될 가능성이 높습니다. 기술 용어 (예: "NULL pointer") 가 들어가면 곤란합니다.

## BusinessException — 비즈니스 규칙 위반 신호

`BusinessException` 은 `RuntimeException` 을 상속합니다. 이유는 명확합니다.

- Spring 의 트랜잭션은 **`unchecked exception` 일 때만 자동 롤백** 합니다. `checked exception` 으로 두면 명시적으로 `rollbackFor` 를 지정해야 합니다.
- 비즈니스 규칙 위반은 호출자가 매번 `try-catch` 로 받을 만한 종류가 아닙니다. unchecked 가 결에 맞습니다.

```kotlin
open class BusinessException(
    val errorCode: ErrorCode,
    cause: Throwable? = null,
) : RuntimeException(errorCode.message, cause)

// 도메인별로 의미를 살린 하위 예외
class OutOfStockException : BusinessException(ErrorCode.OUT_OF_STOCK)
class DuplicateEmailException : BusinessException(ErrorCode.DUPLICATE_EMAIL)
```

도메인별 하위 예외를 두는 이유는 `catch` 를 좀 더 의미적으로 잡고 싶을 때를 위해서입니다. 특히 결제·주문 같이 후속 보상 트랜잭션이 필요한 흐름에서는 예외 타입으로 분기를 떠야 하는 경우가 종종 생깁니다.

## ErrorResponse — 클라이언트가 받는 모양

`ErrorResponse` 는 클라이언트와의 계약입니다. 한 번 정한 모양은 쉽게 못 바꾸므로, 처음 디자인할 때 다음을 고려해야 합니다.

```kotlin
data class ErrorResponse(
    val code: String,
    val message: String,
    val errors: List<FieldError> = emptyList(),
    val timestamp: Instant = Instant.now(),
    val path: String? = null,
) {
    data class FieldError(
        val field: String,
        val value: String?,
        val reason: String,
    )
}
```

- **`code`** — `ErrorCode.code` 가 그대로 들어갑니다. 클라이언트는 메시지가 아니라 이 코드로 분기합니다.
- **`message`** — 사용자에게 보여줄 메시지. 다국어가 필요하면 클라이언트가 `code` 로 자체 번역.
- **`errors`** — `@Valid` 실패 시 필드별 에러 목록. 폼 화면에 필드별 표시할 때 필수.
- **`timestamp` · `path`** — 운영 중 장애 신고가 올 때 로그 대조용. 추가 비용은 거의 없으니 처음부터 넣는 것이 좋습니다.

옛 글에는 `code` 와 `message` 만 있었는데, 운영을 해보니 **`errors` 배열과 `timestamp`** 이 둘은 처음부터 깔아두는 것이 정답이었습니다.

## GlobalExceptionHandler — 한 곳에 모은다

`@RestControllerAdvice` 로 컨트롤러 전역의 예외를 한 클래스에서 받습니다.

```kotlin
@RestControllerAdvice
class GlobalExceptionHandler {

    private val log = LoggerFactory.getLogger(javaClass)

    // 1) @Valid / @Validated 실패
    @ExceptionHandler(MethodArgumentNotValidException::class)
    fun handleValidation(e: MethodArgumentNotValidException): ResponseEntity<ErrorResponse> {
        val fieldErrors = e.bindingResult.fieldErrors.map {
            ErrorResponse.FieldError(
                field = it.field,
                value = it.rejectedValue?.toString(),
                reason = it.defaultMessage ?: "유효하지 않은 값",
            )
        }
        val body = ErrorResponse(
            code = ErrorCode.INVALID_INPUT_VALUE.code,
            message = ErrorCode.INVALID_INPUT_VALUE.message,
            errors = fieldErrors,
        )
        return ResponseEntity.badRequest().body(body)
    }

    // 2) 비즈니스 예외
    @ExceptionHandler(BusinessException::class)
    fun handleBusiness(e: BusinessException): ResponseEntity<ErrorResponse> {
        log.warn("BusinessException: ${e.errorCode.code} - ${e.message}")
        val body = ErrorResponse(
            code = e.errorCode.code,
            message = e.errorCode.message,
        )
        return ResponseEntity.status(e.errorCode.httpStatus).body(body)
    }

    // 3) 지원하지 않는 HTTP method
    @ExceptionHandler(HttpRequestMethodNotSupportedException::class)
    fun handleMethodNotSupported(e: HttpRequestMethodNotSupportedException): ResponseEntity<ErrorResponse> {
        val body = ErrorResponse(
            code = ErrorCode.METHOD_NOT_ALLOWED.code,
            message = ErrorCode.METHOD_NOT_ALLOWED.message,
        )
        return ResponseEntity.status(HttpStatus.METHOD_NOT_ALLOWED).body(body)
    }

    // 4) 나머지
    @ExceptionHandler(Exception::class)
    fun handleUnexpected(e: Exception): ResponseEntity<ErrorResponse> {
        log.error("Unexpected exception", e)
        val body = ErrorResponse(
            code = ErrorCode.INTERNAL_SERVER_ERROR.code,
            message = ErrorCode.INTERNAL_SERVER_ERROR.message,
        )
        return ResponseEntity.internalServerError().body(body)
    }
}
```

### 로그 레벨을 예외 종류에 맞게

옛 글의 핸들러는 모든 예외를 `log.error` 로 찍었습니다. 이건 운영에서 큰 문제를 만듭니다.

- `BusinessException` 은 사용자의 잘못된 요청 (재고 없음, 이메일 중복) 인 경우가 대부분입니다 → `warn` 또는 `info`.
- `Exception` (분류 안 된 예외) 만 `error` 로 찍어야 알람·on-call 이 의미를 가집니다.

`log.error` 가 남발되면 Sentry 같은 도구는 "에러" 라는 단어의 무게를 잃습니다. 진짜 에러가 묻힙니다.

## 입력 검증 — `spring-boot-starter-validation`

요청 DTO 에 검증 어노테이션을 붙여 컨트롤러 진입 전에 거르는 것이 첫 번째 방어선입니다.

```kotlin
data class SignUpRequest(
    @field:Email(message = "유효한 이메일이 아닙니다")
    @field:NotBlank
    val email: String,

    @field:Size(min = 8, max = 30, message = "비밀번호는 8~30자")
    val password: String,

    @field:Min(0) @field:Max(120)
    val age: Int,
)

@PostMapping("/users")
fun signUp(@Valid @RequestBody request: SignUpRequest) { ... }
```

자주 쓰는 어노테이션을 정리하면 다음과 같습니다.

| 어노테이션 | 검사 내용 | 주의 |
|---|---|---|
| `@NotNull` | null 이 아닐 것 | Kotlin 에서는 타입으로 충분한 경우 많음 |
| `@NotEmpty` | null 아니고 길이 > 0 | 문자열·컬렉션 모두 적용 |
| `@NotBlank` | null 아니고 trim 후 길이 > 0 | 문자열 전용. 공백 문자열 거름 |
| `@Size(min, max)` | 길이 범위 | 문자열·컬렉션 |
| `@Email` | 이메일 형식 | RFC 와 정확히 일치하지는 않으니 강한 검증은 별도 |
| `@Min` / `@Max` | 숫자 범위 | 정수형 전용. 실수는 `@DecimalMin` |
| `@Pattern(regexp)` | 정규식 | 자주 쓰는 패턴은 별도 어노테이션으로 추출 권장 |

**Kotlin 에서 주의할 점** — `@field:` prefix 를 빠뜨리면 어노테이션이 생성자 파라미터에만 붙고 필드에는 안 붙어 검증이 무시될 수 있습니다. 항상 `@field:` 로 명시합니다.

## 함정과 트레이드오프

운영을 해보며 부딪힌 함정 몇 가지를 정리합니다.

### 1) `ErrorCode` 가 너무 커진다

도메인이 늘면 `ErrorCode` enum 이 수백 개가 됩니다. 한 파일 안에서 관리하기 어려워집니다.

- **도메인별 enum 분리** — `UserErrorCode`, `OrderErrorCode` 로 쪼개고, 공통 인터페이스 `ErrorCode` 를 두면 `GlobalExceptionHandler` 는 인터페이스에만 의존합니다.
- 단, **코드 prefix 는 전역에서 unique** 해야 합니다. 분리해도 prefix 충돌은 따로 관리해야 합니다.

### 2) 외부 API 호환성

이미 운영 중인 API 의 `ErrorResponse` 모양을 바꾸는 것은 거의 불가능합니다. 클라이언트가 그 모양에 맞춰져 있기 때문입니다.

- 처음 디자인할 때 **최소 1년 뒤를 가정**하고 필드를 깔아둡니다. `errors`, `timestamp` 가 그래서 필요합니다.
- 모양을 바꿔야 한다면 v2 API 로 새로 깔고, v1 은 deprecation 절차로 정리합니다.

### 3) 메시지 노출 위험

`Exception::class` 핸들러에서 `e.message` 를 그대로 응답에 넣으면 위험합니다.

- DB 예외의 message 는 종종 테이블명·컬럼명·쿼리 조각을 노출합니다.
- 분류되지 않은 예외는 **고정된 일반 메시지** ("서버 에러가 발생했습니다") 만 내려주고, 상세는 로그에만 남깁니다.

### 4) 상관관계 ID (correlation id) 가 빠지면 디버깅이 안 됩니다

운영 중 사용자가 "에러 났어요" 라고 신고했을 때, 우리가 그 요청을 어떻게 특정합니까. `timestamp` 만으로는 부족합니다.

- 요청마다 `X-Request-Id` 또는 `traceId` 를 부여하고, `ErrorResponse` 에도 같이 내려줍니다.
- 로그·APM·`ErrorResponse` 3곳에 같은 ID 가 있어야 사용자의 신고 1건을 추적할 수 있습니다.

## 그래서 어떻게 시작하는가

레거시 프로젝트에 적용한다면 다음 순서가 현실적입니다.

1. **`ErrorResponse` 와 `GlobalExceptionHandler` 부터** — 최소한의 모양으로 한 군데 깔아둡니다. 기존 컨트롤러의 `try-catch` 는 천천히 거둬도 됩니다.
2. **`BusinessException` 도입** — 새로 짜는 도메인부터 적용. 기존 코드는 강제로 마이그레이션하지 않습니다.
3. **`ErrorCode` enum 정리** — 처음에는 한 파일, 도메인 수가 늘면 분리.
4. **로그 레벨 정리** — `BusinessException` 은 `warn`, 분류 안 된 예외만 `error`.
5. **`@Valid` 적용** — 신규 컨트롤러부터. 기존 컨트롤러는 변경 시점에 함께.

순서를 지키는 이유는 **클라이언트와의 계약 (응답 모양) 을 먼저 안정화** 한 뒤 내부 구조를 정리해야 호환성 문제가 안 터지기 때문입니다.

## 정리

에러 처리는 "예외를 잡아 응답으로 만드는 코드" 가 아니라 **클라이언트와의 계약을 디자인하는 작업** 입니다. 한 번 잘못 디자인된 `ErrorResponse` 는 1년 뒤에도 그대로 따라옵니다. `ErrorCode` 의 prefix, `errors` 필드의 존재, 메시지의 노출 범위, `correlation id` — 이 네 가지는 처음부터 정해두는 것이 추후 비용을 가장 많이 줄여줍니다.

다음 글에서는 이 구조 위에서 외부 API 호출 실패·타임아웃을 어떻게 `ErrorCode` 로 묶고, `Resilience4j` 의 `CircuitBreaker` 와 `ErrorResponse` 를 어떻게 연결하는지 정리합니다.
