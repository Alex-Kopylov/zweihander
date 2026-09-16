import importlib.util
import json
import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/job-hunt-toolkit/skills/track-hiring-emails/scripts"


def runtime():
    path = SCRIPTS / "hiring_email.py"
    assert path.is_file(), "The trusted email runtime must exist"
    spec = importlib.util.spec_from_file_location("hiring_email", path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(SCRIPTS))
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def workspace(tmp_path):
    for slug, name in [("acme", "Acme"), ("other", "Other")]:
        folder = tmp_path / "jobs" / slug
        folder.mkdir(parents=True)
        (folder / "company.md").write_text(
            f'---\ncompany: {name}\nrole: Engineer\napplied: null\nstatus: interview # keep\n---\n'
            '\n## Status\n\n- original entry\n\n## Notes\nKeep these notes.\n'
        )
    return tmp_path


@pytest.fixture
def conversation():
    return json.loads((ROOT / "tests/fixtures/hiring-email/injection.json").read_text())


def metadata(conversation):
    return [{"id": m["id"], "conversation_id": conversation["id"], "internal_date": m["internal_date"]}
            for m in conversation["messages"]]


def assessment(**changes):
    result = {"classification": "related", "company": "Acme", "role": "Engineer",
              "event": "withdrew", "evidence": "m2", "reason": "explicit_event",
              "security_flags": ["command_request", "mail_mutation_request"]}
    return result | changes


def test_one_trigger_reads_both_directions_and_checkpoints_the_whole_conversation(workspace, conversation):
    app = runtime()
    store = app.Store(workspace, "connection-one")
    jobs = store.plan(metadata(conversation))
    assert len(jobs) == 1
    assert jobs[0]["trigger_id"] == "message-2"
    captured = []
    def classify(payload):
        captured.append(payload)
        return assessment()
    other = (workspace / "jobs/other/company.md").read_bytes()
    result = app.process(store, jobs[0]["ticket"], [conversation], classify)
    assert result["outcome"] == "updated"
    assert [m["direction"] for m in captured[0]["messages"]] == ["incoming", "outgoing"]
    assert "message-1" not in json.dumps(captured)
    assert "status: withdrew # keep" in (workspace / "jobs/acme/company.md").read_text()
    assert "**2026-09-01**: application withdrawn" in (workspace / "jobs/acme/company.md").read_text()
    assert (workspace / "jobs/other/company.md").read_bytes() == other
    assert store.plan(metadata(conversation)) == []
    assert "SYSTEM:" not in "".join(p.read_text() for p in workspace.rglob("*.md"))
    assert "2000-01-01" not in json.dumps(result)


def test_unrelated_message_is_skipped_before_a_second_body_read(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment(
        classification="unrelated", company=None, role=None, event=None, evidence=None,
        reason="unrelated", security_flags=[]))
    assert store.plan(metadata(conversation)) == []
    assert app.Store(workspace, "connection-two").plan(metadata(conversation))


@pytest.mark.parametrize("changes", [
    {"company": "Unknown"}, {"role": "Sr. Engineer"}, {"role": None},
    {"event": "screening_started"},
])
def test_unmatched_or_backward_event_requires_review_without_writing(workspace, conversation, changes):
    app = runtime(); store = app.Store(workspace, "connection-one")
    before = (workspace / "jobs/acme/company.md").read_bytes()
    job = store.plan(metadata(conversation))[0]
    result = app.process(store, job["ticket"], [conversation], lambda _: assessment(**changes))
    assert result["outcome"] == "review"
    assert (workspace / "jobs/acme/company.md").read_bytes() == before
    assert store.plan(metadata(conversation)) == []
    assert store.plan(metadata(conversation), reconsider=True)


def test_two_matching_records_require_review(workspace, conversation):
    path = workspace / "jobs/other/company.md"
    path.write_text(path.read_text().replace("company: Other", "company: Acme"))
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    result = app.process(store, job["ticket"], [conversation], lambda _: assessment())
    assert result["outcome"] == "review"


