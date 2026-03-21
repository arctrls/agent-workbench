---
name: upgrade-springboot
description: Spring Boot 버전 업그레이드를 수행합니다. "Spring Boot 올려줘", "스프링 부트 업그레이드", "Spring Boot 4로 변경" 등의 요청 시 사용합니다. 마이너 버전 우선 업그레이드, 의존성 호환성 검사, 테스트 검증을 체계적으로 진행하고 상황에 맞는 PR 분할 전략을 제안합니다.
---

# Spring Boot 버전 업그레이드

프로젝트의 Spring Boot 버전을 목표 버전으로 안전하게 업그레이드합니다.

## 핵심 원칙

1. **마이너 먼저**: 메이저 업그레이드 전 반드시 현재 메이저의 최신 마이너로 먼저 업그레이드
2. **공식 문서 필독**: Release Notes와 Migration Guide를 반드시 확인
3. **작은 스텝**: 한 번에 큰 변경보다 단계적 업그레이드로 위험 최소화
4. **테스트 검증**: 매 단계마다 test + integrationTest 실행

## 작업 프로세스

### Phase 0: 분석 및 로드맵 수립

#### 1. 현재 상태 파악

다음 파일들에서 현재 버전 설정을 확인:

| 파일 | 확인 항목 |
|------|----------|
| `build.gradle.kts` / `build.gradle` | `org.springframework.boot` 플러그인 버전 |
| `build.gradle.kts` / `build.gradle` | `io.spring.dependency-management` 버전 |
| `build.gradle.kts` / `build.gradle` | Java `toolchain.languageVersion`, Kotlin `jvmTarget` |
| `build.gradle.kts` / `build.gradle` | Kotlin 플러그인 버전 |
| `gradle/wrapper/gradle-wrapper.properties` | `distributionUrl` (Gradle 버전) |
| `Dockerfile` | 베이스 이미지 (Java 버전) |
| `.github/workflows/*.yaml` | `java-version`, `java-distribution` |
| `.java-version` / `.jvmrc` | jenv/asdf 로컬 설정 |

현재 버전을 표로 정리하여 사용자에게 보고:

```
| 구성 요소            | 현재 버전  |
|--------------------|----------|
| Spring Boot        | x.y.z    |
| Java               | XX       |
| Kotlin             | x.y.z    |
| Gradle             | x.y.z    |
| Spring Dependency  | x.y.z    |
```

#### 2. 목표 버전 확인 및 경로 설계

사용자가 목표 버전을 명시하지 않은 경우 최신 안정 버전을 웹 검색으로 확인.

**중요: 메이저 업그레이드 요청 시 반드시 확인 질문**

사용자가 "최신 버전으로" 또는 메이저 업그레이드를 요청하면:

```
현재 Spring Boot X.Y.Z에서 A.B.C로의 업그레이드를 요청하셨습니다.

메이저 업그레이드는 Breaking Changes가 많아 위험할 수 있습니다.
다음과 같이 단계적으로 진행하는 것을 권장합니다:

1. X.Y.Z → X.최신.최신 (현재 메이저의 마이너 최신화)
2. (필요시) Gradle/Kotlin/Java 선행 업그레이드
3. Deprecated API 선제적 마이그레이션
4. X.최신.최신 → A.B.C (메이저 업그레이드)

이렇게 단계적으로 진행할까요, 아니면 한 번에 진행할까요?
```

#### 3. 공식 문서 조회

웹 검색으로 다음 문서들을 확인:

| 문서 | 검색 쿼리 | 확인 내용 |
|------|----------|----------|
| Release Notes | `Spring Boot X.Y Release Notes site:github.com/spring-projects` | 새 기능, 변경사항 |
| Migration Guide | `Spring Boot X.Y Migration Guide site:github.com/spring-projects` | Breaking changes, 마이그레이션 단계 |
| Configuration Changelog | `Spring Boot X.Y Configuration Changelog` | 속성명 변경 |

Migration Guide의 주요 항목을 요약하여 사용자에게 보고:

```
## Spring Boot X.Y 주요 변경사항

### Breaking Changes
- [ ] 항목1: 설명
- [ ] 항목2: 설명

### Deprecated → Removed
- [ ] 항목1
- [ ] 항목2

### 새로운 의존성 요구사항
- Java: XX 이상
- Gradle: X.Y 이상
- Kotlin: X.Y 이상
```

