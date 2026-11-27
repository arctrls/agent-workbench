# agent-workbench

- Codex·Claude Code용 개발·리뷰 스킬, 프롬프트, 전역 지침 관리
- Java·Kotlin Spring 구현과 리뷰를 같은 기준으로 연결
- 개인 경로·회사 접속 정보는 Git 밖의 환경 파일로 분리

## 시작하기

- 준비: Codex, Bash, `rsync`, Python 3.11+ 또는 `uv`
- Claude Code 사용 시: `claude` CLI (없으면 플러그인 등록 생략)
- 저장소 루트에서 변경 내용을 확인한 뒤 적용
- 적용 범위: **Codex 스킬·프롬프트·전역 지침·관리 대상 MCP 설정**, **Claude Code 플러그인 `z` 등록**

```bash
./codex/sync.sh --dry-run
./codex/sync.sh
```

## 개발·리뷰

- 호출 형식: Codex `$<skill>` · Claude Code `/z:<skill>`
- **구현:** `$spring-workflow` → 구현·검사 → 통합 리뷰 → 수정·검증
- **리뷰만:** `$spring-review` → 설계·동작·언어별 스타일을 한 번에 보고
- **검사 설정이 없는 프로젝트:** ktlint·detekt·PMD로 기본 검사 가능
- [전체 흐름과 역할](codex/skills/spring-workflow/references/workflow-overview.md) · [기본 검사 도구 설치·사용](codex/skills/spring-review/references/standalone-checks.md)

## 이전 대화 찾기

- `$find-session`으로 날짜·주제·프로젝트에 맞는 이전 Codex 세션을 검색 (Codex 전용)
- 대화 근거와 세션 재개 명령을 함께 확인하며, 시간대를 좁혀 먼저 검색

## 파일 위치 열기

- `$finder-reveal` 또는 “Finder로 열어”로 현재 결과 파일을 Finder에서 선택
- 폴더를 지정하면 Finder에서 폴더 내용 표시 · [사용 방법](codex/skills/finder-reveal/SKILL.md)

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
- `--target-dir` 지정 시 공통 스킬 연결과 Claude 플러그인 등록 생략; 필요하면 `--shared-skills-dir`, `--claude-plugin` 추가
- 선택 사항: `git config core.hooksPath .githooks`로 push·merge·rebase 후크 동기화 활성화

## Claude Code

- sync가 `codex/`를 로컬 마켓플레이스 `agent-workbench`의 플러그인 `z`로 등록 — 미등록이거나 다른 clone을 가리킬 때만 재등록
- 복사본 없이 저장소의 `codex/skills`를 직접 읽음 — 수정 사항은 새 세션 또는 `/reload-plugins`에서 반영
- 스킬 추가·삭제 시 `codex/.claude-plugin/marketplace.json`의 `skills` 목록도 갱신 — 불일치하면 sync가 변경 전에 중단 (`find-session`은 제외 대상)
- MCP: 저장소에서 관리하지 않음 — claude.ai 계정 커넥터 사용
- [플러그인 구성 상세](codex/setup.md#claude-code에서-같은-스킬-사용)

## 검증

```bash
# 회귀 테스트
uv run --python 3.13 python -m unittest discover -s scripts/tests -p 'test*.py' -v

# 실제 스킬 발견·인증 파일 보존 확인 (--home 반복 가능)
python3 scripts/verify-codex-skills.py --home ~/.codex

# 추적 파일의 민감정보 패턴 검사
./scripts/check-sensitive-data.sh
```
