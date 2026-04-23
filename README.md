# Claude Code Plugin Marketplace

A collection of Claude Code plugins for LLM observability, API exploration, and Python development workflows.

## Installation

```shell
/plugin marketplace add Alex-Kopylov/claude-marketplace
```

Then install individual plugins:

```shell
/plugin install langfuse@my-plugins
/plugin install openapi-tools@my-plugins
/plugin install python-dev-workflow@my-plugins
```

## Plugins

### langfuse

General-purpose Langfuse integration — data exploration, dashboard/widget management, prompt versioning, dataset/experiment management, and more via conversational interface.

**Skills:** create-evaluator, update-evaluator, delete-evaluator, inspect-evaluator, list-evaluators, toggle-evaluator-status, discover-filter-options, discover-traces, discover-models, discover-scores, discover-datasets, create-dataset, manage-dataset-items, design-dataset-schema, trigger-experiment, configure-remote-experiment, analyze-experiment-results, compare-experiments, list-dataset-runs, query-metrics, create-widget, update-widget, delete-widget, list-widgets, suggest-widgets, layout-widgets, manage-dashboard

**Agents:** langfuse-data-explorer, langfuse-eval-manager, langfuse-dataset-expert, langfuse-experiment-manager, langfuse-widget-manager

### openapi-tools

Skills for listing and inspecting OpenAPI endpoints on running services (FastAPI, etc.).

**Skills:** openapi-list, openapi-inspect

### python-dev-workflow

Python development workflow — pytest test execution & review agents, conventional commits, PR creation, branch management, unit testing guide, and task management with background agent orchestration.

**Skills:** commit, create-pr, pr-checkout, ticket-branch, ticket-comment-status, version-bumper, writing-unit-tests, pytest-redis, task-management, contradiction-hunter

**Agents:** test-runner, test-unit-reviewer

## Updating

```shell
/plugin marketplace update my-plugins
```