#### 4. 연관 의존성 호환성 전수조사

웹 검색으로 프로젝트에서 사용 중인 주요 의존성의 호환 버전 확인:

| 의존성 | 검색 쿼리 예시 |
|-------|--------------|
| MyBatis | `mybatis-spring-boot-starter Spring Boot X.Y compatibility` |
| Flyway | `flyway Spring Boot X.Y version` |
| Spring Cloud | `Spring Cloud Spring Boot X.Y compatibility matrix` |
| QueryDSL | `querydsl Spring Boot X.Y Hibernate Y version` |
| SpringDoc | `springdoc-openapi Spring Boot X.Y` |

호환성 매트릭스를 표로 정리:

```
| 의존성               | 현재 버전 | 목표 SB 호환 버전 | 조치 필요 |
|--------------------|---------|-----------------|---------|
| mybatis-starter    | 3.x     | 4.x             | 업그레이드 |
| flyway             | 9.x     | 10.x + starter  | 업그레이드 |
| spring-cloud       | 2023.x  | 2024.x          | 업그레이드 |
```

#### 5. 업그레이드 로드맵 및 PR 분할 제안

분석 결과를 바탕으로 전체 로드맵과 PR 분할 옵션을 제안:

```
## 업그레이드 로드맵

현재: Spring Boot X.Y.Z, Java XX, Gradle X.Y, Kotlin X.Y
목표: Spring Boot A.B.C

### 권장 경로

1. Spring Boot X.Y.Z → X.최신.최신 (마이너 최신화)
2. Gradle X.Y → A.B (목표 SB 요구사항)
3. Kotlin X.Y → A.B (목표 SB 요구사항)
4. Deprecated API 선제적 마이그레이션 (@MockBean → @MockitoBean 등)
5. 연관 의존성 호환 버전으로 업그레이드
6. Spring Boot X.최신.최신 → A.B.C (메이저 업그레이드)
7. Breaking Changes 적용 (패키지명 변경 등)

### PR 분할 옵션

프로젝트 상황에 따라 선택:

**옵션 A (보수적 - 대규모 프로젝트 권장)**
- PR 1: 마이너 버전 최신화
- PR 2: Gradle/Kotlin 선행 업그레이드
- PR 3: Deprecated API 마이그레이션
- PR 4: 메이저 버전 업그레이드 + Breaking Changes
- PR 5: Warning 해결 및 최적화

**옵션 B (중간 - 일반적인 경우)**
- PR 1: 선행 준비 (마이너 최신화 + Gradle/Kotlin)
- PR 2: 메이저 업그레이드 (Breaking Changes 포함)
- PR 3: 후속 정리 (Warning 해결)

**옵션 C (단일 PR - 소규모 프로젝트 또는 마이너 업그레이드)**
- 모든 변경을 하나의 PR로

어떤 방식으로 진행할까요?
```

---

### Phase 1: 선행 준비 (상황에 따라 생략 가능)

#### 6. Gradle Wrapper 업그레이드 (필요시)

```bash
# 현재 Gradle 버전 확인
./gradlew --version

# 최신 호환 버전으로 업그레이드
./gradlew wrapper --gradle-version=<target-version>
```

#### 7. Kotlin 버전 업그레이드 (필요시)

`build.gradle.kts` 수정:

```kotlin
plugins {
    val kotlinVersion = "<target-version>"
    kotlin("jvm") version kotlinVersion
    kotlin("plugin.spring") version kotlinVersion
    kotlin("plugin.jpa") version kotlinVersion
}
```

#### 8. Java 버전 업그레이드 (필요시)

Java 업그레이드가 필요한 경우 `/upgrade-java` skill 실행을 권장.

업그레이드 시 확인 사항:
- JDK 배포본(Corretto, Temurin 등)에 해당 버전 존재 여부
- Dockerfile 베이스 이미지
- GitHub Actions java-version
- .java-version (jenv)
- build.gradle toolchain 설정

#### 9. 선행 준비 검증

```bash
# 클린 빌드
./gradlew clean build -x test

# 단위 테스트
./gradlew test

# 통합 테스트
./gradlew integrationTest
```

---

### Phase 2: 마이너 버전 업그레이드 (메이저 전 필수)

#### 10. 마이너 버전 최신화

`build.gradle.kts` 수정:

