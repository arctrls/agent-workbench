# Standalone checks for an unconfigured project

Use project-configured checks first. This fallback is for missing checks, not a replacement for the project's conventions or a reason to install Gradle/Maven plugins.

Resolve scripts relative to this installed skill. They share the workbench environment loader, installed by the repository's sync command.

```bash
python3 <skill-directory>/scripts/check_sources.py <package-directory-or-source-file>
```

- Kotlin: ktlint and detekt. Java: PMD's bundled quickstart ruleset. Mixed packages select all three.
- Executable lookup: `SPRING_REVIEW_KTLINT`, `SPRING_REVIEW_DETEKT`, or `SPRING_REVIEW_PMD`; then PATH; then the managed per-user cache. An explicit invalid override is reported as unavailable, not silently replaced.
- If tools are missing and local tool setup is authorized, use the installer below. It downloads only official artifacts, checks pinned SHA-256 values, and installs outside the project. Otherwise report the missing check and continue contextual review.

```bash
python3 <skill-directory>/scripts/setup_tools.py ktlint detekt pmd
```

Install only tools needed by the source languages. Tested versions are ktlint 1.8.0, detekt 1.23.8, and PMD 7.20.0. Java 17+ and Bash are needed; no Homebrew-specific paths are required. Use `JAVA_HOME` for a suitable runtime. Tool overrides must support these CLI/report formats; changing versions requires verification, especially for the Kotlin compiler used by detekt.

## Evidence and limits

- Source files are not auto-formatted, rewritten, or compiled. Reports and tool working files go to a new system temporary directory by default. `--output` selects another directory outside the reviewed source directory.
- The runner excludes `.git`, `.gradle`, `.idea`, `build`, `target`, `generated`, and `node_modules` directories and symlinked source files in directory scans. Select a specific source file if it needs separate review.
- `summary.json` records tool/version, command, source count, status, exit code, findings count, report and log locations, and limitations. Exit 0 means selected checks completed without findings; 1 means findings; 2 means a missing tool, failure, timeout, or no applicable sources. A zero diagnostic count is not proof of compilation or runtime correctness.
- ktlint may use existing parent `.editorconfig` rules. detekt uses its active defaults, not every rule. `--classpath` is optional for detekt/PMD type-aware analysis and requires compatible compiler/dependency information; absence of type resolution must be reported. detekt is not a syntax checker and can emit no findings for malformed source; retain compiler/ktlint evidence separately.
- Basic checks do not establish Spring Modulith boundaries, transactions, security, concurrency correctness, or appropriate design. Do not synthesize architecture constraints and then call them established project requirements.
- Default-rule findings are review candidates. Deduplicate overlapping diagnostics and distinguish tool defaults from the project's adopted rules.

Cache root: `SPRING_REVIEW_CACHE_DIR`, otherwise `$XDG_CACHE_HOME/agent-workbench/review-tools`, otherwise `~/.cache/agent-workbench/review-tools`. Do not commit reports, downloaded binaries, or machine-specific executable paths.

Official CLI references: [ktlint](https://ktlint.github.io/ktlint/1.8.0/install/cli/), [detekt](https://detekt.dev/docs/1.23.8/gettingstarted/cli/), [PMD](https://pmd.github.io/pmd/pmd_userdocs_cli_reference.html).
