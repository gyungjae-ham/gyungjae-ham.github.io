---
author: "luca"
pubDatetime: 2023-05-18T13:10:50+09:00
modDatetime: 2026-10-06T18:18:44+09:00
title: "QueryDSL 설정 방법"
slug: "querydsl-quick-setup"
featured: false
draft: false
tags: ["학습노트", "querydsl", "jpa", "setup", "gradle"]
description: "Java 17·Spring Boot 3.0·QueryDSL 5.0의 jakarta 설정 예시입니다. 라이브러리와 annotation processor 버전, Q 타입 생성 경로를 함께 확인합니다."
---

QueryDSL JPA는 엔티티를 표현하는 Q 타입으로 JPQL을 작성하게 해 줍니다. 필드 이름과 타입 변경을 컴파일 단계에서 발견하기 쉽고, 검색 조건을 코드로 조합할 수 있습니다. 다만 DB별 지원 문법이나 실행 성능까지 컴파일러가 확인해 주지는 않습니다.

아래는 **Java 17·Spring Boot 3.0.x·QueryDSL 5.0.0**의 Gradle Groovy 설정 예시입니다. Boot의 dependency management가 적용되어 있다고 가정합니다. 최신 버전 권장값이 아닌 이 글의 재현 기준이며, Boot 2의 `javax.persistence` 조합과 섞지 않습니다.

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

Gradle의 기본 annotation processing 생성 경로를 우선 사용하면 별도 생성 디렉터리를 소스 트리에 넣는 설정을 줄일 수 있습니다. IDE에서만 Q 타입을 못 찾으면 Gradle 컴파일 결과와 IDE 빌드 위임 설정을 나눠 확인합니다. 생성 파일을 소스와 빌드 경로 양쪽에 중복으로 포함하지 않습니다.

`./gradlew clean compileJava`로 Q 타입이 생성되고 이를 참조하는 코드가 컴파일되는지 확인한 뒤, [기본 조회 예시](/posts/querydsl-setup-and-basics/)로 이어갑니다.
