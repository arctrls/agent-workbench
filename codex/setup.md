# 설치·환경 설정 상세

- [빠른 시작](../README.md)
- 아래 명령은 저장소 루트에서 실행합니다.

## Sync Model

This repository syncs only repository-owned configuration outward to local home
directories. It requires Python 3.11+ and `rsync`; no Python packages are needed. The launcher uses `AGENT_WORKBENCH_PYTHON`, a suitable `python3`, or `uv run --python 3.13` when the system Python is older.

- `./codex/sync.sh`
  - recursively merges only `[features]`, `[tui]`, and `[mcp_servers]` keys from
    `codex/config.base.toml` into the selected Codex home (`--target-dir`, then `CODEX_HOME`, then `~/.codex`)
  - preserves model/reasoning preferences, plugin state, and all other local keys
  - updates prompts without deleting local-only prompt files
  - syncs each repository-owned skill separately, deleting stale files only
    inside that skill's directory
  - publishes per-skill links under `~/.agents/skills` for account-independent discovery
  - registers the `z` Claude Code plugin from `codex/.claude-plugin/marketplace.json` when it is missing or points to another clone
  - preserves `.system` and skills installed outside this repository
  - generates the selected home's `AGENTS.md` from `codex/AGENTS.user.md`
  - installs the shared `environment.py` / `with-env.py` helpers used by bundled scripts

Edit repository-owned items here first. The app owns its runtime settings and
built-in skills; existing `codex/skills/.system` snapshots are not deployed.
Removing a skill or config key from the repository does not delete it from the
home directory. Such removals must be handled explicitly.

`sync.sh` remains the entry point; `sync.py` prepares and validates the complete
change plan before writing. Dry-run shows that same plan, including deletions,
without printing config values. Changed config is re-parsed and atomically
replaced; unchanged config is left byte-for-byte intact. When config values do
change, TOML formatting and comments are regenerated rather than preserved.
Arbitrary managed destination symlinks are rejected. If the default account home already shares `config.toml`, `AGENTS.md`, `skills`, and `prompts` with one canonical home, sync updates that content home; it never follows or copies `auth.json`. Partial sharing requires an explicit canonical `--target-dir`. Existing conflicting shared skill entries cause sync to stop before writing.

Config changes detected during preparation or staging abort the sync. The app
does not share a lock with this script, so a concurrent write in the final
check/replace interval remains possible. Config replacement is atomic, but the
entire multi-file sync is not a transaction: an I/O failure during rsync can leave
some repository-owned files updated. Review the error and rerun after fixing it.


## 개인 환경 설정

개인 경로·회사 DB 주소·Secret ARN은 공개 기본 설정에 넣지 않습니다. 선택 설정 파일은 `$XDG_CONFIG_HOME/agent-workbench/env`(기본 `~/.config/agent-workbench/env`)이며, `AGENT_WORKBENCH_ENV_FILE`로 바꿀 수 있습니다. 파일은 Git 밖에 두고 권한을 `600`으로 설정합니다.

파일 형식은 **따옴표 없는 `KEY=value`**입니다. 빈 줄과 `#`로 시작하는 주석을 지원합니다. `export`, 명령 치환, `$HOME` 등의 셸 확장은 실행하지 않습니다. 값 안의 공백은 그대로 유지합니다. 파일값보다 프로세스 환경변수가 우선하고, 개별 도구의 CLI 인자가 최종 우선합니다. 이 파일을 셸에서 `source`하지 마세요.

```text
# 회사/개인 값은 각 컴퓨터에서 설정합니다. 아래는 예시입니다.
MYSQL_READ_DEV_HOST=db.example.internal
MYSQL_READ_DEV_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:example
MYSQL_READ_DEV_DATABASE=example_db
MYSQL_READ_DEV_REGION=us-east-1
MYSQL_READ_DEV_PROFILE=default
```

