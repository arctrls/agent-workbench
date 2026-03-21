# Java Code Style Guide

이 문서는 Java 개발에서 따라야 할 코드 스타일과 컨벤션을 정의합니다.

## General Rules

- 한국어로 답변해.
- **YAGNI (You Aren't Gonna Need It)**: 명확하게 사용할 곳이 있는 상황에서만 코드를 추가해. 특히 사용하지 않는 메서드를 만들지 말 것.

## Java Code Style Rules

### 파라미터 포맷팅

- **파라미터 개행**: 메소드나 생성자의 파라미터가 3개 이상이거나 라인이 길어질 때 여러 라인으로 개행
- **정렬**: 첫 번째 파라미터부터 개행하고, 각 파라미터를 같은 들여쓰기로 정렬
- **닫는 괄호**: 마지막 파라미터와 같은 들여쓰기 레벨에 위치

```java
// Good - 파라미터 개행
public OrderPayment create(
    final Long sellDaddrNo,
    final String kpid,
    final PaymentStatusCode statusCode,
    final LocalDateTime createdAt
) {
    // 구현
}

// Good - 짧은 파라미터는 한 라인
public void delete(final Long id) {
    // 구현
}

// Bad - 긴 라인을 한 줄로
public OrderPayment create(final Long sellDaddrNo, final String kpid, final PaymentStatusCode statusCode, final LocalDateTime createdAt) {
    // 구현
}
```

### 메소드 명명 스타일

- **Record 스타일 메소드 명명**: 모든 클래스에서 `getXxx()` 대신 `xxx()` 사용

```java
// Good
public String code() {
    return code;
}

// Bad
public String getCode() {
    return code;
}
```

### Query/Command 메소드 명명 규칙

- **Query 메소드 (데이터 조회/반환)**: 
  - 상태를 변경하지 않고 데이터만 반환하는 메소드
  - `getXxx()` 대신 간결한 `xxx()` 사용 (Record 스타일과 일치)
  - 조건이 있는 경우 `xxxBy()` 또는 `xxxFor()` 사용
  - 문맥에 따라 선택: 호출부에서 읽을 때 자연스러운 전치사 사용

```java
// Good - Query 메소드
public String name() { return name; }  // 단순 조회
public User userById(final Long id) { ... }  // ID로 조회
public List<Order> ordersFor(final Customer customer) { ... }  // 특정 고객의 주문 조회
public Payment latestPaymentBy(final String userId) { ... }  // 조건부 조회

// 실제 예시
private Kpid latestKpidFor(final Long sellDaddrNo) {
    return repository.findLatestBySellDaddrNo(sellDaddrNo)
            .map(request -> Kpid.of(request.kpid()))
            .orElse(Kpid.EMPTY);
}

// Bad - 장황한 이름
public String getName() { ... }
public User getUserById(final Long id) { ... }
private Kpid getLatestKpidForSellDaddrNo(final Long sellDaddrNo) { ... }
```

- **Command 메소드 (상태 변경)**:
  - 상태를 변경하고 void를 반환하거나 변경 결과만 반환
  - 동사로 시작: `create()`, `update()`, `delete()`, `process()`

```java
// Command 메소드 예시
public void cancelOrder(final Long orderId) { ... }
public OrderId createOrder(final CreateOrderRequest request) { ... }
public void updateStatus(final OrderStatus newStatus) { ... }
```

### 예외 처리 스타일

- **예외 타입**: `Exception` 대신 `RuntimeException` 사용 (더 구체적)
- **일관된 로깅 프리픽스**: 기능별로 일관된 프리픽스 사용 (예: "payment history: ")

#### 조용한 실패 (Silent Failure) vs 요란한 실패 (Fail Fast)

- **조용한 실패가 적절한 경우**:
  - 레거시 코드베이스에 새 기능 추가 시 (테스트 커버리지가 낮은 경우)
  - 부가적인 기능 (로깅, 모니터링, 분석 등)
  - 사용자 경험에 직접적 영향이 없는 기능
  - 실패해도 핵심 비즈니스 로직이 계속 동작해야 하는 경우

```java
// Good - 레거시 시스템의 부가 기능
try {
    // 결제 이력 추적 (부가 기능)
    paymentHistoryTracker.track(payment);
} catch (final RuntimeException e) {
    log.warn("payment history: tracking failed", e);
    // 핵심 결제 프로세스는 계속 진행
}
```

- **요란한 실패가 적절한 경우**:
  - 새 프로젝트 또는 새로운 핵심 기능
  - 데이터 무결성이 중요한 경우
  - 비즈니스 규칙 위반
  - 복구 불가능한 상태

```java
// Good - 새 기능의 핵심 로직
public void processPayment(final Payment payment) {
    if (!payment.isValid()) {
        throw new IllegalArgumentException("Invalid payment: " + payment);
    }
    
    // 결제 검증 실패는 즉시 예외 발생
    final ValidationResult result = validator.validate(payment);
    if (!result.isSuccess()) {
        throw new PaymentValidationException(result.errors());
    }
}
```

### 상수 비교 스타일 (Yoda 조건)

- **상수 좌변 배치**: null, 상수, enum 값 등을 항상 좌변에 배치
- **실수 방지**: 실수로 할당(=) 대신 비교(==)를 쓰는 것을 컴파일 타임에 방지

```java
// Good - Yoda style
if (null != value) { }
if (EMPTY == this) { }
if ("ACTIVE".equals(status)) { }

// Bad
if (value != null) { }
if (this == EMPTY) { }
```

### 조건문 스타일

- **단일 라인 if-return**: if 문이 한 줄이면 return도 같은 줄에 작성 가능
- **return 없는 한 줄 if문**: if 다음 라인에 들여쓰기해서 로직을 추가
- **간결성 우선**: 가독성을 해치지 않는 선에서 간결하게 작성

```java
// Good - 간결한 경우 (return 있음)
if (!sellDaddrNo.isPresent()) return Kpid.EMPTY;

// Good - return 없는 한 줄 if문
if (!kpid.isEmpty())
    sbHtml.append(String.format("metadata: {kpid: \"%s\"},", kpid));

// Good - 복잡한 경우
if (!sellDaddrNo.isPresent()) {
    log.warn("payment history: sellDaddrNo not found");
    return Kpid.EMPTY;
}
```

### 불변성 규칙

- **클래스 불변성**: 가능하면 모든 클래스를 불변으로 만들기
- **예외**: 도메인 모델 중 엔터티만 일부 가변 프로퍼티 허용
- **파라미터 final**: 모든 메소드 파라미터에 final 키워드 사용
- **로컬 변수 final**: 모든 로컬 변수는 무조건 final 사용

```java
public void someMethod(final String param1, final Integer param2) {
    final String localVar = "value";
    final List<String> items = new ArrayList<>();
    // 구현
}
```

### 반복문 스타일

- **스트림 우선**: for, while문은 꼭 필요한 경우에만 사용하고 스트림을 우선 사용
- **간결한 수집기**: Java 버전이 지원한다면 `.toList()` 같은 간결한 버전 사용
- **불변 컬렉션**: 항상 불변 컬렉션으로 수집

```java
// Java 16+ - 간결하고 불변
final List<String> result = items.stream()
    .filter(Item::isValid)
    .map(Item::name)
    .toList();

// Java 10+ - 불변 컬렉션 사용 (static import 필요)
final List<String> result = items.stream()
    .filter(Item::isValid)
    .map(Item::name)
    .collect(toUnmodifiableList());

// Java 8+ - static import 권장
final List<String> result = items.stream()
    .filter(Item::isValid)
    .map(Item::name)
    .collect(toList());
```

### 람다/메서드 레퍼런스 스타일

- **메서드 레퍼런스 우선**: 람다에서는 메서드 레퍼런스를 우선적으로 적용
- **간결성과 가독성**: 단순한 메서드 호출은 메서드 레퍼런스로 표현

```java
// Good - 메서드 레퍼런스 사용
.map(OrderPaymentRequest::kpid)
.filter(Item::isValid)
.forEach(System.out::println)

// Bad - 불필요한 람다
.map(request -> request.kpid())
.filter(item -> item.isValid())
.forEach(item -> System.out.println(item))

// Good - 복잡한 로직은 람다 사용
.filter(order -> order.amount().isGreaterThan(minAmount) && order.isActive())
```

### 람다 파라미터 명명 규칙

- **기본 규칙**: 의미있는 이름 사용 (예: `user`, `order`, `item`)
- **이름 충돌 시**: 바깥쪽 변수와 이름이 겹치는 경우 코틀린 스타일의 `it` 사용
- **일관성**: 같은 맥락에서는 동일한 명명 규칙 적용

```java
// Good - 이름 충돌이 없는 경우
users.stream().filter(user -> user.isActive())

// Good - 이름 충돌이 있는 경우 (바깥쪽에 kpid 변수가 있음)
final Kpid kpid = paymentTrackingService.trackPaymentRequest(SellDaddrNo);
kpid.ifPresent(it -> sParaTemp.put("param2", it.toString()));

// Bad - 바깥쪽 변수와 이름 충돌
final Kpid kpid = paymentTrackingService.trackPaymentRequest(SellDaddrNo);
kpid.ifPresent(kpid -> sParaTemp.put("param2", kpid.toString())); // 컴파일 에러
```

### 컬렉션 타입 선택

- **Collection 우선 사용**: 변수 선언, 메서드 리턴타입, 파라미터에서 List보다 Collection으로 weaken 가능한 경우 Collection 사용
- **API 유연성**: 구체적인 구현체(ArrayList, LinkedList 등)에 의존하지 않는 유연한 API 설계
- **구현 세부사항 숨김**: 클라이언트 코드가 컬렉션의 구체적인 타입에 의존하지 않도록 함

```java
// Good - Collection 사용으로 유연한 API
public void processItems(final Collection<Item> items) {
    items.forEach(this::processItem);
}

public Collection<String> getActiveUsers() {
    return users.stream()
        .filter(User::isActive)
        .map(User::name)
        .toList();
}

// Bad - 불필요하게 구체적인 List 타입 사용
public void processItems(final List<Item> items) {  // Collection으로 충분
    items.forEach(this::processItem);
}
```

### 클래스 가시성

- **기본 가시성**: package-private을 기본으로 사용
- **public 사용**: 꼭 필요한 경우에만 public으로 선언

```java
// Good - package-private
class OrderPaymentMapDao {
    // 구현
}

// Only when necessary - public
public class PaymentStatusCode {
    // 구현
}
```

### Enum 스타일

- **필수 필드**: 항상 `code`, `description` 필드를 기본으로 포함
  - `code`: 실제 저장되는 값
  - `description`: code에 대한 설명
  - **이유**: enum 이름을 리팩터링하기 쉽게 만들기 위함
- **Lombok 사용**: @Getter + @RequiredArgsConstructor + @Accessors(fluent = true) 조합 사용

```java
@Getter
@RequiredArgsConstructor
@Accessors(fluent = true)
public enum PaymentStatusCode {
    PAYMENT_REQUESTED("PAYMENT_REQUESTED", "결제 요청됨");

    private final String code;
    private final String description;
}
```

### 클래스 설계

- **Parameter Object 도입**: 메소드 파라미터가 3개 이상일 때 Parameter Object 패턴 사용
- **Record 우선**: 프로젝트에서 record 사용 가능하면 파라미터 오브젝트는 무조건 record로 구현
- **Factory Method 선호**: 생성자 대신 static factory method 사용
  - 생성자는 `private`으로 만들기
  - Factory method 이름: 파라미터 1개일 때 `from`, 여러 개일 때 `of`

### Lombok 사용 규칙

- **@Getter + @RequiredArgsConstructor + @Accessors(fluent = true)**: Record 스타일 클래스에 사용
- **Builder 패턴 지양**: `@Builder` 어노테이션 사용하지 않기
- **모든 필드 final**: 불변성 보장을 위해 모든 필드를 final로 선언
- **생성자 기반**: 단순한 생성자와 factory method 조합 선호
- **생성자 가시성**: @RequiredArgsConstructor(access = lombok.AccessLevel.PRIVATE) 사용해서 팩토리 메서드만 사용하도록 강제

```java
@Getter
@RequiredArgsConstructor(access = lombok.AccessLevel.PRIVATE)
@Accessors(fluent = true)
class OrderPayment {
    private final Long sellDaddrNo;
    private final String kpid;
    private final PaymentStatusCode statusCode;
    private final LocalDateTime createdAt;

    static OrderPayment of(
        final Long sellDaddrNo,
        final String kpid,
        final PaymentStatusCode statusCode,
        final LocalDateTime createdAt
    ) {
        return new OrderPayment(sellDaddrNo, kpid, statusCode, createdAt);
    }
}
```

## Spring Framework Rules

### Service 클래스 스타일

- **유즈케이스 이름**: @Service 클래스는 동사로 시작하는 유즈케이스 이름 사용
- **메소드 이름**: 간결하게 작성
- **불변 파라미터/리턴값**: 모든 파라미터와 리턴값은 불변이어야 함
  - Record 우선 사용
  - Record 사용 불가시 Lombok으로 record 스타일 구현
- **명명 규칙**: 파라미터는 `XxxRequest`, 리턴값은 `XxxResponse`
- **시간 의존성**: 현재 시간에 의존하는 로직이 있으면 Request 객체에 포함하거나 마지막 파라미터로 전달
  - **이유**: ambient context인 현재시간을 서비스에 직접 넘기지 않아 로직을 deterministic하게 만들기 위함

```java
// 파라미터 오브젝트가 있는 경우 - Request에 포함
@Service
public class CreateOrderPayment {
    public CreateOrderPaymentResponse create(final CreateOrderPaymentRequest request) {
        // request.now()를 사용
    }
}

record CreateOrderPaymentRequest(
    Long sellDaddrNo,
    String kpid,
    PaymentStatusCode statusCode,
    LocalDateTime now  // Request에 시간 포함
) {}

// 파라미터 오브젝트가 없는 경우 - 마지막 파라미터로 전달
@Service
public class DeletePayment {
    public void delete(final Long paymentId, final LocalDateTime now) {
        // 마지막 파라미터로 시간 전달
    }
}
```

### 데이터베이스 관련

- **시간 처리**: 쿼리에서 `NOW()` 함수 사용하지 않고 애플리케이션에서 `LocalDateTime.now()` 전달
  - **이유**: 로직을 deterministic하게 만들기 위함 (테스트 가능성과 예측 가능성 확보)
- **파라미터 바인딩**: 모든 동적 값은 파라미터로 전달하여 SQL Injection 방지

## 패키지 구조 및 아키텍처

### Package-by-Feature 원칙

- **기능별 패키지**: 계층별(controller, service, repository) 대신 기능별로 패키지 구성
- **Vertical Slice**: 각 기능이 독립적으로 완성되도록 수직적 분할
- **높은 응집도**: 관련된 코드들을 하나의 패키지에 모아 응집도 향상

```java
// Good - Package-by-Feature
src/main/java/
├── payment/
│   ├── CreatePayment.java              // Service
│   ├── PaymentController.java
│   ├── PaymentRepository.java
│   ├── Payment.java                    // Domain
│   └── PaymentStatusCode.java          // Enum
├── order/
│   ├── CreateOrder.java
│   ├── OrderController.java
│   └── Order.java
└── user/
    ├── RegisterUser.java
    ├── UserController.java
    └── User.java

// Bad - Package-by-Layer
src/main/java/
├── controller/
│   ├── PaymentController.java
│   ├── OrderController.java
│   └── UserController.java
├── service/
│   ├── CreatePayment.java
│   ├── CreateOrder.java
│   └── RegisterUser.java
└── repository/
    ├── PaymentRepository.java
    ├── OrderRepository.java
    └── UserRepository.java
```

### DIP (Dependency Inversion Principle) 준수

- **고수준 → 저수준 의존 금지**: 고수준 컴포넌트가 저수준 컴포넌트에 직접 의존하지 않음
- **인터페이스 의존**: 클라이언트는 항상 추상화(인터페이스)에 의존
- **의존성 주입**: 구체적인 구현체는 외부에서 주입받음
- **인터페이스 소유권**: 클라이언트가 필요로 하는 인터페이스를 클라이언트 패키지에서 정의

```java
// Bad - DIP 위반: 고수준이 저수준에 직접 의존
@Service
class CreateOrder {
    private final MySqlOrderRepository repository;  // 구체적인 구현체에 의존

    public void create(final CreateOrderRequest request) {
        repository.save(order);  // MySQL에 강하게 결합
    }
}

// Good - DIP 준수: 인터페이스에 의존
@Service
class CreateOrder {
    private final OrderRepository repository;  // 추상화에 의존

    public void create(final CreateOrderRequest request) {
        repository.save(order);  // 구현체와 무관하게 동작
    }
}

// 클라이언트(order 패키지)가 필요로 하는 인터페이스 정의
interface OrderRepository {
    void save(Order order);
    Optional<Order> findById(Long id);
}

// 저수준 구현체는 별도 패키지에서 인터페이스 구현
@Repository
class JpaOrderRepository implements OrderRepository {
    // JPA 구현
}
```

### 패키지 간 통신

- **이벤트 기반**: 패키지 간 느슨한 결합을 위해 도메인 이벤트 활용
- **퍼사드 패턴**: 복잡한 패키지 내부 로직을 단순한 인터페이스로 노출
- **직접 호출 최소화**: 다른 패키지의 내부 구현체에 직접 의존하지 않음

```java
// 이벤트 기반 통신
@Service
class CreateOrder {
    private final ApplicationEventPublisher eventPublisher;

    public void create(final CreateOrderRequest request) {
        // 주문 생성 로직
        final Order order = createOrder(request);
        
        // 이벤트 발행으로 다른 패키지에 알림
        eventPublisher.publishEvent(new OrderCreatedEvent(order.id()));
    }
}

// payment 패키지에서 이벤트 처리
@EventListener
class OrderEventHandler {
    public void handleOrderCreated(final OrderCreatedEvent event) {
        // 결제 관련 후처리
    }
}
```