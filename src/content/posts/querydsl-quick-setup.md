---
author: "luca"
pubDatetime: 2023-05-18T13:10:50+09:00
title: "QueryDSL 설정 방법"
slug: "querydsl-quick-setup"
featured: false
draft: false
tags: ["querydsl", "jpa", "setup", "gradle"]
description: "QueryDSL 의 특징과 build.gradle 의존성·QClass 생성 디렉터리 설정까지, 빠르게 훑는 설정 노트입니다."
---

> QueryDSL 을 프로젝트에 도입할 때 필요한 설정을 짧게 정리하는 글입니다.

## QueryDSL 이란

`QueryDSL` 은 HQL(Hibernate Query Language) 쿼리를 타입에 맞게 생성 및 관리할 수 있도록 도와주는 역할을 합니다. SQL 을 자바 코드처럼 작성할 수 있도록 해 줍니다.

## 특징

- 문자가 아닌 코드로 쿼리를 작성하기 때문에 **컴파일 시점에서 문법 오류가 발견** 됩니다.
- 자동완성 등 IDE 의 도움을 받을 수 있습니다.
- **동적 쿼리 작성이 편리합니다.** (여러 방법들 중에서 압도적으로 좋은 부분)
- 쿼리 작성 시 제약 조건 등을 메서드화해서 재사용할 수 있습니다.
- 도메인 타입과 프로퍼티를 안전하게 참조할 수 있으며, 도메인 타입의 리팩터링을 더 잘할 수 있습니다.

아쉽게도 `QueryDSL` 은 `Spring Initializr` 페이지에서는 추가할 수 없고, 직접 설치해줘야 합니다.

## 설정 방법

### 1. dependencies 부분

```gradle
// queryDSL 설정
// collections는 그렇게 중요한 부분은 아니고 jpa, core, apt 부분은 중요한 설정이다
implementation "com.querydsl:querydsl-jpa"
implementation "com.querydsl:querydsl-core"
implementation "com.querydsl:querydsl-collections"
annotationProcessor "com.querydsl:querydsl-apt:${dependencyManagement.importedProperties['querydsl.version']}:jpa"

// querydsl 사용하다 보면 나오는 에러 메시지 대응하는 설정
// java.lang.NoClassDefFoundError (javax.annotation.Generated) 대응코드
annotationProcessor "jakarta.annotation:jakarta.annotation-api"
// java.lang.NoClassDefFoundError (javax.annotation.Entity) 대응코드
annotationProcessor "jakarta.persistence:jakarta.persistence-api"
```

### 2. 전역 부분 설정

```gradle
// Querydsl 설정부
// QClass가 빌드 디렉토리에 들어가는데 원하는 위치에 꺼내기 위해서
// 꺼내는 이유는 Gradle이 탐색하는 영역과 intellij가 탐색하는 영역이 중복될 시
// 이미 찾은 클래스를 다시 찾아서 충돌이 나는 걸 방지하기 위해서
def generated = 'src/main/generated'

// 컴파일 시 querydsl QClass 파일 생성 위치를 지정
tasks.withType(JavaCompile) {
    options.getGeneratedSourceOutputDirectory().set(file(generated))
}

// java source set 에 querydsl QClass 위치 추가
sourceSets {
    main.java.srcDirs += [ generated ]
}

// gradle clean 시에 QClass 디렉토리 삭제
clean {
    delete file(generated)
}
```

> 해당 설정 내용은 Spring Boot 3.0 이상부터 수정되었습니다.
