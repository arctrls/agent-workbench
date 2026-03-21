# 배포 모니터링

배포 후 Datadog 로그를 주기적으로 모니터링하고, 문제 발견 시 macOS 알림을 보냅니다.

## 파라미터

사용자에게 다음 정보를 확인합니다 (명시되지 않은 경우):

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| service | (필수) | Datadog service 이름 (예: vador, klimt) |
| env | prod | 환경 (dev, stage, prod) |
| interval | 15 | 조회 간격 (초) |
| duration | 10 | 모니터링 시간 (분) |

## 실행 순서

### 1. 모니터링 시작

Datadog MCP 도구(`mcp__datadog__search_datadog_logs`)를 사용하여 반복 조회합니다.

매 조회마다 다음 2가지를 병렬로 실행:

**a. error/critical/warn 로그 조회:**
```
query: service:{service} env:{env} status:(error OR critical OR warn)
from: now-{interval}s
to: now
```

**b. 전체 로그 건수 확인 (첫 회차만):**
```
query: service:{service} env:{env}
from: now-30s
to: now
```

### 2. 로그 판별 기준

다음은 **무시해도 되는 로그**입니다 (비즈니스 에러 아님):
- `[dd.trace` 로 시작하는 Datadog tracer 초기화 로그 (파드 시작 시 발생)
- `Communications link failure` - DB 연결 끊김 (일시적)
- `Connection is closed` - 위 이슈의 부수 에러
- `active SQL connection has changed` - AWS JDBC Wrapper Failover 로그

다음은 **즉시 알림이 필요한 로그**입니다:
- `status:error` 또는 `status:critical` 중 위 무시 패턴에 해당하지 않는 것
- DB 연결 실패가 지속적으로 발생하는 경우 (3회 연속)
- 5xx 응답 관련 에러
- `OutOfMemoryError`, `StackOverflowError` 등 JVM 에러

### 3. 알림 방식

문제 발견 시 macOS 알림을 보냅니다:

```bash
osascript -e 'display notification "{메시지 내용}" with title "배포 모니터링" subtitle "{service} {env}" sound name "Funk"'
```

**알림 발송 조건:**
- 비즈니스 error/critical 로그 발견 시
- 동일 에러가 3회 연속 발생 시 (반복 알림 방지를 위해 이후에는 알리지 않음)

**알림 메시지 포맷:**
- `"[ERROR] {에러 요약} - {건수}건 발견"`
- `"[CRITICAL] {에러 요약} - 즉시 확인 필요"`

### 4. 출력 형식

매 조회마다 한 줄로 상태를 출력합니다:

```
[N회차 HH:MM:SS] error: 0 | warn: 3 (products GET 패턴) | critical: 0 ✅
```

문제 발견 시:
```
[N회차 HH:MM:SS] error: 2 | warn: 5 | critical: 0 ⚠️ — DB 연결 실패 감지
```

### 5. 모니터링 종료 후 요약

모니터링이 완료되면 다음 형식으로 요약합니다:

```
=== 모니터링 요약 ===
서비스: {service} | 환경: {env}
시간: HH:MM:SS ~ HH:MM:SS ({duration}분)
총 조회: {N}회

| 항목 | 건수 |
|------|------|
| error | N |
| warn | N |
| critical | N |

판정: ✅ 정상 / ⚠️ 주의 필요 / ❌ 문제 발견

주요 이벤트:
- HH:MM:SS: DD tracer 초기화 (파드 롤링 업데이트)
- HH:MM:SS: products warn 패턴 (기존 패턴)
```

## 주의사항

- `sleep` 명령어로 interval 간격을 유지합니다
- 사용자가 중단하면 즉시 종료 후 그 시점까지의 요약을 출력합니다
