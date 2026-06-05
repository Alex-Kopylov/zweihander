# Codex Harness Notes

When adapting follow-up delegation to Codex, treat named Langfuse agents as subagent capabilities. Use `spawn_agent` only when the current Codex harness exposes or permits it; otherwise, present `langfuse-dataset-expert` or `langfuse-experiment-manager` as follow-up capabilities for the user to invoke.
