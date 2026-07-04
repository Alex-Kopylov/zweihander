---
name: langfuse
description: >-
  General-purpose Langfuse integration for observability, evaluations, datasets,
  dataset items, experiment runs, remote experiment webhooks, dashboard widgets,
  dashboards, metrics, traces, scores, models, and filter discovery. Use for any
  Langfuse task including discovering project data, querying metrics, creating
  or managing datasets, running or comparing experiments, creating or managing
  LLM-as-a-Judge evaluators, and creating or arranging dashboard visualizations.
---

# Langfuse

Use this as the single public Langfuse skill. The previous task-specific skills
are preserved as internal sub-skills under `references/sub-skills/`.

## Start

1. Read `../../AGENTS.md` for shared Langfuse data model, credentials, storage,
   and API/DB access strategy.
2. Classify the user request with the routing map below.
3. Read each matching `references/sub-skills/<name>/SKILL.md` before acting.
4. Resolve any sub-skill `references/...` links relative to that sub-skill
   directory, not relative to this file.
5. When a sub-skill says to invoke, use, or delegate to another former skill,
   read the matching internal sub-skill instead of looking for a separate
   exposed skill.
6. Load only the sub-skills needed for the task. Do not read every internal
   sub-skill by default.

For destructive operations, direct database writes, status changes, or webhook
configuration, follow the confirmation and safety checks in the selected
sub-skill before applying changes.

## Routing Map

| User intent | Internal sub-skills to read |
|---|---|
| Discover traces, trace names, tags, environments, sessions, or users | [`discover-traces`](references/sub-skills/discover-traces/SKILL.md) |
| Discover scores, score names, score types, or score sources | [`discover-scores`](references/sub-skills/discover-scores/SKILL.md) |
| Discover datasets, dataset metadata, items, or runs | [`discover-datasets`](references/sub-skills/discover-datasets/SKILL.md) |
| Discover dataset runs | [`list-dataset-runs`](references/sub-skills/list-dataset-runs/SKILL.md) |
| Discover model definitions or pricing | [`discover-models`](references/sub-skills/discover-models/SKILL.md) |
| Discover trace filter options for evaluators | [`discover-filter-options`](references/sub-skills/discover-filter-options/SKILL.md) |
| Query aggregate analytics or the metrics API | [`query-metrics`](references/sub-skills/query-metrics/SKILL.md) |
| Create a dataset | [`create-dataset`](references/sub-skills/create-dataset/SKILL.md) |
| Design dataset input or expected output schemas | [`design-dataset-schema`](references/sub-skills/design-dataset-schema/SKILL.md) |
| Add, update, archive, delete, list, or bulk import dataset items | [`manage-dataset-items`](references/sub-skills/manage-dataset-items/SKILL.md) |
| Trigger an experiment or dataset run | [`trigger-experiment`](references/sub-skills/trigger-experiment/SKILL.md) |
| Configure remote experiment webhooks or payloads | [`configure-remote-experiment`](references/sub-skills/configure-remote-experiment/SKILL.md) |
| Analyze experiment results or inspect per-item scores | [`analyze-experiment-results`](references/sub-skills/analyze-experiment-results/SKILL.md) |
| Compare experiment runs or detect regressions | [`compare-experiments`](references/sub-skills/compare-experiments/SKILL.md) |
| Create an LLM-as-a-Judge evaluator | [`create-evaluator`](references/sub-skills/create-evaluator/SKILL.md) |
| List evaluator configurations | [`list-evaluators`](references/sub-skills/list-evaluators/SKILL.md) |
| Inspect evaluator prompts, versions, or job configs | [`inspect-evaluator`](references/sub-skills/inspect-evaluator/SKILL.md) |
| Update evaluator prompts, filters, mappings, model, or sampling | [`update-evaluator`](references/sub-skills/update-evaluator/SKILL.md) |
| Activate, deactivate, pause, resume, enable, or disable evaluators | [`toggle-evaluator-status`](references/sub-skills/toggle-evaluator-status/SKILL.md) |
| Delete or remove evaluators | [`delete-evaluator`](references/sub-skills/delete-evaluator/SKILL.md) |
| List dashboard widgets | [`list-widgets`](references/sub-skills/list-widgets/SKILL.md) |
| Suggest dashboard visualizations | [`suggest-widgets`](references/sub-skills/suggest-widgets/SKILL.md) |
| Create a dashboard widget | [`create-widget`](references/sub-skills/create-widget/SKILL.md) |
| Update a dashboard widget | [`update-widget`](references/sub-skills/update-widget/SKILL.md) |
| Delete a dashboard widget | [`delete-widget`](references/sub-skills/delete-widget/SKILL.md) |
| Create, update, delete, or arrange dashboards | [`manage-dashboard`](references/sub-skills/manage-dashboard/SKILL.md) |
| Calculate dashboard widget placement | [`layout-widgets`](references/sub-skills/layout-widgets/SKILL.md) |

## Common Chains

- For dashboard creation from a vague request, read `suggest-widgets`, then
  `create-widget`, `layout-widgets`, and `manage-dashboard` as needed.
- For evaluator setup, read `discover-traces`, `discover-filter-options`,
  `discover-models`, and `create-evaluator`.
- For experiment setup, read `discover-datasets`, `create-dataset`,
  `manage-dataset-items`, `configure-remote-experiment`, and
  `trigger-experiment` as needed.
- For experiment review, read `list-dataset-runs`,
  `analyze-experiment-results`, and `compare-experiments` as needed.
