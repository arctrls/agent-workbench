---
name: session-to-skills
description: Extract reusable code-review feedback and design decisions from a conversation, compare them with existing skills, and recommend or apply focused updates. Use when the user asks to turn session lessons into skill guidance.
---

# Session to Skills

Turn supported session lessons into concise guidance, not a transcript archive.

## Workflow

1. Extract explicit user feedback, accepted decisions, and recurring corrections. Prefer the latest confirmed decision over superseded proposals. Separate user requirements from assistant interpretations; flag missing context instead of inventing it.
2. Choose the scope: shared rules belong in common skills, repeatable specialist procedures in focused skills, and repository conventions in project instructions or references. Keep one-off exceptions local.
3. Read the relevant existing skills and their canonical sources. Identify gaps, duplicates, and conflicts. Prefer updating an existing skill; create a new one only for a distinct trigger and reusable workflow. Check linked references and reviewer prompts for consistency.
4. Match the request:
   - **Recommend:** show session evidence, the proposed reusable rule, and its destination. Do not edit.
   - **Apply:** use `skill-creator`, edit the canonical source, validate, and follow the repository's sync process. Reuse existing authorization; do not ask again for approved work. Commit and push only when requested.
5. Report what changed, where it lives, and what validation and synchronization completed. State commit/push status separately.

## Generalization Check

- A task-specific test deletion is not a ban on tests; a no-lock decision is not a universal locking policy.
- Keep feature-specific authorization, timezone, status, and delivery contracts out of global rules unless explicitly generalized.
- Do not treat an assistant suggestion or user silence as an accepted preference.
- Preserve useful exceptions, remove conflicting wording, and avoid adding a rule already covered elsewhere.
- Record only decision-changing guidance. Do not copy secrets, customer data, or incidental operational identifiers from the session.
