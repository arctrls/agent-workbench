---
name: mysql-read
description: Run read-only MySQL queries against the Thomas local Docker MySQL or the dev Aurora hmmall/thomas databases. Use when the user wants quick schema inspection, SQL lookups, NATION/STATE mapping checks, or direct read-only validation without relying on MCP.
---

# MySQL Read

Use the bundled shell script for read-only MySQL access. Always choose the
database target deliberately before running a query.

Default targets:
- `local`: the developer's local Thomas Docker MySQL, reached through the local `mysql` client
- `dev`: the shared DEV Aurora read endpoint, reached through the local `mysql` client after loading credentials from AWS Secrets Manager

## Workflow

1. Decide the target:
   - Use `local` only for local Docker data seeded or generated on this machine.
   - Use `dev` only for shared development data in Aurora after `aws sso login`.
   - If the user says "local", "Docker", "compose", "seeded data", "my machine", or asks to validate a local change, use `local`.
   - If the user says "DEV", "development DB", "Aurora", "shared data", "real dev data", or asks to compare against the deployed development environment, use `dev`.
   - If the request does not identify the data source and the answer would differ between local and DEV, ask one concise clarifying question before querying.
2. Keep queries read-only.
3. Run the script instead of hand-assembling credentials inline.
4. Summarize the result briefly and include the important rows or counts in the reply.
5. Mention which target was queried (`local` or `dev`) in the reply when the distinction matters.

## Commands

```bash
~/.codex/skills/mysql-read/scripts/mysql-read.sh --target local --database hmmall --sql "SELECT 1"
```

```bash
~/.codex/skills/mysql-read/scripts/mysql-read.sh --target dev --database hmmall --sql "SELECT NATION_NO, COUNTRY_ID, DEF_NATION_NM FROM NATION WHERE COUNTRY_ID IN ('US','CA')"
```

## Behavior

- Only `SELECT`, `SHOW`, `DESCRIBE`, `DESC`, `EXPLAIN`, and `WITH ... SELECT` queries are allowed.
- `local` uses a running Docker MySQL container and defaults to:
  - host `127.0.0.1`
  - port `3306`
  - user `user`
  - password `pass`
- `dev` defaults to:
  - AWS profile `default`
  - region `ap-northeast-2`
  - host `dev-20251223-cluster.cluster-ro-cn1xjryhj9xq.ap-northeast-2.rds.amazonaws.com`
  - secret ARN `arn:aws:secretsmanager:ap-northeast-2:170023315897:secret:database/mcp/dev/credentials-7bZ8iP`
- Override defaults with flags or env vars when needed.
- Do not use Docker as a MySQL client shim. The script assumes the local `mysql` client is installed and uses it for both targets.
- `local` never reads AWS Secrets Manager. `dev` never depends on a local Docker container.

## Common Cases

- Find a nation number:
  - `--sql "SELECT NATION_NO, COUNTRY_ID, DEF_NATION_NM FROM NATION WHERE COUNTRY_ID = 'US'"`
- Check state code mapping:
  - `--sql "SELECT NATION_NO, STATE_NM, STATE_CD FROM STATE WHERE STATE_NM = 'New York'"`
- Inspect schema:
  - `--sql "SHOW COLUMNS FROM STATE"`

## Prerequisites

- `mysql`
- `aws`

If `local` is used, the Thomas MySQL container must be reachable from the host, normally at `127.0.0.1:3306`.
If `dev` is used, run `aws sso login` first.
