"""Launch an ephemeral classifier with no tools; only structured output is accepted."""

import json
import subprocess
import tempfile
from threading import Event, Timer
from pathlib import Path

from openai_codex import CodexConfig
from openai_codex.client import CodexClient
from openai_codex.errors import CodexError

REFERENCES = Path(__file__).resolve().parents[3] / "references"
TIMEOUT = 180
CODEX_CONFIG_OVERRIDES = (
    "mcp_servers={}", "notify=[]", 'web_search="disabled"',
    "tools.experimental_request_user_input.enabled=false", "tools.update_plan.enabled=false",
    "project_doc_max_bytes=0", "analytics.enabled=false", 'history.persistence="none"',
    "otel.log_user_prompt=false", 'otel.exporter="none"', 'otel.trace_exporter="none"',
    "features.shell_tool=false", "features.apps=false", "features.plugins=false",
    "features.multi_agent=false", "features.hooks=false", "features.browser_use=false",
    "features.computer_use=false", "features.image_generation=false",
    "features.workspace_dependencies=false", "features.code_mode=false",
    "features.code_mode_host=false", "features.skill_search=false", "features.memories=false",
    "features.goals=false", "features.sleep_tool=false", "features.tool_suggest=false",
    "features.view_image=false", "features.shell_snapshot=false",
)


def codex_read(payload, rules, schema, directory):
    def reject_request(method, _params):
        raise RuntimeError(f"Reader requested an unauthorized action: {method}")

    client = CodexClient(
        CodexConfig(cwd=directory, config_overrides=CODEX_CONFIG_OVERRIDES),
        approval_handler=reject_request,
    )
    timed_out = Event()
    timer = Timer(TIMEOUT, lambda: (timed_out.set(), client.close()))
    try:
        timer.start()
        client.start()
        client.initialize()
        thread = client.thread_start({
            "ephemeral": True, "environments": [], "dynamicTools": [],
            "approvalPolicy": "never", "sandbox": "read-only",
            "baseInstructions": rules, "developerInstructions": "",
        })
        if thread.approval_policy.root.value != "never" or thread.sandbox.root.type != "readOnly":
            raise RuntimeError("Reader isolation was not applied")
        turn = client.turn_start(thread.thread.id, [{"type": "text", "text": json.dumps(payload)}], {
            "environments": [], "dynamicTools": [], "outputSchema": schema,
        })
        output = None
        while True:
            notification = client.next_turn_notification(turn.turn.id)
            if notification.method == "item/completed":
                item = notification.payload.item.root
                if item.type == "agentMessage":
                    output = item.text
                elif item.type not in {"userMessage", "reasoning"}:
                    raise RuntimeError("Reader attempted an unauthorized action")
            if notification.method == "turn/completed":
                if notification.payload.turn.status.value != "completed" or output is None:
                    raise RuntimeError("Reader assessment failed")
                return json.loads(output)
    except CodexError:
        if timed_out.is_set():
            raise RuntimeError("Reader timed out") from None
        raise RuntimeError("Reader assessment failed") from None
    except Exception:
        if timed_out.is_set():
            raise RuntimeError("Reader timed out") from None
        raise
    finally:
        timer.cancel()
        client.close()


def read(payload, runtime):
    rules = (REFERENCES / "hiring-email-rules.md").read_text()
    schema = json.loads((REFERENCES / "hiring-email-result.schema.json").read_text())
    with tempfile.TemporaryDirectory(prefix="hiring-email-reader-") as directory:
        if runtime == "codex":
            return codex_read(payload, rules, schema, directory)
        if runtime != "claude":
            raise ValueError("Unsupported reader runtime")
        command = [
            "claude", "--print", "--safe-mode", "--tools", "", "--strict-mcp-config",
            "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence",
            "--disable-slash-commands", "--setting-sources", "", "--no-chrome",
            "--permission-mode", "dontAsk", "--system-prompt", rules,
            "--output-format", "json", "--json-schema", json.dumps(schema),
        ]
        try:
            result = subprocess.run(command, input=json.dumps(payload), cwd=directory,
                                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                    text=True, timeout=TIMEOUT, check=True)
        except (subprocess.SubprocessError, OSError):
            raise RuntimeError("Reader assessment failed") from None
        response = json.loads(result.stdout)
        if response.get("is_error") or not isinstance(response.get("structured_output"), dict):
            raise RuntimeError("Reader returned no structured assessment")
        return response["structured_output"]