| 환경변수 | 필요 여부·기본값 | 용도 |
| --- | --- | --- |
| `CODEX_HOME` | 선택, `~/.codex` | 계정별 설정·인증 홈. 셸/런처에 설정하며 위 파일에서는 읽지 않습니다. |
| `AGENT_WORKBENCH_ENV_FILE` | 선택, 위 기본 파일 | 환경 파일 위치. 프로세스 환경변수로 지정합니다. |
| `AGENT_WORKBENCH_PYTHON` | 선택 | sync를 실행할 Python 3.11+ 실행 파일. 프로세스 환경변수로 지정합니다. |
| `XDG_CONFIG_HOME` | 선택, `~/.config` | 환경 파일의 기본 상위 경로. 프로세스 환경변수로 지정합니다. |
| `MYSQL_READ_DEV_HOST` | 회사 MySQL 사용 시 필수 | 개발 DB 호스트. 하드코딩된 회사 기본값이 없습니다. |
| `MYSQL_READ_DEV_SECRET_ARN` | 회사 MySQL 사용 시 필수 | Secrets Manager 식별자. 비밀번호 자체를 저장하지 않습니다. |
| `MYSQL_READ_DEV_DATABASE` | MySQL MCP 생성 시 필수 | MCP 기본 DB. 조회 스크립트는 `--database`로 지정합니다. |
| `MYSQL_READ_DEV_REGION` | MySQL MCP 생성 시 필수 | AWS 리전. 조회 스크립트만 `AWS_REGION` 또는 `--region`도 허용합니다. |
| `MYSQL_READ_DEV_PROFILE` | 선택, `default` | 사용할 로컬 AWS 프로필. 로그인·권한은 별도로 필요합니다. |
| `MYSQL_READ_DEV_PORT` | 조회 스크립트 선택, `3306` | 개발 DB 포트. |
| `MYSQL_READ_PROJECT_DIR` | 조회 스크립트 선택, 현재 디렉터리 | 로컬 datasource 탐색 기준. |
| `MYSQL_READ_LOCAL_HOST`, `MYSQL_READ_LOCAL_PORT`, `MYSQL_READ_LOCAL_USER`, `MYSQL_READ_LOCAL_PASSWORD` | 로컬 조회 선택 | 프로젝트 설정·Docker 탐색보다 우선하는 로컬 DB 설정. 비밀번호는 공개 문서나 Git에 저장하지 않습니다. |
| `REA_NPX` | 선택, 신규 설치는 `npx` | REA용 실행 파일. 특정 Node 설치가 필요할 때만 지정합니다. |
| `REA_NODE_PATH` | 선택 | REA의 PATH 앞에 붙일 Node 실행 파일 디렉터리. 빈 값으로 명시하면 이전 PATH override를 제거합니다. |
| `SPRING_REVIEW_KTLINT`, `SPRING_REVIEW_DETEKT`, `SPRING_REVIEW_PMD` | 선택 | 각 CLI 실행 파일 경로. 명령과 추가 인자를 한 문자열에 넣지 않습니다. |
| `SPRING_REVIEW_CACHE_DIR` | 선택 | 리뷰 도구 캐시 위치. 기본은 `$XDG_CACHE_HOME/agent-workbench/review-tools` 또는 `~/.cache/agent-workbench/review-tools`. |
| `XDG_CACHE_HOME` | 선택, `~/.cache` | 도구 캐시 기본 상위 경로. |
| `JAVA_HOME` | 리뷰 도구용 선택 | 설치한 CLI와 호환되는 JDK. 기본 도구 세트는 Java 17+가 필요합니다. |
| `MD_TO_PDF_OUTPUT_DIR` | 선택, `~/Downloads` | PDF 저장 디렉터리. `~` 경로를 지원합니다. |
| `BROWSER` | 선택, 사용자 기본 브라우저 | 브라우저 선택 선호. 프로세스 환경에 설정하며 자동화 연결 가능 여부는 따로 확인합니다. |

기존 `.mcp.json`의 `NOTION_TOKEN`, `GITHUB_PERSONAL_ACCESS_TOKEN`, `DD_API_KEY`, `DD_APP_KEY`는 해당 커넥터를 사용할 때만 호스트가 제공할 인증 환경변수입니다. 이 환경 파일이 모든 MCP 클라이언트에 자동 적용되는 것은 아닙니다. Codex MySQL 설정은 위 값을 읽는 sync에서 생성하며, 공개 `.mcp.json`에는 회사 MySQL 기본 설정을 포함하지 않습니다.

MySQL 변수 네 개가 모두 없으면 신규 MySQL MCP를 만들지 않고 **이미 설치된 MySQL 설정은 유지**합니다. 일부만 설정하면 쓰기 전에 오류로 종료합니다. REA도 새 override가 없으면 기존 실행 경로를 보존합니다. 따라서 다른 컴퓨터에서 업데이트해도 기존 연결 정보를 빈 값으로 덮어쓰지 않습니다.

### 기존 컴퓨터에서 환경값 이전

Python 3.11+로 실행합니다. 시스템 Python이 오래된 경우 아래처럼 `uv`를 사용합니다.

```bash
# 설치된 config.toml에서 MySQL 식별자와 REA 실행 경로만 추출합니다.
# 이미 환경 파일에 있는 키는 보존하고, 값은 터미널에 출력하지 않습니다.
uv run --python 3.13 python codex/migrate-env.py
./codex/sync.sh --dry-run
./codex/sync.sh
```

`migrate-env.py --config <config.toml> --env-file <private-env-file>`로 위치를 지정할 수 있습니다. `auth.json`, API 키, 비밀번호, 세션은 이전하지 않습니다. 다른 컴퓨터에서는 기존 설정에서 다시 추출하거나 해당 컴퓨터의 경로로 설정하세요. 이 변경은 현재 소스에서 개인 기본값을 제거하며 과거 Git 이력을 재작성하지 않습니다.

## 계정을 전환해도 같은 스킬 사용

