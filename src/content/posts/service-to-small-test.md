---
author: "luca"
pubDatetime: 2023-07-15T19:43:49+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "Service 테스트에서 fake를 쓰면 편한 경우와 남는 검증"
slug: "service-to-small-test"
featured: false
draft: false
tags: ["학습노트", "testing", "unit-test", "mock", "fake", "spring", "kotlin"]
description: "Service를 직접 생성하는 테스트와 실제 DB 테스트를 나눕니다. fake의 편의성, mock으로 가능한 검증, 컨텍스트 캐시와 속도 비교의 조건을 다룹니다."
---

Service의 조건문 하나를 바꿨는데 전체 애플리케이션과 DB가 준비될 때까지 기다려야 한다면, 그 테스트가 무엇을 확인하는지 나눠볼 필요가 있습니다. 회원가입 규칙을 검증하는 테스트와 JPA 매핑을 검증하는 테스트는 같은 환경을 필요로 하지 않을 수 있습니다.

## Spring 없이 Service를 만들 수 있는가

생성자로 협력자를 받는 Service는 테스트에서 직접 생성할 수 있습니다. `JpaRepository`를 상속한 인터페이스도 mock할 수 있으므로 별도의 도메인 Repository를 만드는 것이 필수 조건은 아닙니다. 인터페이스를 추가하는 결정은 테스트뿐 아니라 애플리케이션이 저장소 API를 어디까지 알아야 하는지와 함께 봅니다.

시간은 `Clock.fixed`, 코드 생성은 고정된 값을 반환하는 대역으로 제어하면 만료 시점이나 메일 내용의 기대값을 명확하게 쓸 수 있습니다. 단순한 계산 객체까지 모두 추상화할 필요는 없습니다.

## fake를 쓰면 편한 시나리오

설명용 회원 저장소를 다음처럼 둘 수 있습니다. 이 구현은 각 테스트가 독립적으로 생성해 **단일 스레드에서 사용하는 대역**입니다.

```kotlin
data class TestUser(val id: Long, val email: String)

class InMemoryUsers {
    private val users = mutableMapOf<Long, TestUser>()
    private var nextId = 0L

    fun save(email: String): TestUser {
        val user = TestUser(++nextId, email)
        users[user.id] = user
        return user
    }

    fun findByEmail(email: String): TestUser? =
        users.values.firstOrNull { it.email == email }
}
```

이 대역은 저장 후 조회가 이어지는 테스트에서 매번 반환값을 다시 설정하지 않아도 됩니다. 그러나 DB의 unique 제약은 흉내내지 않습니다. ‘가입한 이메일로 다시 가입하면 Service가 거부한다’는 규칙과 ‘동시 가입에도 DB에서 중복이 생기지 않는다’는 보장은 따로 검증해야 합니다.

ID 생성만 `AtomicLong`으로 바꿔도 전체 Map과 조회·저장의 조합이 스레드 안전해지는 것은 아닙니다. 병렬 테스트에서는 인스턴스를 공유하지 않는 편이 단순합니다.

## mock으로도 같은 내용을 검증할 수 있다

메일 본문은 argument captor로, 두 번의 가입은 연속 응답이나 answer로 검증할 수 있습니다. fake의 장점은 mock으로 불가능한 기능을 여는 것이 아니라, 반복되는 상태 전이를 작은 구현으로 표현하는 데 있습니다. 어떤 방식이 더 읽기 쉽고 실제 계약과 덜 어긋나는지 비교합니다.

속도를 비교할 때도 범위를 맞춰야 합니다. Spring 테스트는 동일한 컨텍스트 설정을 재사용할 수 있으므로 매 메서드마다 부팅한다고 계산하지 않습니다. 최초 부팅을 포함한 전체 실행 시간과 이미 준비된 환경의 테스트 시간을 나눠 측정합니다. 예를 들어 20초와 0.05초의 비율은 400배지만, 서로 다른 검증 범위의 수치라면 그대로 개선율로 쓰기 어렵습니다.

쿼리·마이그레이션·트랜잭션·실제 어댑터는 통합 테스트에 남깁니다. Service의 빠른 피드백과 저장소의 실제 동작을 각각 확인하는 구성이 목적이며, 모든 테스트를 하나의 크기로 맞추는 작업은 아닙니다.
