# Codex Harness Adaptation

Load this file only when the active harness is Codex and the workflow needs harness-specific evaluator delegation.

For follow-up LLM-as-Judge evaluator setup, use Codex subagent delegation such as `spawn_agent` for an equivalent `langfuse-eval-manager` context when available. If subagent delegation is not available in the active tool list or through discovery, keep the evaluator setup guidance in the current context.