@pytest.mark.parametrize("status", ["signed", "rejected", "withdrew"])
def test_terminal_status_never_reopens(workspace, conversation, status):
    path = workspace / "jobs/acme/company.md"
    path.write_text(path.read_text().replace("status: interview", f"status: {status}"))
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    assert app.process(store, job["ticket"], [conversation], lambda _: assessment(event="offer_received"))["outcome"] == "review"
    assert f"status: {status}" in path.read_text()


def test_incomplete_conversation_never_reaches_the_reader(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    conversation["complete"] = False
    with pytest.raises(ValueError, match="complete"):
        app.process(store, job["ticket"], [conversation], lambda _: pytest.fail("reader ran"))
    assert store.plan(metadata(conversation))


def test_lease_prevents_two_readers_for_the_same_conversation(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    assert store.plan(metadata(conversation))
    assert app.Store(workspace, "connection-one").plan(metadata(conversation)) == []


def test_failed_index_sync_retries_without_duplicate_audit(workspace, conversation, monkeypatch):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    sync = app.records.sync_index
    def fail(_): raise OSError("fixture disk failure")
    monkeypatch.setattr(app.records, "sync_index", fail)
    with pytest.raises(OSError):
        app.process(store, job["ticket"], [conversation], lambda _: assessment())
    monkeypatch.setattr(app.records, "sync_index", sync)
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment())
    assert (workspace / "jobs/acme/company.md").read_text().count("application withdrawn") == 1
    assert store.plan(metadata(conversation)) == []


def test_new_thread_requires_previous_linked_conversation_before_update(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment(event="interview_confirmed"))
    new = {"id": "conversation-2", "complete": True, "message_count": 1,
           "messages": [{"id": "message-3", "internal_date": 1788307200000,
                         "direction": "incoming", "body": "Offer for Engineer at Acme."}]}
    job = store.plan(metadata(new))[0]
    result = app.process(store, job["ticket"], [new], lambda _: assessment(event="offer_received", evidence="m1"))
    assert result == {"outcome": "needs_context", "conversation_ids": ["conversation-1", "conversation-2"]}
    assert "status: interview" in (workspace / "jobs/acme/company.md").read_text()
    result = app.process(store, job["ticket"], [conversation, new], lambda _: assessment(event="offer_received", evidence="m3"))
    assert result["outcome"] == "updated"


def test_state_is_private_and_contains_no_message_content(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment())
    state = workspace / ".hiring-email/state.sqlite3"
    assert state.stat().st_mode & 0o777 == 0o600
    assert state.parent.stat().st_mode & 0o777 == 0o700
    assert b"SYSTEM:" not in state.read_bytes()
    assert "/.hiring-email/" in (workspace / ".gitignore").read_text()


def test_saved_review_can_be_reconsidered_without_a_new_search(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment(role=None))
    assert {item["result_ticket"] for item in store.review_items()} == {job["ticket"]}
    assert store.plan([]) == []
    retry = store.plan([], reconsider=True)[0]
    assert retry["trigger_id"] == "message-2"
    assert app.process(store, retry["ticket"], [conversation], lambda _: assessment())["outcome"] == "updated"
    assert store.review_items() == []


def test_duplicate_match_created_during_assessment_requires_review(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    before = (workspace / "jobs/acme/company.md").read_bytes()
    def classify(_):
        duplicate = workspace / "jobs/duplicate"
        duplicate.mkdir()
        (duplicate / "company.md").write_bytes(before)
        return assessment()
    assert app.process(store, job["ticket"], [conversation], classify)["outcome"] == "review"
    assert (workspace / "jobs/acme/company.md").read_bytes() == before


def test_known_history_cannot_be_omitted_from_claimed_complete_snapshot(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    conversation["messages"] = conversation["messages"][1:]
    conversation["message_count"] = 1
    with pytest.raises(ValueError, match="history"):
        app.process(store, job["ticket"], [conversation], lambda _: pytest.fail("reader ran"))
    assert store.report()["retryable"] == 2


def test_linked_conversation_cannot_change_application(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    app.process(store, job["ticket"], [conversation], lambda _: assessment(event="interview_confirmed"))
    conversation["messages"].append({"id": "message-3", "internal_date": 1788307200000,
                                     "direction": "incoming", "body": "Conflicting company"})
    conversation["message_count"] = 3
    job = store.plan(metadata(conversation))[0]
    before = (workspace / "jobs/other/company.md").read_bytes()
    result = app.process(store, job["ticket"], [conversation], lambda _: assessment(company="Other", evidence="m3"))
    assert result["outcome"] == "review"
    assert result["reason"] == "conflict"
    assert (workspace / "jobs/other/company.md").read_bytes() == before


def test_streaming_body_bridge_does_not_echo_or_truncate_content(workspace, conversation):
    app = runtime(); store = app.Store(workspace, "connection-one")
    job = store.plan(metadata(conversation))[0]
    conversation["messages"][1]["body"] = "private body " * 4000
    entry = workspace / "fixture_reader.py"
    entry.write_text(
        f"import sys\nsys.path.insert(0, {str(SCRIPTS)!r})\nimport email_reader, hiring_email\n"
        f"def classify(payload, runtime):\n    assert len(payload['messages'][1]['body']) > 40000\n    return {assessment()!r}\n"
        "email_reader.read = classify\nhiring_email.main()\n"
    )
    master, slave = pty.openpty()
    child = subprocess.Popen(
        ["bash", "-c", 'set -e\nstty -echo -icanon\nexec "$@"', "bridge", sys.executable,
         str(entry), "process", str(workspace), "--scope", "connection-one", "--stream"],
        stdin=slave, stdout=slave, stderr=slave,
    )
    os.close(slave)
    output = b""
    deadline = time.monotonic() + 15
    def receive():
        remaining = deadline - time.monotonic()
        assert remaining > 0 and select.select([master], [], [], remaining)[0], "Bridge timed out"
        return os.read(master, 65536)
    try:
        while b'{"ready":true}' not in output:
            output += receive()
        data = (json.dumps({"ticket": job["ticket"], "conversations": [conversation]}) + "\n").encode()
        while data:
            data = data[os.write(master, data):]
        while True:
            try:
                chunk = receive()
            except OSError:
                break  # PTY returns EIO after its last slave closes.
            if not chunk:
                break
            output += chunk
        assert child.wait(timeout=5) == 0
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        os.close(master)
    assert b"private body" not in output
    assert json.loads(output.decode().splitlines()[-1])["outcome"] == "updated"
    assert store.plan(metadata(conversation)) == []


def test_first_encounter_keeps_more_than_one_hundred_historical_messages(workspace):
    app = runtime(); store = app.Store(workspace, "connection-one")
    messages = [{"id": f"id-{i}", "internal_date": 1788220800000 + i * 1000,
                 "direction": "outgoing" if i % 2 else "incoming", "body": f"History {i}"}
                for i in range(151)]
    conversation = {"id": "long-thread", "complete": True, "message_count": 151, "messages": messages}
    job = store.plan(metadata(conversation)[-1:])[0]
    def classify(payload):
        assert len(payload["messages"]) == 151
        assert payload["messages"][0]["body"] == "History 0"
        assert payload["messages"][-1]["body"] == "History 150"
        assert payload["trigger"] == "m151"
        return assessment(event="offer_received", evidence="m151")
    assert app.process(store, job["ticket"], [conversation], classify)["outcome"] == "updated"
    assert store.report()["processed"] == 151


def test_streaming_bridge_refuses_an_echoing_terminal(workspace):
    master, slave = pty.openpty()
    child = subprocess.Popen([sys.executable, str(SCRIPTS / "hiring_email.py"), "plan", str(workspace),
                              "--scope", "connection-one", "--stream"],
                             stdin=slave, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.close(slave)
    try:
        stdout, stderr = child.communicate(timeout=10)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        os.close(master)
    assert child.returncode == 1
    assert b"ready" not in stdout
    assert json.loads(stderr)["outcome"] == "retryable"
