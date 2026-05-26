#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF' >&2
Usage:
  mysql-read.sh --target local|dev --database <db> --sql "<query>" [options]

Options:
  --target <local|dev>
  --database <name>
  --sql <query>
  --host <mysql-host>
  --port <mysql-port>
  --user <mysql-user>
  --password <mysql-password>
  --profile <aws-profile>
  --region <aws-region>
  --secret-arn <aws-secret-arn>

Env overrides:
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

target=""
database=""
sql=""
host_override=""
port_override=""
user_override=""
password_override=""
local_host="${MYSQL_READ_LOCAL_HOST:-127.0.0.1}"
local_port="${MYSQL_READ_LOCAL_PORT:-3306}"
local_user="${MYSQL_READ_LOCAL_USER:-user}"
local_password="${MYSQL_READ_LOCAL_PASSWORD:-pass}"
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
    --secret-arn)
      secret_arn=${2:-}
      shift 2
      ;;
    *)
      usage
      ;;
  esac
done

if [[ -z "$target" || -z "$database" || -z "$sql" ]]; then
  usage
fi

validate_read_only_sql "$sql"
require_command mysql

case "$target" in
  local)
    host=${host_override:-$local_host}
    port=${port_override:-$local_port}
    user=${user_override:-$local_user}
    password=${password_override:-$local_password}
    MYSQL_PWD="$password" mysql -h "$host" -P "$port" -u"$user" -D "$database" -N -e "$sql"
    ;;
  dev)
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
