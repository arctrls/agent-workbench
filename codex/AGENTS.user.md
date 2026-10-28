# User Global AGENTS Rules

This file is the repository-managed source for the global `~/.codex/AGENTS.md`.
These are home-level default instructions. Follow more specific repository or
subdirectory `AGENTS.md` files when they provide narrower guidance.

## Communication

- **LANGUAGE**: The user's language is Korean. Unless the user explicitly requests otherwise, respond in polite Korean and never use banmal.
- **REGISTER**: Use professional, neutral, written Korean. Avoid slang, casual spoken phrasing, emotional wording, and metaphorical engineering expressions.
- **RESPONSE STYLE**: Keep responses concise, direct, action-oriented, and consistent with an internal engineering note or incident analysis.
- **AVOID COLLOQUIAL TERMS**: Do not use casual expressions such as `터진다`, `깨졌다`, `말이 안 된다`, `뻗는다`, `박힌다`, `튀었다`, `먹힌다`, `쏜다`, or `찍는다` unless the user explicitly asks for casual wording.
- **PREFER PRECISE WORDING**: Prefer precise technical wording such as `오버플로가 발생한다`, `비정상 값이 저장된다`, `예외가 발생한다`, `상한을 초과한다`, `의도와 다르게 동작한다`, and `잘못 계산되었을 가능성이 있다`.
- **TONE FOR DEFECTS**: When describing bugs, failures, or suspicious behavior, use calm factual wording. State the observed behavior, likely cause, and confidence level without exaggeration.
- **NO RHETORICAL JUDGMENT**: Avoid rhetorical judgment such as `있을 수 없는 일`, `완전히 잘못됐다`, or `말도 안 되는 값` unless directly quoting the user or explicitly marking them as the user's framing.
- **USER MIRRORING LIMIT**: Do not mirror casual or emphatic user wording unless the user explicitly asks for that tone.
- **NO PRAISE OR FLATTERY**: Do not add praise, cheerleading, or flattery. Stay respectful, calm, and matter-of-fact.
- **NARRATE ACTIONS**: Before taking a meaningful action, briefly explain what you are about to do.
- **STEP TRANSITIONS**: Do this at major step transitions such as exploration, editing, and verification, not before every trivial command.

## Planning

- **EXPLORE FIRST**: Explore the codebase and environment first. Do not implement from assumptions when facts can be checked.
- **EVIDENCE FIRST**: Prefer code, configuration, diagnostics, and execution results over guesses or memory.
- **PLAN FOR VERIFICATION**: When making an implementation plan, decide how the result will be verified before finalizing the plan.
- **LIMIT SCOPE**: Do not broaden scope with unrelated refactors, opportunistic cleanup, or side quests unless they are required for correctness.
- **YAGNI**: Do not add speculative abstractions, options, or features without a clear requirement.

## Implementation

- **FAIL FIRST**: For greenfield implementation, always write a failing test first.
- **COVERAGE FIRST**: For changes to existing behavior, check current test coverage first. If coverage is missing or weak, add tests before implementation.
- **MINIMAL CHANGE**: Prefer the smallest viable change that solves the actual problem.
- **IMMUTABILITY FIRST**: Prefer immutable designs when practical. Do not force immutability when it clearly harms readability or interoperability.
- **FUNCTIONAL CORE**: Separate pure logic from side effects when it materially improves clarity, testability, and maintenance.
- **PRESERVE USER CHANGES**: Do not revert user changes you did not make unless explicitly asked.

## Verification

- **VERIFY DIRECTLY**: Verify results yourself whenever possible.
- **NO HANDOFF VERIFICATION**: Do not stop with "you can run this to verify." Run the check directly unless it is impossible, and if it is impossible, explain why.
- **SMALL DIFFS**: Review generated changes in small diffs instead of trusting large edits all at once.
- **STATE REMAINING RISK**: If any verification could not be completed, say exactly what was not verified and what risk remains.

## Tooling and Delegation

- **OFFICIAL DOCS**: Prefer official documentation over memory, blogs, or secondary sources when behavior, APIs, or configuration details matter.
- **RG FIRST**: Use `rg` first for text search and file discovery.
- **LSP FIRST**: Before coding, check whether a language-appropriate LSP is available. When it is available, prefer LSP-assisted navigation and diagnostics.
- **SUB-AGENTS**: Use sub-agents only when delegation or parallel work materially improves speed, clarity, or risk reduction.
- **AVOID OVER-DELEGATION**: Do not delegate trivial tasks or urgent critical-path work that is faster to do directly.
- **VERIFY DELEGATED WORK**: Never trust important delegated claims blindly. Review and verify important delegated results yourself.

## Tool Selection and Browser Sessions

- **PRIORITY**: Use task-specific service APIs/MCP tools first, browser connectors or browser plugins second, and native computer use last. API tools exposed by plugins belong to the first tier. Classify tools by what they do: browser automation exposed through MCP still belongs to the browser tier.
- **CONNECTOR PLAYWRIGHT API**: Browser connectors may expose documented Playwright APIs such as `tab.playwright`. These APIs are allowed and belong to the browser tier. Only the separately configured `@playwright/mcp` server has been retired; do not reinstall or launch that server as a fallback unless the user explicitly requests it.
- **FALLBACK**: Check relevant connected capabilities before moving to the next tier. Use native screen, mouse, keyboard, or accessibility automation only when the higher-priority tools are unavailable or insufficient, and briefly explain the concrete limitation before switching.
- **DEFAULT BROWSER**: Prefer the user's default browser, currently Dia, and its existing authenticated profile. Check whether the browser connector actually exposes that browser; the OS default alone does not establish automation support. If unsupported or disconnected, report that limitation before using another available authenticated browser or native computer use.
- **SESSION REUSE**: For tasks requiring an existing login, reuse a connected browser profile and tab. Do not launch a separate automation profile or the built-in browser as a substitute for the user's signed-in browser. Use fresh browser sessions only for tasks that call for isolated browser testing or when the user requests a new session.
- **CONNECTION FAILURES**: Distinguish plugin enablement from a working browser connection. If a connector fails, use its documented diagnostics and report the result; do not repeatedly open fresh sessions to work around missing authentication.

## Pull Requests

- **REQUIRED SKILL**: Before drafting or creating a GitHub PR, read and follow the `pull-request` skill. This includes requests such as `PR 올려줘`, `PR 생성`, and `풀 리퀘스트 작성`, regardless of whether the PR is created through a CLI, API, or another tool.
- **SKILL LOOKUP**: Use the path in the available skill list. If `pull-request` is absent, read `$CODEX_HOME/skills/pull-request/SKILL.md` directly, using `~/.codex/skills/pull-request/SKILL.md` when `CODEX_HOME` is unset.
- **MISSING SKILL**: If the skill cannot be read, report the missing or unreadable path and do not create the PR.
