---
author: "luca"
title: "ObjectMapper 의 예외 계층을 잘못 잡고 있었다 — JsonProcessingException 과 JsonMappingException 의 진짜 관계"
description: "JsonProcessingException 과 JsonMappingException 을 따로 catch 했는데 후자는 닿지도 않는 코드였습니다. 예외 계층을 정확히 보지 않은 채로 catch 를 늘리던 습관을 정리하고, Wrapper 패턴으로 정돈합니다."
slug: "objectmapper-exception-hierarchy"
tags: ["spring", "objectmapper", "jackson", "exception-handling", "error-handling", "kotlin"]
pubDatetime: 2024-12-25T12:13:00+09:00
modDatetime: 2026-05-23T00:00:00+09:00
featured: false
draft: false
---

> 이 글은 ObjectMapper 시리즈 3편의 2편입니다. 1편은 ObjectMapper 가 Spring MVC 의 어느 자리에 살고 있는지를 다뤘습니다 (slug: objectmapper-where-in-spring-mvc).

그때는 `JsonMappingException` 을 별도 catch 로 잡고 있었지만, 그건 `JsonProcessingException` 의 자식이라 닿지도 않는 코드였습니다. "예외 계층을 정확히 보지 않은 채로 catch 를 늘리는 것" 이 가장 위험합니다. 다음 코드가 그때의 모양입니다.

```kotlin
try {
    objectMapper.readValue(request, A::class.java)
} catch (e: JsonProcessingException) {
    throw CoreException(ExceptionCode.FAILED_PARSE_JSON)
} catch (e: JsonMappingException) {
    throw CoreException(ExceptionCode.FAILED_MAP_TO_SCHEMA)
}
```

부모 catch 가 먼저 걸리면 자식 catch 는 영원히 도달하지 않습니다. Java/Kotlin 의 catch 순서 규칙입니다. 알면서도 라이브러리 예외 계층을 직접 확인하지 않은 채 "그래도 두 개 다 잡아두면 안전하지 않을까" 라고 작성한 결과였습니다.

## JsonProcessingException 의 정체

`JsonProcessingException` 은 Jackson 라이브러리가 JSON 을 처리할 때 발생하는 가장 기본적인 부모 예외입니다.

- JSON 문법이 잘못된 경우 (괄호 누락, 콤마 위치 오류 등)
- JSON 문자열이 중간에 끊긴 경우
- 입출력 작업 중 에러가 발생한 경우

이 예외가 발생하는 영역은 대부분 **클라이언트가 보낸 데이터의 문제** 입니다. 개발자가 코드 레벨에서 사전에 제어할 수 있는 영역이 아니라, 사용자 측 휴먼 에러나 네트워크 사건에 가깝습니다. 그래서 이 예외를 완전히 제거하는 일은 불가능합니다. 무엇을 catch 하느냐의 문제로 좁혀집니다.

## JsonMappingException 은 자식이었습니다

`JsonMappingException` 은 Jackson 2.10 부터 `DatabindException` 을 상속하고, `DatabindException` 은 다시 `JsonProcessingException` 을 상속합니다. 계층은 다음과 같습니다.

- `JsonProcessingException`
  - `DatabindException`
    - `JsonMappingException`

그러니까 위의 코드는 두 줄짜리 catch 가 아니라 **사실상 한 줄짜리 catch** 였습니다. 부모를 먼저 잡으면서 자식 catch 를 무력화하고 있었던 셈입니다. 자식만 따로 잡고 싶었다면 자식을 먼저 써야 합니다. 다만 그렇게 분기를 늘리는 게 정말로 의미가 있는지부터 묻는 편이 낫습니다.

## ObjectMapper 의 핵심 설정 옵션

try-catch 로 예외를 처리하는 대신, **ObjectMapper 의 설정으로 예외 발생 자체를 제거** 할 수 있는 영역이 있습니다. 카테고리별 옵션을 전부 나열할 수도 있지만, 실무에서 가장 자주 쓰는 다섯 개로 좁히면 다음과 같습니다.