```kotlin
plugins {
    id("org.springframework.boot") version "<current-major.latest-minor>"
    id("io.spring.dependency-management") version "<latest>"
}
```

#### 11. Deprecation Warning 수집

```bash
# 빌드하면서 deprecated 경고 수집
./gradlew clean build 2>&1 | grep -iE "deprecat|warning"

# 또는 상세 로그
./gradlew clean build --warning-mode all
```

#### 12. Deprecated API 선제적 마이그레이션

Migration Guide에서 deprecated → 대체 API 확인 후 선제적으로 변경:

| 기존 (Deprecated) | 대체 | 영향 파일 |
|------------------|-----|---------|
| `@MockBean` | `@MockitoBean` | 테스트 클래스 |
| `@SpyBean` | `@MockitoSpyBean` | 테스트 클래스 |
| `ClientHttpRequestFactories` | `ClientHttpRequestFactoryBuilder` | RestClient 설정 |

#### 13. 마이너 업그레이드 검증

```bash
./gradlew clean build
./gradlew test
./gradlew integrationTest
```

---

### Phase 3: 메이저 버전 업그레이드

#### 14. Spring Boot 버전 변경

```kotlin
plugins {
    id("org.springframework.boot") version "<target-major.minor.patch>"
}
```

#### 15. 연관 의존성 호환 버전 업그레이드

Phase 0에서 조사한 의존성들을 호환 버전으로 변경:

```kotlin
dependencies {
    // MyBatis - 호환 버전으로 변경
    implementation("org.mybatis.spring.boot:mybatis-spring-boot-starter:<compatible-version>")

    // Flyway - Spring Boot X에서 명시적 starter 필요할 수 있음
    implementation("org.springframework.boot:spring-boot-starter-flyway")

    // 기타 의존성...
}

dependencyManagement {
    imports {
        // Spring Modulith 등 BOM 버전 업그레이드
        mavenBom("org.springframework.modulith:spring-modulith-bom:<compatible-version>")
    }
}
```

#### 16. Breaking Changes 적용

Migration Guide 기반으로 Breaking Changes 적용:

**패키지명 변경 (예: Jackson 3)**
```bash
# 영향 범위 확인
grep -r "기존패키지" --include="*.java" --include="*.kt" | wc -l

# IDE 리팩토링 또는 수동 변경
```

**어노테이션 변경**
```java
// Before
import org.springframework.boot.test.mock.mockito.MockBean;

// After
import org.springframework.test.context.bean.override.mockito.MockitoBean;
```

**설정 속성 변경**
```yaml
# application.yml
# Migration Guide에서 변경된 속성 확인 후 수정
```

---

### Phase 4: 검증 및 마무리

#### 17. 전체 테스트 실행

```bash
# 단위 테스트
./gradlew test

# 통합 테스트
./gradlew integrationTest
```

#### 18. 이전 브랜치와 테스트 결과 비교

업그레이드로 인한 테스트 실패가 발생하면:

```bash
# 현재 변경사항 임시 저장
git stash

# 이전 브랜치로 이동
git checkout main

# 동일 테스트 실행
./gradlew test

# 원래 브랜치로 복귀
git checkout -
git stash pop
```

동일한 테스트가 동일한 이유로 실패하는지 확인하여 업그레이드 영향 판단.

#### 19. LSP 위반 감지

인터페이스 구현체가 변경되어 동작이 달라질 수 있는 영역 확인:

| 확인 대상 | 잠재적 변화 | 검증 방법 |
|----------|-----------|----------|
| Jackson ObjectMapper | 직렬화/역직렬화 동작 | Approval 테스트 결과 비교 |
| JPA Repository | 쿼리 생성 방식 (Hibernate 버전) | 통합 테스트 + SQL 로그 확인 |
| RestClient/RestTemplate | 응답 처리 방식 | API 호출 테스트 |
| WebMvcConfigurer | 설정 적용 순서 | E2E 테스트 |

동작 변화가 감지되면 사용자에게 보고하고 해결책 논의.

#### 20. Warning 전수 분석

```bash
./gradlew build --warning-mode all 2>&1 | tee build-warnings.log
```

모든 Warning을 분류하고 해결 방안 제시:

| Warning 유형 | 원인 | 해결 방법 |
|-------------|-----|----------|
| Deprecation | API deprecated | 대체 API로 마이그레이션 |
| 의존성 충돌 | 버전 불일치 | exclude 또는 버전 명시 |
| 설정 경고 | 속성 변경/제거 | 설정 파일 수정 |

