#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  mysql-read.sh --target local|dev --sql "<query>" [--database <db>] [options]

Options:
  --target <local|dev>
  --database <name>
  --sql <query>
  --host <mysql-host>
  --port <mysql-port>
  --user <mysql-user>
  --password <mysql-password>
  --project-dir <spring-boot-project-dir>
  --profile <aws-profile>
  --region <aws-region>
  --secret-arn <aws-secret-arn>

Env overrides:
  MYSQL_READ_PROJECT_DIR
  MYSQL_READ_LOCAL_HOST
  MYSQL_READ_LOCAL_PORT
  MYSQL_READ_LOCAL_USER
  MYSQL_READ_LOCAL_PASSWORD
  MYSQL_READ_DEV_PROFILE
  MYSQL_READ_DEV_REGION
  MYSQL_READ_DEV_HOST
  MYSQL_READ_DEV_PORT
  MYSQL_READ_DEV_SECRET_ARN
EOF
  exit 1
}

require_command() {
  local cmd=$1
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command not found: $cmd" >&2
    exit 1
  fi
}

trim() {
  local value=$1
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

validate_read_only_sql() {
  local sql trimmed lower
  sql=$1
  trimmed=$(trim "$sql")
  lower=$(printf '%s' "$trimmed" | tr '[:upper:]' '[:lower:]')

  if [[ ! "$lower" =~ ^(select|show|describe|desc|explain|with[[:space:]]) ]]; then
    echo "Error: only read-only queries are allowed" >&2
    exit 1
  fi

  if printf '%s' "$lower" | grep -Eq '(^|[^a-z])(insert|update|delete|replace|alter|drop|truncate|create|rename|grant|revoke|call|do|load[[:space:]]+data|lock|unlock|set[[:space:]]+global|set[[:space:]]+session)([^a-z]|$)'; then
    echo "Error: mutating SQL keyword detected" >&2
    exit 1
  fi
}

json_field() {
  local json=$1
  local field=$2
  python3 - "$json" "$field" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
field = sys.argv[2]
value = payload.get(field, "")
if value is None:
    value = ""
print(value)
PY
}

detect_spring_local_config() {
  local project_dir=$1
  python3 - "$project_dir" <<'PY'
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

project_dir = Path(sys.argv[1]).resolve()
candidate_names = {
    "application-local.properties",
    "application-local.yml",
    "application-local.yaml",
    "bootstrap-local.properties",
    "bootstrap-local.yml",
    "bootstrap-local.yaml",
}
candidate_dirs = [
    project_dir / "src/main/resources",
    project_dir / "src/test/resources",
    project_dir / "config",
    project_dir,
]


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def resolve_placeholders(value):
    def replace(match):
        body = match.group(1)
        if ":" in body:
            name, default = body.split(":", 1)
            return os.environ.get(name, default)
        return os.environ.get(body, "")

    return re.sub(r"\$\{([^}]+)\}", replace, value)


def parse_properties(path):
    values = {}
    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
        elif ":" in line:
            key, value = line.split(":", 1)
        else:
            continue
        values[key.strip()] = resolve_placeholders(unquote(value))
    return values


def parse_yaml_like(path):
    values = {}
    stack = []
    for raw in path.read_text(errors="ignore").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or raw.strip() == "---":
            continue
        match = re.match(r"^(\s*)([A-Za-z0-9_.-]+)\s*:\s*(.*)$", raw)
        if not match:
            continue
        indent = len(match.group(1).replace("\t", "  "))
        key = match.group(2)
        value = match.group(3).strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        path_keys = [item[1] for item in stack] + [key]
        if value == "":
            stack.append((indent, key))
        else:
            values[".".join(path_keys)] = resolve_placeholders(unquote(value))
    return values


def jdbc_parts(url):
    result = {}
    if not url:
        return result
    cleaned = url.strip()
    if cleaned.startswith("jdbc:"):
        cleaned = cleaned[5:]
    if cleaned.startswith("mysql:"):
        cleaned = cleaned[6:]
    parsed = urlsplit(cleaned)
    if parsed.hostname:
        result["host"] = parsed.hostname
    if parsed.port:
        result["port"] = str(parsed.port)
    database = parsed.path.lstrip("/").split("/", 1)[0]
    if database:
        result["database"] = database
    return result


def candidate_files():
    seen = set()
    for directory in candidate_dirs:
        if not directory.exists():
            continue
        for name in candidate_names:
            path = directory / name
            if path.exists() and path not in seen:
                seen.add(path)
                yield path
    for path in project_dir.rglob("application-local.*"):
        if path.is_file() and path.name in candidate_names and path not in seen:
            seen.add(path)
            yield path


selected = {}
for path in candidate_files():
    values = parse_properties(path) if path.suffix == ".properties" else parse_yaml_like(path)
    url = values.get("spring.datasource.url") or values.get("spring.datasource.hikari.jdbc-url")
    username = values.get("spring.datasource.username")
    password = values.get("spring.datasource.password")
    if not any((url, username, password)):
        continue
    selected.update(jdbc_parts(url))
    if url:
        selected["url"] = url
    if username:
        selected["user"] = username
    if password:
        selected["password"] = password
    selected["source"] = str(path)
    break

print(json.dumps(selected))
PY
}

detect_docker_mysql() {
  if ! command -v docker >/dev/null 2>&1; then
    printf '{}'
    return 0
  fi

  local docker_ps
  docker_ps=$(docker ps --format '{{json .}}' 2>/dev/null || true)
  python3 - "$docker_ps" <<'PY'
import json
import re
import sys

for raw in sys.argv[1].splitlines():
    if not raw.strip():
        continue
    item = json.loads(raw)
    name = item.get("Names", "")
    image = item.get("Image", "")
    ports = item.get("Ports", "")
    haystack = f"{name} {image} {ports}".lower()
    if "mysql" not in haystack and "mariadb" not in haystack and "3306/tcp" not in haystack:
        continue
    match = re.search(r"(?:(?:0\.0\.0\.0|127\.0\.0\.1|::|\[::\]):)?([0-9]+)->3306/tcp", ports)
    if not match:
        continue
    print(json.dumps({
        "host": "127.0.0.1",
        "port": match.group(1),
        "source": name,
    }))
    break
else:
    print("{}")
PY
}

target=""
database=""
sql=""
host_override=""
port_override=""
user_override=""
password_override=""
project_dir="${MYSQL_READ_PROJECT_DIR:-$PWD}"
local_host="${MYSQL_READ_LOCAL_HOST:-}"
local_port="${MYSQL_READ_LOCAL_PORT:-}"
local_user="${MYSQL_READ_LOCAL_USER:-}"
local_password="${MYSQL_READ_LOCAL_PASSWORD:-}"
profile="${MYSQL_READ_DEV_PROFILE:-default}"
region="${MYSQL_READ_DEV_REGION:-ap-northeast-2}"
dev_host="${MYSQL_READ_DEV_HOST:-dev-20251223-cluster.cluster-ro-cn1xjryhj9xq.ap-northeast-2.rds.amazonaws.com}"
dev_port="${MYSQL_READ_DEV_PORT:-3306}"
secret_arn="${MYSQL_READ_DEV_SECRET_ARN:-arn:aws:secretsmanager:ap-northeast-2:170023315897:secret:database/mcp/dev/credentials-7bZ8iP}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      target=${2:-}
      shift 2
      ;;
    --database)
      database=${2:-}
      shift 2
      ;;
    --sql)
      sql=${2:-}
      shift 2
      ;;
    --profile)
      profile=${2:-}
      shift 2
      ;;
    --region)
      region=${2:-}
      shift 2
      ;;
    --host)
      host_override=${2:-}
      shift 2
      ;;
    --port)
      port_override=${2:-}
      shift 2
      ;;
    --user)
      user_override=${2:-}
      shift 2
      ;;
    --password)
      password_override=${2:-}
      shift 2
      ;;
    --project-dir)
      project_dir=${2:-}
      shift 2
      ;;
    --secret-arn)
      secret_arn=${2:-}
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z "$target" || -z "$sql" ]]; then
  usage