일반 sync는 관리 스킬을 선택된 Codex 홈에 설치하고 `~/.agents/skills/<skill-name>`에서 같은 파일을 가리키게 합니다. 계정별 `CODEX_HOME`이 달라도 사용자 공통 경로에서 발견할 수 있습니다. [공식 스킬 탐색 위치](https://developers.openai.com/codex/skills/)

- 사용자 공통 경로의 다른 스킬은 유지합니다. 같은 이름의 다른 소유 파일이 있으면 덮어쓰지 않고 중단합니다.
- `auth.json`, 로그인 상태, 대화 기록과 SQLite 데이터는 복사하거나 합치지 않습니다.
- 기존 계정 홈이 전체 관리 콘텐츠를 심볼릭 링크로 공유한다면 원본 홈에 동기화합니다. 인증은 계정별로 유지합니다.
- `--target-dir`를 지정하면 격리 설치로 간주해 공통 경로에 쓰지 않습니다. 공통 연결도 원하면 `--shared-skills-dir <directory>`를 함께 지정합니다. Codex의 기본 사용자 탐색 위치는 `~/.agents/skills`입니다.
- `spring-workflow`는 기존 정책대로 명시적 호출용입니다. `$spring-workflow`로 호출합니다. 자동 선택 목록과 명시적 호출 가능 여부를 구분하세요.
- 설치 후 현재 프로세스에 반영되지 않으면 새 세션에서 확인합니다. 플러그인 포함 스킬의 계정 권한은 로컬 스킬 공유와 별개입니다.

계정별 실제 스킬 발견 여부는 다음 명령으로 검증합니다. 모델을 실행하거나 로그인하지 않고, Codex app-server의 `skills/list`에서 관리 스킬의 누락·비활성화·중복·로딩 오류와 인증 파일 보존을 확인합니다.

```bash
python3 scripts/verify-codex-skills.py --home ~/.codex --home /path/to/other-codex-home
```


## Claude Code에서 같은 스킬 사용

`codex/`는 로컬 마켓플레이스 `agent-workbench`이자 플러그인 `z`의 루트입니다. Claude Code에서는 관리 스킬이 `/z:<skill-name>`으로 표시됩니다. 다른 명령과 이름이 겹치지 않으면 `/<skill-name>`으로도 호출됩니다. [플러그인 로딩 문서](https://code.claude.com/docs/en/plugins/loading)

- 로컬 경로 마켓플레이스이므로 Claude Code는 복사본 없이 이 저장소의 `codex/skills`를 직접 읽습니다. 수정 사항은 새 세션 또는 `/reload-plugins`에서 반영되며 재설치가 필요 없습니다.
- sync(`--target-dir` 미지정, 또는 `--claude-plugin`)는 `claude` CLI가 있으면 마켓플레이스와 플러그인 등록을 확인합니다. 없거나 다른 clone 경로로 등록되어 있으면 이 clone으로 다시 등록합니다. 다른 컴퓨터에서는 clone 후 `./codex/sync.sh`를 한 번 실행하면 됩니다.
- 플러그인 루트를 저장소 루트가 아닌 `codex/`로 둡니다. 저장소 루트의 `.mcp.json`이 플러그인 MCP 서버로 함께 로드되지 않게 하기 위해서입니다.
- 스킬을 추가하거나 삭제하면 `codex/.claude-plugin/marketplace.json`의 `skills` 목록도 갱신합니다. 목록이 다르면 sync가 변경 전에 중단합니다. Codex 대화 기록만 검색하는 `find-session`은 목록에서 제외합니다.
- Claude Code는 홈 안쪽 작업 경로에서 `~/AGENTS.md`를 직접 읽습니다(v2.1.277+). [Claude Code 메모리 문서](https://code.claude.com/docs/en/memory#agents-md)

## 검사 설정이 없는 프로젝트 리뷰

`spring-review`는 프로젝트 검사 설정을 우선 사용하고, 없으면 독립 실행형 기본 검사를 사용할 수 있습니다. 프로젝트 빌드 파일이나 소스는 수정하지 않습니다.

```bash
# 필요한 언어의 도구만 사용자 캐시에 설치 (공식 배포물·고정 SHA-256 검증)
python3 codex/skills/spring-review/scripts/setup_tools.py ktlint detekt pmd
# 패키지 디렉터리 또는 단일 Java/Kotlin 소스 파일
python3 codex/skills/spring-review/scripts/check_sources.py /path/to/package
```

테스트한 기본 버전은 ktlint 1.8.0, detekt 1.23.8, PMD 7.20.0입니다. 설치된 PATH 명령이나 실행 파일 환경변수로 대체할 수 있지만 CLI 형식과 언어 버전 호환성을 확인해야 합니다. Bash·Java 17+가 필요하며 도구 설치 시에만 다운로드합니다.

결과는 임시 디렉터리의 `summary.json`, XML, 로그에 기록됩니다. 종료 코드 `0`은 선택된 검사에서 진단 없음, `1`은 진단 있음, `2`는 도구 없음·실패·시간 초과·검사 대상 없음입니다. 타입 정보가 없으면 검사 범위가 제한됩니다. 컴파일·Spring 모듈 경계·런타임 동작은 별도 검증 대상이며, 기본 규칙 진단을 프로젝트 규칙 위반으로 단정하지 않습니다. 상세 동작은 [독립 실행형 검사](skills/spring-review/references/standalone-checks.md)를 참조하세요.
