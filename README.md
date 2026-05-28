# My Marketplace

A collection of agent plugins for LLM observability, API exploration, and development workflows.

## Installation

This repository publishes marketplace metadata for both supported plugin runtimes:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

## Shared Instructions

Use `AGENTS.md` as the shared instruction file when a plugin needs runtime
context. Runtimes that read `AGENTS.md` can consume it directly.

For runtimes that read `CLAUDE.md`, keep a sibling `CLAUDE.md` next to every
`AGENTS.md` and import the shared file:

```md
@AGENTS.md
```

This keeps both supported runtimes on the same instructions without copying
content between files.

```shell
/plugin marketplace add Alex-Kopylov/my-marketplace
```

Use the equivalent marketplace add command if your runtime uses a CLI command
instead of slash commands.

Then install individual plugins:

```shell
/plugin install langfuse@my-marketplace
```

## Plugins

### langfuse

General-purpose Langfuse integration for data exploration, dashboard management, prompt versioning, datasets, and experiments.

**Skills:** analyze-experiment-results, compare-experiments, configure-remote-experiment, create-dataset, create-evaluator, create-widget, delete-evaluator, delete-widget, design-dataset-schema, discover-datasets, discover-filter-options, discover-models, discover-scores, discover-traces, inspect-evaluator, layout-widgets, list-dataset-runs, list-evaluators, list-widgets, manage-dashboard, manage-dataset-items, query-metrics, suggest-widgets, toggle-evaluator-status, trigger-experiment, update-evaluator, update-widget

**Agents:** langfuse-data-explorer, langfuse-dataset-expert, langfuse-eval-manager, langfuse-experiment-manager, langfuse-widget-manager

### openapi-tools

Skills for listing and inspecting OpenAPI endpoints on running services.

**Skills:** openapi-inspect, openapi-list

### llm-application-dev

LLM application design and schema-guided reasoning patterns.

**Skills:** schema-guided-reasoning

### python-dev-workflow

Python-specific pytest, Redis test patterns, Celery, and unit-test review/execution agents.

**Skills:** celery-expert, pytest-redis, writing-unit-tests

**Agents:** test-runner, test-unit-reviewer

### dev-workflow

Git, PRs, tickets, releases, and review-comment workflows.

**Skills:** commit, create-pr, pr-address-comments, pr-checkout, pr-comment, spec-contradiction-hunter, spec-interview, ticket-branch, ticket-comment-status, version-bumper

**Agents:** ambiguity-contradiction-hunter, release-manager, structural-contradiction-hunter, surface-contradiction-hunter

### work-session-tools

Productivity and orchestration inside an assistant session.

**Skills:** create-team, daily, interview, task-management

### ai-assistant-ops

Assistant setup, instruction hygiene, memory capture, and markdown/prompt maintenance.

**Skills:** agents-md-improver, ai-insights-hunter, ai-setup-audit, md-bloat-hunter

### os-tools

Operating-system utilities for local machine automation.

**Skills:** loop_macos

### cloud-storage-tools

Dropbox, Google Drive, OneDrive, and MEGA style user-file storage tools.

**Skills:** mega-cmd

### job-hunt-toolkit

Version-controlled job application workspace with resume tailoring, PDF export, metadata scrubbing, and pre-send checks.

**Skills:** export-pdf, init-workspace, new-application, prepare-to-send, resume-tailoring, scrub-pdf-metadata

## Recommended Third-Party Plugins

These are useful companion plugin and skill collections to consider alongside this marketplace:

- [browser-harness](https://github.com/browser-use/browser-harness) - direct browser control through CDP.
- [plannotator](https://github.com/backnotprop/plannotator) - browser-based plan review, annotation, and visual explanation workflows.
- [worktrunk](https://github.com/max-sixty/worktrunk) - worktree and branch workflow support.
- [ralphex](https://github.com/umputun/ralphex) - AI-assisted development planning and project workflow tools.
- [wshobson/agents](https://github.com/wshobson/agents) - Claude Code workflow skills for Python, LLM applications, debugging, testing, and PR work.

## Updating

```shell
/plugin marketplace update my-marketplace
```
