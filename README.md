# agent-workbench

- Codex용 개발·리뷰 스킬, 프롬프트, 전역 지침 관리
- Java·Kotlin Spring 구현과 리뷰를 같은 기준으로 연결
- 개인 경로·회사 접속 정보는 Git 밖의 환경 파일로 분리

## 시작하기

- 준비: Codex, Bash, `rsync`, Python 3.11+ 또는 `uv`
- 저장소 루트에서 변경 내용을 확인한 뒤 적용
- 적용 범위: **스킬·프롬프트·전역 지침·관리 대상 MCP 설정**

```bash
./codex/sync.sh --dry-run
./codex/sync.sh
```

## 개발·리뷰

- **구현:** `$spring-workflow` → 구현·검사 → 통합 리뷰 → 수정·검증
- **리뷰만:** `$spring-review` → 설계·동작·언어별 스타일을 한 번에 보고
- **검사 설정이 없는 프로젝트:** ktlint·detekt·PMD로 기본 검사 가능
- [전체 흐름과 역할](codex/skills/spring-workflow/references/workflow-overview.md) · [기본 검사 도구 설치·사용](codex/skills/spring-review/references/standalone-checks.md)

## 이전 대화 찾기

- `$find-session`으로 날짜·주제·프로젝트에 맞는 이전 Codex 세션을 검색
- 대화 근거와 세션 재개 명령을 함께 확인하며, 시간대를 좁혀 먼저 검색

## 개인 환경 설정

- 파일: `~/.config/agent-workbench/env` · 권한: `600`
- 형식: 따옴표 없는 `KEY=value` — 셸에서 `source`하지 않음
- 파일 위치 변경: `AGENT_WORKBENCH_ENV_FILE`
- MySQL MCP 사용 시 필수: `MYSQL_READ_DEV_HOST`, `MYSQL_READ_DEV_SECRET_ARN`, `MYSQL_READ_DEV_DATABASE`, `MYSQL_READ_DEV_REGION`
- 기존 설정 이전: `uv run --python 3.13 python codex/migrate-env.py`
- [전체 환경변수·이전 절차·동기화 동작](codex/setup.md)

## 계정 전환·동기화

- 계정 홈: `--target-dir` → `CODEX_HOME` → `~/.codex`
- 공통 스킬: `~/.agents/skills`에서 계정과 무관하게 발견
- 보존: 계정 인증·대화 기록·모델 설정·외부 설치 스킬
- 관리 스킬 내부의 오래된 파일은 삭제될 수 있으므로 저장소 원본에서 수정
- `--target-dir` 지정 시 공통 스킬 연결 생략; 필요하면 `--shared-skills-dir` 추가
- 선택 사항: `git config core.hooksPath .githooks`로 push·merge·rebase 후크 동기화 활성화

## 검증

```bash
# 회귀 테스트
uv run --python 3.13 python -m unittest discover -s scripts/tests -p 'test*.py' -v

# 실제 스킬 발견·인증 파일 보존 확인 (--home 반복 가능)
python3 scripts/verify-codex-skills.py --home ~/.codex

# 추적 파일의 민감정보 패턴 검사
./scripts/check-sensitive-data.sh
```
