---
name: create-production-data-fix
description: Create a reviewable MySQL SQL file for correcting production data without executing it. Use when the user asks for a production or commercial data correction, restoration, one-off UPDATE, or one-off INSERT whose current production values must be read from a Databricks replica while the authoritative table schema and primary key must be inspected in the DEV MySQL database.
---

# Create Production Data Fix

Create a MySQL correction file from read-only evidence. Never execute the
generated file or any data-changing statement.

## Safety Boundaries

- Treat DEV MySQL as authoritative only for table structure, column types,
  nullability, defaults, and primary keys.
- Treat the Databricks production replica as authoritative for current
  production row values and target discovery.
- Use only read-only queries against both systems.
- Never update, insert into, delete from, merge into, or otherwise mutate a
  Databricks table.
- Never connect to production MySQL or execute DML in any database.
- Never execute the generated SQL file, even when the user asks for
  verification. Verify its text statically instead.
- Create the correction as a `.sql` file. Do not return DML only in chat.
- Omit `START TRANSACTION`, `BEGIN`, `COMMIT`, and `ROLLBACK`. Let the user
  control transaction boundaries.

## Workflow

1. Identify the target MySQL database, table, requested correction, and output
   location. If the user does not specify a path, create a descriptive `.sql`
   file in the current working directory.
2. Load and follow `$mysql-read` for read-only DEV access. Inspect the DEV
   MySQL schema with commands such as `SHOW CREATE TABLE`, `SHOW COLUMNS`, and
   `SHOW KEYS`. Do not use DEV row values as a substitute for production data.
3. Confirm the exact primary key from DEV MySQL. For a composite primary key,
   record every component in key order. Do not infer a key from names, unique
   indexes, application code, or the Databricks schema.
4. Query the Databricks replica with `SELECT` only. Read the current target
   rows, their complete primary keys, and the columns needed to derive literal
   correction values. Read-only joins or calculations may be used for
   investigation, but never copy them into DML.
5. Resolve the intended result into explicit rows and literal values. For an
   `UPDATE`, confirm that every target row exists in the replica. For an
   `INSERT`, check the proposed primary key in the replica and confirm that no
   row currently exists.
6. Write every backup `SELECT` at the top of the file, before any DML. Then
   write one single-row `UPDATE` or `INSERT` per primary key.
7. Review the file text against the SQL file rules below. Do not run the file or
   paste its DML into a database client.
8. Report the file path, affected tables, statement counts, and which evidence
   came from DEV MySQL versus Databricks. State any freshness or access
   limitation.

## SQL File Rules

Place a brief warning comment at the beginning, followed by all backup queries:

```sql
-- REVIEW REQUIRED: generated production correction SQL; not executed.

-- Backup rows
SELECT
    `id`,
    `column_to_change`
FROM `database_name`.`table_name`
WHERE `id` = 123;

-- Corrections
UPDATE `database_name`.`table_name`
SET `column_to_change` = 'corrected literal'
WHERE `id` = 123;
```

Apply all of these rules:

- Select the full primary key and every column that the corresponding DML will
  write. Put all such backup `SELECT` statements before the first DML
  statement.
- Use the same exact full-primary-key equality predicate in the backup
  `SELECT` and its corresponding `UPDATE`.
- For composite keys, join every key component with `AND`.
- Use only `=` predicates with literal primary-key values. Do not use `IN`,
  ranges, patterns, non-primary-key predicates, or `LIMIT` to identify rows.
- Generate one `UPDATE` per row. Do not use joined updates, multi-table
  updates, CTEs, subqueries, `CASE`, arithmetic, functions, or expressions in
  `SET`.
- Assign only explicit MySQL literals or `NULL` in `SET`. Render dates and
  timestamps as explicit quoted values rather than `NOW()` or other functions.
- Generate one single-row `INSERT ... VALUES (...)` per row with an explicit
  column list and every primary-key column included. Do not use multi-row
  values, `INSERT ... SELECT`, `ON DUPLICATE KEY UPDATE`, or `REPLACE`.
- Do not change a primary-key value unless the user explicitly requested that
  exact key change and both the old and new key values were checked.
- Quote identifiers with MySQL backticks and escape string literals for MySQL.
- Do not add transaction-control statements, export commands, stored
  procedures, session settings, or executable shell commands.

For an `INSERT`, make its backup query select the explicit insert columns by
the proposed full primary key. The empty result is the evidence the user can
preserve before inserting.

## Stop Conditions

Stop and request the missing information without creating guessed DML when:

- DEV MySQL schema access is unavailable, the table has no primary key, or the
  full primary key cannot be established.
- Databricks replica access is unavailable and the user has not supplied the
  exact production rows needed to establish target keys and values.
- The replica result is ambiguous, unexpectedly broad, or may be stale enough
  to make the correction unsafe.
- Any target cannot be enumerated by its complete primary key.
- A desired value cannot be represented as a known MySQL literal.
- An insert would reuse an existing primary key.

Never relax these conditions by using DEV data as production truth or by
writing broader DML.