| 옵션 | 효과 | 언제 켜는가 |
|---|---|---|
| `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES = false` | 알 수 없는 필드를 무시 | 클라이언트가 잉여 필드를 자주 보낼 때 |
| `SerializationFeature.WRITE_DATES_AS_TIMESTAMPS = false` | 날짜를 ISO-8601 로 직렬화 | 프론트와 시간 포맷을 맞출 때 |
| `JavaTimeModule()` 등록 | `LocalDateTime` 등 Java 8 시간 타입 지원 | Kotlin/Java 17 환경 기본 세팅 |
| `PropertyNamingStrategies.SNAKE_CASE` | snake_case 와 camelCase 자동 변환 | 외부 API 명명 규칙과 다를 때 |
| `DeserializationFeature.ACCEPT_SINGLE_VALUE_AS_ARRAY = true` | 단일 값을 배열로 받기 | 일부 클라이언트가 길이 1 배열을 단일 값으로 보낼 때 |

이 다섯 가지만 잘 설정해도 매핑 단계에서 던져지는 예외의 대부분이 사라집니다. **설정으로 막을 수 있는 예외를 catch 로 막는 일이 잦았다** 가 자기 개정의 핵심입니다.

## Wrapper 로 정돈하기

설정으로 막을 수 없는 영역, 즉 진짜로 JSON 자체가 깨진 경우는 결국 try-catch 가 필요합니다. 다만 그 try-catch 가 **호출 지점마다 흩어지는 것** 이 문제이지, try-catch 자체가 문제는 아닙니다. 한 군데로 모으면 됩니다.

```kotlin
@Component
class JsonConverter(private val objectMapper: ObjectMapper) {

    fun <T : Any> fromJson(json: String, type: Class<T>): Optional<T> =
        try {
            Optional.ofNullable(objectMapper.readValue(json, type))
        } catch (e: JsonProcessingException) {
            log.error("JSON 변환 실패: {}", e.message)
            Optional.empty()
        }

    fun toJson(value: Any): Optional<String> =
        try {
            Optional.ofNullable(objectMapper.writeValueAsString(value))
        } catch (e: JsonProcessingException) {
            log.error("JSON 변환 실패: {}", e.message)
            Optional.empty()
        }

    companion object {
        private val log = LoggerFactory.getLogger(JsonConverter::class.java)
    }
}
```

- **`Optional<T>` 반환**: 호출부가 `orElseThrow()` 또는 `orElseGet()` 으로 분기를 명시하도록 강제합니다.
- **`JsonProcessingException` 한 줄**: 자식 예외까지 한 번에 받습니다. 더 늘릴 이유가 없습니다.
- **로그 일관성**: 어디서 변환에 실패했든 한 위치에서 로깅됩니다.

사용은 다음과 같이 호출부가 책임을 명시하는 모양이 됩니다.

```kotlin
fun processUser(jsonData: String): User =
    jsonConverter.fromJson(jsonData, User::class.java)
        .orElseThrow { BusinessException("유효하지 않은 JSON 데이터") }
```

호출부마다 try-catch 두 줄이 흩어지지 않고, 변환의 책임이 한 컴포넌트 안에 모입니다.

## 그래서 어떻게 시작하는가

예외 catch 가 두 줄 이상 늘어났다면, 그건 예외 계층을 다시 봐야 한다는 신호입니다. 두 예외가 부모-자식이라면 자식 catch 는 닿지 않습니다. 둘이 형제라면 분기 자체가 의미를 가지는지 다시 묻습니다. 대부분의 경우 답은 "부모 하나로 충분하다" 입니다.

옛 글에는 "ObjectMapper 의 모든 예외를 잡고 싶다" 고 적었는데, 실제로는 "ObjectMapper 의 모든 예외가 결국 `JsonProcessingException` 의 자식들이라 한 줄이면 끝난다" 가 정확합니다. 한 줄 조언: catch 줄을 늘리기 전에 예외의 부모를 먼저 본다.

다음 글에서는 같은 `MappingJackson2HttpMessageConverter` 가 클라이언트 사이드에서 일으킨 사이드 이펙트 — RestClient 의 청크 전송 사건을 정리합니다 (slug: restclient-chunked-transfer).