fi

validate_read_only_sql "$sql"
require_command mysql

case "$target" in
  local)
    require_command python3
    config_json=$(detect_spring_local_config "$project_dir")
    docker_json=$(detect_docker_mysql)
    config_host=$(json_field "$config_json" host)
    config_port=$(json_field "$config_json" port)
    config_user=$(json_field "$config_json" user)
    config_password=$(json_field "$config_json" password)
    config_database=$(json_field "$config_json" database)
    docker_host=$(json_field "$docker_json" host)
    docker_port=$(json_field "$docker_json" port)

    host=${host_override:-${local_host:-${config_host:-${docker_host:-127.0.0.1}}}}
    port=${port_override:-${local_port:-${config_port:-${docker_port:-3306}}}}
    user=${user_override:-${local_user:-${config_user:-user}}}
    password=${password_override:-${local_password:-${config_password:-pass}}}
    database=${database:-$config_database}
    if [[ -z "$database" ]]; then
      echo "Error: --database is required when no Spring Boot local datasource database is found" >&2
      exit 1
    fi
    MYSQL_PWD="$password" mysql -h "$host" -P "$port" -u"$user" -D "$database" -N -e "$sql"
    ;;
  dev)
    if [[ -z "$database" ]]; then
      echo "Error: --database is required for dev" >&2
      exit 1
    fi
    require_command aws
    require_command python3
    secret_json=$(AWS_PROFILE="$profile" AWS_REGION="$region" aws secretsmanager get-secret-value \
      --secret-id "$secret_arn" \
      --query SecretString \
      --output text)
    host=${host_override:-$dev_host}
    port=${port_override:-$dev_port}
    dev_user=$(json_field "$secret_json" username)
    dev_password=$(json_field "$secret_json" password)
    user=${user_override:-$dev_user}
    password=${password_override:-$dev_password}
    MYSQL_PWD="$password" mysql -h "$host" -P "$port" -u"$user" -D "$database" -N -e "$sql"
    ;;
  *)
    echo "Error: unsupported target: $target" >&2
    exit 1
    ;;
esac
