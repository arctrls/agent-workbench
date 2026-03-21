---
name: upgrade-java
description: Java 버전 업그레이드를 수행합니다. "자바 버전 올려줘", "Java 25로 업그레이드", "JDK 버전 변경" 등의 요청 시 사용합니다. Gradle, Kotlin, Dockerfile, GitHub Actions의 호환성을 검사하고 필요한 모든 설정을 업데이트합니다.
---

# Java 버전 업그레이드

프로젝트의 Java 버전을 목표 버전으로 업그레이드합니다.

## 작업 프로세스

### 1. 현재 버전 확인

다음 파일들에서 현재 Java 버전 설정을 확인:

- `build.gradle.kts` 또는 `build.gradle`
  - `java.toolchain.languageVersion`
  - Kotlin `jvmTarget`
  - Kotlin 플러그인 버전
- `gradle/wrapper/gradle-wrapper.properties` (Gradle 버전)
- `Dockerfile` (베이스 이미지)
- `.github/workflows/*.yml` 또는 `.github/workflows/*.yaml` (GitHub Actions)
- `.java-version` (jenv 설정)

### 2. 호환성 검사

목표 Java 버전에 대해 다음 도구들의 지원 여부를 웹 검색으로 확인:

| 도구 | 확인 사항 |
|------|----------|
| **Gradle** | 현재 버전이 목표 Java를 지원하는지, 미지원 시 필요한 최소 버전 |
| **Spring Boot** | 현재 버전이 목표 Java를 지원하는지 |
| **Kotlin** | 현재 버전이 목표 JVM bytecode를 지원하는지, 미지원 시 필요한 최소 버전 |

호환성 결과를 표로 정리하여 사용자에게 보고:

```
| 구성 요소 | 현재 버전 | Java X 지원 | 필요 조치 |
|----------|----------|-------------|----------|
| Gradle   | x.x.x    | O/X         | 변경 불필요 / x.x.x 이상 필요 |
| Spring   | x.x.x    | O/X         | 변경 불필요 / x.x.x 이상 필요 |
| Kotlin   | x.x.x    | O/X         | 변경 불필요 / x.x.x 이상 필요 |
```

**호환되지 않는 도구가 있으면 사용자에게 확인 후 진행**

### 3. 의존성 업그레이드 (필요시)

#### Gradle Wrapper 업그레이드
```bash
./gradlew wrapper --gradle-version=<latest-compatible-version>
```

#### Kotlin 버전 업그레이드
`build.gradle.kts`에서 Kotlin 플러그인 버전 수정

### 4. Java 버전 변경

`build.gradle.kts` 수정:

```kotlin
java {
    toolchain {
        languageVersion = JavaLanguageVersion.of(<target-version>)
    }
}

tasks.withType<KotlinJvmCompile> {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_<target-version>)
    }
}
```

### 5. 로컬 환경 설정 (jenv 사용 시)

```bash
# 설치된 JDK 확인
/usr/libexec/java_home -V 2>&1 | grep -i <target-version>

# jenv에 추가 (필요시)
jenv add <jdk-path>

# 프로젝트에 설정
jenv local <target-version>
```

### 6. Dockerfile 업데이트

베이스 이미지 변경:
```dockerfile
ARG BASE_IMG=amazoncorretto:<target-version>
```

### 7. GitHub Actions 업데이트

`.github/workflows/*.yml` 파일에서 java-version 수정:
```yaml
java-version: '<target-version>'
```

### 8. 빌드 테스트

```bash
./gradlew clean build -x test
```

### 9. Gradle 커스텀 태스크 호환성 확인

Gradle 메이저 버전 업그레이드 시 커스텀 Test 태스크 확인:

```kotlin
// Gradle 9+에서는 소스셋을 명시적으로 설정해야 함
tasks.register<Test>("integrationTest") {
    testClassesDirs = sourceSets["test"].output.classesDirs
    classpath = sourceSets["test"].runtimeClasspath
    // ...
}
```

`NO-SOURCE` 오류 발생 시 위 설정 추가

### 10. 커밋 및 PR

변경사항을 커밋하고 PR 메시지 생성:

```
## Summary

- Java X에서 Java Y로 업그레이드
- Gradle a.b.c -> x.y.z (Java Y 지원 필수)
- Kotlin a.b.c -> x.y.z (JVM Y bytecode 지원)
- Dockerfile 베이스 이미지 업데이트
- GitHub Actions java-version 업데이트

## Test plan

- [ ] 빌드 성공 확인
- [ ] 테스트 실행 확인
- [ ] 스테이징 환경 배포 및 검증
```

## 주의사항

- 목표 Java 버전이 시스템에 설치되어 있어야 함
- Gradle toolchain auto-provisioning 미설정 시 수동 설치 필요
- LTS 버전 권장 (17, 21, 25 등)
- 메이저 버전 업그레이드 시 deprecated API 경고 확인 필요
