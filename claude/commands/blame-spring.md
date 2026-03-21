# /blame-spring

**목적**: Claude가 CLAUDE.md의 Spring Framework 규칙을 위반했을 때 사용

## 사용 상황
Claude가 Spring 관련 규칙을 위반했을 때 사용합니다:
- @Service 클래스를 명사로 명명
- 현재 시간을 서비스에서 직접 호출
- Request/Response 네이밍 규칙 위반
- Package-by-Feature 구조 위반
- DIP 위반

## 명령어 실행 시 동작

**Spring Framework 규칙 위반을 감지했습니다.**

CLAUDE.md의 Spring Framework Rules를 위반했습니다. 자세한 내용은 `~/.claude/docs/CODE-STYLE-GUIDE.md`를 참조하세요:

## 핵심 Spring 규칙 체크리스트

### Service 클래스 규칙
- [ ] @Service 클래스는 **동사로 시작하는 유즈케이스 이름** (예: CreateOrderPayment)
- [ ] 메소드 이름은 간결하게 작성
- [ ] 파라미터는 **XxxRequest**, 리턴값은 **XxxResponse**
- [ ] 모든 파라미터와 리턴값은 불변 (Record 우선 사용)

### 시간 의존성 관리
- [ ] **LocalDateTime.now()를 서비스에서 직접 호출 금지**
- [ ] Request 객체에 시간 포함 또는 마지막 파라미터로 전달
- [ ] 쿼리에서 NOW() 함수 사용 금지

### 패키지 구조
- [ ] **Package-by-Feature** 원칙 준수 (계층별 구조 금지)
- [ ] 기능별 패키지로 수직 분할
- [ ] package-private 기본, public은 외부 노출 시에만

### 의존성 관리 (DIP)
- [ ] 고수준 → 저수준 직접 의존 금지
- [ ] 인터페이스에 의존, 구체 구현체 의존 금지
- [ ] 클라이언트 패키지가 인터페이스 소유

### 아키텍처 원칙
- [ ] 단방향 의존성 유지
- [ ] 도메인 레이어 외부 의존성 없음
- [ ] 이벤트 기반 패키지 간 통신
- [ ] 순환 참조 방지

### 구현 예시

```java
// Good - 올바른 Service 구조
@Service
class CreateOrderPayment {  // 동사로 시작하는 유즈케이스
    public CreateOrderPaymentResponse create(final CreateOrderPaymentRequest request) {
        // request.now() 사용 - 시간을 외부에서 주입
    }
}

record CreateOrderPaymentRequest(
    Long sellDaddrNo,
    String kpid,
    PaymentStatusCode statusCode,
    LocalDateTime now  // 시간을 Request에 포함
) {}

// Bad - 규칙 위반 예시
@Service
class PaymentService {  // 명사 사용 (잘못됨)
    public Payment create(Long id, String kpid) {  // Request 객체 없음
        LocalDateTime now = LocalDateTime.now();  // 서비스에서 직접 시간 호출 (잘못됨)
    }
}
```

**지금 당장 올바른 Spring 규칙에 따라 수정하세요.**