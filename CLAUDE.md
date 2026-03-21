# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CRITICAL: Single Source of Truth

**This project (`/Users/jazzbach/projects/prompts`) is the ONLY source of truth for Claude Code and personal Codex configuration.**

- All changes MUST be made in this project FIRST
- The home directory (`~/.claude/`) is synced FROM this project, never the reverse
- The home directory (`~/.codex/`) is also synchronized FROM this project for declarative configuration
- The home-level `~/AGENTS.md` is also generated FROM this project via `codex/AGENTS.user.md`
- When comparing directories: copy FROM this project TO home, never delete from this project
- Repo-managed Git hooks can run `codex/sync.sh` on push/pull after `git config core.hooksPath .githooks`

**Claude sync targets:** `CLAUDE.md` + `claude/` directory contents → `~/.claude/` via `claude/sync.sh`
**Codex sync targets:** `codex/config.base.toml` + `codex/sync.sh` → `~/.codex/config.toml`, plus `codex/prompts`, `codex/skills`, and `codex/AGENTS.user.md` → `~/AGENTS.md`
**Excluded from version control:** `~/.omx` (runtime state, logs, and sessions only)

Use `./codex/sync.sh` to sync managed Codex config keys, prompts, skills, and the global home `AGENTS.md`.
Do not import Codex home config back into this repo; this project remains the sole source of truth.

## Common Commands

This repository contains no build system, but operates through prompt templates and configuration sync:

```bash
# Enable repo-managed Git hooks for Codex sync on push/pull
git config core.hooksPath .githooks

# Commit changes
git commit -m "Updated prompts"

# Run sensitive data pre-check (recommended before commit)
./scripts/check-sensitive-data.sh

# Manually sync Claude assets
./claude/sync.sh

# Check project structure
tree -d -L 3
```

## Extension Development Guidelines

When creating custom extensions for this prompt system:

- **Slash Commands**: Follow the official Claude Code documentation at https://docs.anthropic.com/en/docs/claude-code/slash-commands
- **Sub-agents**: Refer to the sub-agent guidelines at https://docs.anthropic.com/en/docs/claude-code/sub-agents

These resources provide comprehensive patterns and best practices for extending the system's capabilities.

## High-Level Architecture

This repository is a comprehensive prompt engineering workspace for AI-assisted software development, with particular focus on Test-Driven Development (TDD) and Kent Beck's methodologies.

## Code Style and Conventions

This project follows strict Java code style guidelines to ensure consistency and maintainability:

- **Comprehensive Guide**: See `claude/docs/CODE-STYLE-GUIDE.md` for detailed Java and Spring Framework coding standards
- **Quick Reference Commands**: 
  - `/blame-code-style` - For Java code style violations
  - `/blame-spring` - For Spring Framework rule violations

### Key Principles

- **YAGNI**: Only implement features with clear usage requirements
- **Record Style**: Use `xxx()` instead of `getXxx()` for all accessor methods
- **Immutability**: All parameters and local variables must be `final`
- **Package-by-Feature**: Organize code by business features, not technical layers
- **DIP Compliance**: Depend on abstractions, not concrete implementations

### Directory Structure

- **claude/**: Core prompt system organized into specialized components
  - **agents/**: Specialized AI agent configurations for different development tasks
  - **commands/**: Slash command templates organized by domain
    - **tdd/**: TDD-specific prompts following Kent Beck's principles
    - **obsidian/**: Knowledge management and note-taking workflows
    - **tdp/**: Test-Driven development Patterns
  - **obsidian-presets/**: Configuration files for Obsidian vault operations

### Key Prompt Categories

#### TDD Development System

- **general-tdd.md**: Single-feature TDD workflow with AI pair programming
- **web-usecase-tdd.md**: Full-stack use case development with Spring Boot, REST, JPA
- **tdd-rules.md**: Comprehensive TDD rules and patterns following Kent Beck's three laws
- **tdd-samples.md**: Reference examples and approved test patterns

#### Specialized Agents

- **kent-beck-expert.md**: Kent Beck methodology guidance
- **tdd-expert.md**: TDD-specific expertise
- **spring-expert.md**: Spring ecosystem development
- **vibe-coding-coach.md**: Conversational application building
- **code-refactorer.md**: Code improvement without functionality changes

#### Development Workflow Integration

- Git post-commit hooks automatically sync prompts to `~/.claude/`
- Supports IntelliJ IDEA workflow with open file context
- Korean language support for documentation and communication

### Prompt Engineering Patterns

#### Reference System

- Rules defined in `tdd-rules.md` referenced as `<ground-rule>`, `<feedback-rule>`
- Samples defined in `tdd-samples.md` referenced as `<srs-samples>`, `<boundary-condition-samples>`
- Modular, reusable prompt components

#### TDD Workflow

1. SRS (Software Requirements Specification) creation
2. Example generation for specification validation
3. Test case list development
4. Iterative test implementation following red-green-refactor cycle
5. Walking skeleton for end-to-end architecture

#### Quality Assurance

- Approval testing patterns for complex output validation
- Boundary condition testing
- Feedback loops at each development stage
- Korean documentation standards

### Special Considerations

- **Pair Programming Focus**: Prompts designed for human-AI collaboration
- **Language Mixing**: Korean instructions with English code standards
- **Context Preservation**: Markdown documentation for session continuity
- **Incremental Development**: Emphasis on small, verifiable steps
- **No Premature Refactoring**: Explicit rules against early optimization

This system enables structured, methodical development with AI assistance while maintaining Kent Beck's TDD discipline and providing clear guidance for complex software engineering tasks.
