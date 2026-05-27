# My Marketplace

A collection of agent plugins for LLM observability, API exploration, document handling, and development workflows.

## Installation

This repository publishes marketplace metadata for both supported plugin runtimes:

- `.claude-plugin/marketplace.json`
- `.agents/plugins/marketplace.json`

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

### file-manager

Document and data processing skills for PDF, PPTX, XLSX, and DOCX workflows.

**Skills:** docx, pdf, pptx, xlsx

### langfuse

General-purpose Langfuse integration — data exploration, dashboard/widget management, prompt versioning, dataset/experiment management, and more via conversational interface.

**Skills:** create-evaluator, update-evaluator, delete-evaluator, inspect-evaluator, list-evaluators, toggle-evaluator-status, discover-filter-options, discover-traces, discover-models, discover-scores, discover-datasets, create-dataset, manage-dataset-items, design-dataset-schema, trigger-experiment, configure-remote-experiment, analyze-experiment-results, compare-experiments, list-dataset-runs, query-metrics, create-widget, update-widget, delete-widget, list-widgets, suggest-widgets, layout-widgets, manage-dashboard

**Agents:** langfuse-data-explorer, langfuse-eval-manager, langfuse-dataset-expert, langfuse-experiment-manager, langfuse-widget-manager

### openapi-tools

Skills for listing and inspecting OpenAPI endpoints on running services (FastAPI, etc.).

**Skills:** openapi-list, openapi-inspect

### python-dev-workflow

Python development workflow — pytest execution and review helpers, conventional commits, PR creation, branch management, unit testing guidance, contradiction hunting, Celery support, and version bumping.

**Skills:** commit, create-pr, pr-checkout, ticket-branch, ticket-comment-status, version-bumper, writing-unit-tests, pytest-redis, task-management, contradiction-hunter

**Agents:** test-runner, test-unit-reviewer

### general-plugins

General-purpose workflow and setup utilities.

**Skills:** ai-setup-audit, ai-insights-hunter, daily, interview, loop_macos, md-bloat-hunter, mega-cmd, pr-address-comments, pr-comment, skill-creator, task-management

`/md-bloat-hunter [path]` audits a markdown file or a non-recursive directory
of direct child `*.md` files for redundancy, verbosity, filler, and vocabulary
compression. It requires `jsonschema` on PATH; install it with
`uv tool install jsonschema`. Approved findings mutate markdown files, so run it
from a clean git tree and review changes with `git diff`.

## Updating

```shell
/plugin marketplace update my-marketplace
```
