# /blame-code-style

**목적**: Claude가 CLAUDE.md에 설정된 Java 코드 스타일 규칙을 명백히 위반했을 때 규칙을 상기시키고 즉시 수정하도록 하는 명령어

## 사용 상황
Claude가 ~/.claude/CLAUDE.md의 Java Code Style Rules를 **확실히 위반**했을 때 사용합니다.

## 명령어 실행 시 동작

당신은 방금 CLAUDE.md에 명시된 Java 코드 스타일 규칙을 위반했습니다.

**즉시 해야 할 일:**

1. **규칙 재확인**: ~/.claude/CLAUDE.md의 Java Code Style Rules 섹션과 ~/.claude/docs/CODE-STYLE-GUIDE.md를 다시 읽어보세요
2. **위반 사항 인정**: 어떤 규칙을 위반했는지 구체적으로 식별하고 인정하세요
3. **즉시 수정**: 올바른 CLAUDE.md 규칙에 따라 코드를 **즉시** 다시 작성하세요
4. **확약**: 이런 실수를 반복하지 않겠다고 다짐하세요

## 핵심 규칙 체크리스트

### 파라미터 포맷팅
- [ ] 파라미터 3개 이상 또는 긴 라인 → 개행 및 정렬
- [ ] 닫는 괄호 마지막 파라미터와 같은 들여쓰기

### 메소드 명명
- [ ] `getXxx()` → `xxx()` (Record 스타일)
- [ ] Query 메소드: `xxxBy()`, `xxxFor()` 사용
- [ ] Command 메소드: 동사로 시작 (`create()`, `update()`, `delete()`)

### 예외 처리
- [ ] `Exception` → `RuntimeException` 사용
- [ ] 일관된 로깅 프리픽스 사용
- [ ] 조용한 실패 vs 요란한 실패 전략 선택

### 조건문 스타일
- [ ] Yoda 조건: `null != value`, `EMPTY == this`
- [ ] 단일 라인 if-return 허용
- [ ] 한 줄 if문 브레이스 생략 가능

### 불변성
- [ ] 모든 파라미터에 `final` 사용
- [ ] 모든 로컬 변수에 `final` 사용
- [ ] 가능하면 클래스 불변으로 설계

### 스트림 & 컬렉션
- [ ] for/while문 대신 스트림 우선 사용
- [ ] 메서드 레퍼런스 우선 적용
- [ ] Collection 타입을 List보다 우선 사용
- [ ] 불변 컬렉션으로 수집 (.toList())

### Lombok & 클래스 설계
- [ ] `@Builder` 사용 금지
- [ ] `@Getter + @RequiredArgsConstructor + @Accessors(fluent = true)` 조합
- [ ] Factory method 패턴: `from()`, `of()`
- [ ] package-private 기본 가시성

### Import & 람다
- [ ] qualified import 사용
- [ ] 이름 충돌 시 `it` 사용 (코틀린 스타일)

**지금 당장 수정하세요. 변명하지 말고 행동하세요.**