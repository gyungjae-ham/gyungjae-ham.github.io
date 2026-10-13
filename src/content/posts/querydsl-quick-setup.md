---
author: "luca"
pubDatetime: 2023-05-18T13:10:50+09:00
modDatetime: 2026-10-13T15:36:23+09:00
title: "Spring Boot 3에서 QueryDSL Q 타입 생성하기"
slug: "querydsl-quick-setup"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "setup", "gradle"]
description: "QueryDSL 의존성을 넣어도 QMember가 없을 수 있습니다. 라이브러리와 annotation processor의 역할을 나눠 Gradle 설정과 생성 결과를 확인합니다."
---

QueryDSL 예제를 따라 `QMember.member`를 작성했는데 IDE에 QMember가 없다는 오류가 표시될 수 있습니다. Member 엔티티는 직접 작성하지만, QMember는 엔티티를 읽은 annotation processor가 컴파일 과정에서 생성하기 때문입니다. 라이브러리 의존성만 추가하는 것과 생성 도구를 연결하는 것은 별도 작업입니다.

생성된 Q 타입을 사용하면 필드명과 타입을 코드로 참조할 수 있습니다. 엔티티의 필드를 바꿨을 때 관련 쿼리의 오류를 컴파일 단계에서 찾기 쉬워집니다. 다만 DB가 지원하는 문법이나 실행 성능까지 컴파일러가 보장하지는 않습니다.

아래는 **Java 17·Spring Boot 3.0.x·QueryDSL 5.0.0**의 Gradle Groovy 설정 예시입니다. Boot의 dependency management가 적용되어 있다고 가정합니다. 최신 버전 권장값이 아닌 이 글의 재현 기준이며, Boot 2의 `javax.persistence` 조합과 섞지 않습니다.

## 라이브러리와 생성 도구를 같은 조합으로 맞추기

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'com.querydsl:querydsl-jpa:5.0.0:jakarta'
    annotationProcessor 'com.querydsl:querydsl-apt:5.0.0:jakarta'
    annotationProcessor 'jakarta.annotation:jakarta.annotation-api'
    annotationProcessor 'jakarta.persistence:jakarta.persistence-api'
}
```

라이브러리와 annotation processor의 QueryDSL 버전을 맞추고 `jakarta` classifier를 함께 사용합니다. `querydsl-collections`는 메모리 컬렉션용 모듈이므로 JPA 사용만을 위해 추가할 필요는 없습니다. [QueryDSL 5의 Jakarta 지원](https://github.com/querydsl/querydsl/releases/tag/QUERYDSL_5_0_0)

## IDE 표시보다 컴파일 결과를 먼저 확인하기

Gradle의 기본 annotation processing 생성 경로를 우선 사용하면 별도 생성 디렉터리를 소스 트리에 넣는 설정을 줄일 수 있습니다. IDE에서만 Q 타입을 못 찾으면 Gradle 컴파일 결과와 IDE 빌드 위임 설정을 나눠 확인합니다. 생성 파일을 소스와 빌드 경로 양쪽에 중복으로 포함하지 않습니다.

먼저 `./gradlew clean compileJava`를 실행해 Q 타입이 생성되는지 확인합니다. 이 명령도 실패한다면 의존성과 엔티티 어노테이션 조합을 확인하고, 컴파일은 성공하는데 IDE만 오류를 표시한다면 IDE의 생성 경로 인식 문제를 살펴봅니다. 생성된 Q 타입으로 쿼리를 작성하는 예시는 [QueryDSL 기본 조회](/posts/querydsl-setup-and-basics/)에 이어서 정리했습니다.