#### 21. 인프라 파일 업데이트 (Java 변경 시)

**Dockerfile**
```dockerfile
ARG BASE_IMG=amazoncorretto:<java-version>
```

**GitHub Actions**
```yaml
with:
  java-distribution: 'corretto'
  java-version: '<java-version>'
```

**.java-version (jenv)**
```bash
jenv local <java-version>
```

---

## PR 템플릿

```markdown
## Summary

- Spring Boot X.Y.Z → A.B.C 업그레이드
- [연관 의존성 변경 목록]

## Migration Guide Reference

- https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-X.Y-Migration-Guide

## Breaking Changes Applied

- [ ] 항목1
- [ ] 항목2

## Test Results

| 테스트 유형 | 결과 | 개수 |
|-----------|-----|-----|
| Unit Test | PASS | XXX개 |
| Integration Test | PASS | XXX개 |

## Rollback Plan

1. 이 PR을 revert
2. [추가 롤백 단계 - 필요시]

## Checklist

- [ ] 빌드 성공
- [ ] 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] Warning 분석 완료
- [ ] 로컬 환경 동작 확인
```

---

## 주의사항

### 일반 원칙

- **마이너 먼저**: 3.2.x → 4.0.x 직행보다 3.2.x → 3.5.x → 4.0.x 권장
- **공식 문서 우선**: 웹 검색 시 항상 spring.io 또는 github.com/spring-projects 문서 참조
- **테스트 필수**: 각 단계마다 반드시 test + integrationTest 실행
- **Warning 무시 금지**: 업그레이드 후 발생하는 모든 warning 분석 및 해결

### 의존성 관련

- **BOM 우선**: 직접 버전 명시보다 Spring Boot BOM 관리 활용
- **호환성 매트릭스**: Spring Cloud, Spring Modulith 등은 Spring Boot 버전별 호환 매트릭스 확인 필수
- **서드파티 주의**: Lombok, MapStruct, QueryDSL 등 서드파티는 별도 호환성 확인

### 테스트 관련

- **Approval 테스트**: JSON 직렬화 변경 시 스냅샷 파일 대량 변경 예상
- **테스트 어노테이션**: `@MockBean`/`@SpyBean` deprecated 여부 Migration Guide에서 확인
- **테스트 설정**: `@SpringBootTest` 자동 설정 범위 변경 가능성 확인

### 인프라 관련

- **JDK 배포본**: Java 업그레이드 시 사용 중인 배포본(Corretto, Temurin 등)에 해당 버전 존재 여부 확인
- **CI/CD**: GitHub Actions, Jenkins 등 CI 환경의 Java 버전도 함께 변경
- **컨테이너**: Dockerfile 베이스 이미지 업데이트

### Breaking Changes 패턴 (버전별로 웹 검색 필요)

- **패키지명 변경**: Jackson, Jakarta EE 등 대규모 패키지 이동
- **API 제거**: Deprecated였던 API가 다음 메이저에서 제거
- **기본값 변경**: 설정 기본값 변경으로 인한 동작 차이
- **인터페이스 구현체 변경**: 같은 인터페이스지만 내부 동작이 달라지는 경우 (LSP 위반 주의)

### 롤백 전략

- **PR 단위 롤백**: 단계별 PR 분할로 문제 발생 시 해당 PR만 revert
- **브랜치 전략**: 업그레이드 브랜치를 별도로 유지하여 main 보호
- **데이터베이스**: Flyway/Liquibase 마이그레이션은 롤백 스크립트 준비

---

## 자주 발생하는 문제 해결

### 빌드 실패: 패키지를 찾을 수 없음

```
error: package com.example.xxx does not exist
```

→ 패키지명 변경 확인 (Migration Guide 참조)

### 테스트 실패: Bean 생성 실패

```
No qualifying bean of type 'xxx' available
```

→ 테스트 어노테이션 변경 확인 (`@MockBean` → `@MockitoBean` 등)

### Warning: Deprecated API

```
'xxx' is deprecated
```

→ Migration Guide에서 대체 API 확인 후 마이그레이션

### 런타임 에러: 직렬화 실패

```
Cannot deserialize value of type xxx
```

→ Jackson 버전 변경에 따른 직렬화 설정 확인
