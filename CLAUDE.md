# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a new/empty project. The codebase has not been built out yet.

## Environment

- Linux (6.17.0-22-generic)
- Shell: bash

## Directory

Project root: `/home/leebruce/Project_cc`

## Skill Usage Conventions

Always invoke the relevant skill before performing these categories of work. Skills produce better results than ad-hoc implementation.

### Design & UI
- **`frontend-design`** — Before writing any HTML, CSS, or UI components. Generates distinctive, production-grade interfaces and avoids generic AI aesthetics.

### Code Quality & Security
- **`simplify`** — After non-trivial code changes, review for reuse opportunities, quality issues, and efficiency improvements.
- **`security-review`** — Before merging changes that touch auth, data handling, API endpoints, or user input. Catches vulnerabilities that casual review misses.
- **`review`** — When asked to review a pull request on GitHub. Use `pr-review-toolkit:review-pr` for more comprehensive multi-agent reviews.

### Git Workflow
- **`commit-commands:commit`** — When asked to create a git commit.
- **`commit-commands:commit-push-pr`** — When asked to commit, push, and open a PR in one step.
- **`commit-commands:clean_gone`** — To clean up local branches whose remotes have been deleted.

### Project Configuration
- **`update-config`** — When changing settings.json, configuring permissions, setting env vars, or managing hooks. Examples: "allow npm commands", "set DEBUG=true", "add permission for X".
- **`fewer-permission-prompts`** — When permission prompts become frequent during a session, scan transcripts and add an allowlist to reduce interruptions.
- **`claude-md-management:claude-md-improver`** — When asked to audit, improve, or update CLAUDE.md files. `claude-md-management:revise-claude-md` to append learnings from the current session.
- **`init`** — When initializing a new project that lacks a CLAUDE.md, use to scaffold one.

### Feature Development
- **`feature-dev`** — For complex feature development that requires codebase understanding and architectural planning.

### Claude API / Anthropic SDK
- **`claude-api`** — When writing, debugging, or optimizing code that uses the Anthropic SDK or Claude API. Handles model migrations (4.5→4.6→4.7), prompt caching, and API best practices.

### Loops & Automation
- **`loop`** — When the user wants a recurring task or polling loop (e.g., "check deploy status every 5 minutes").
- **`hookify:hookify`** — To create automated hooks that enforce behaviors from conversation analysis or explicit instructions.

## Development Commands

Add build, test, lint, and run commands here once the project is initialized.
