# /// script
# requires-python = ">=3.11"
# dependencies = ["openai-codex==0.154.0", "PyYAML>=6.0.3,<7"]
# ///
"""Trusted metadata queue and application writer; mail never becomes executable input."""

import argparse
import json
import os
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "init-workspace/scripts"))
import application_records as records

REASONS = {"explicit_event", "unrelated", "ambiguous", "unmatched", "conflict"}
SECURITY_FLAGS = {"command_request", "mail_mutation_request", "authority_claim", "data_exfiltration_request"}


def identifier(value):
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ValueError("Invalid routing identifier")
    return value


def timestamp(value):
    if type(value) is not int or value < 0:
        raise ValueError("Invalid provider timestamp")
    datetime.fromtimestamp(value / 1000, timezone.utc)
    return value


class Store:
    def __init__(self, workspace, scope):
        self.workspace = Path(workspace).resolve(strict=True)
        self.scope = identifier(scope)
        self.directory = self.workspace / ".hiring-email"
        if self.directory.is_symlink():
            raise ValueError("Symlink state directory is not allowed")
        self.directory.mkdir(mode=0o700, exist_ok=True)
        self.directory.chmod(0o700)
        ignore = self.workspace / ".gitignore"
        if ignore.is_symlink():
            raise ValueError("Symlink ignore file is not allowed")
        content = ignore.read_bytes() if ignore.exists() else b""
        if b"/.hiring-email/" not in content.splitlines():
            records.atomic_write(ignore, content + (b"\n" if content and not content.endswith(b"\n") else b"") + b"/.hiring-email/\n")
        path = self.directory / "state.sqlite3"
        if path.is_symlink():
            raise ValueError("Symlink state file is not allowed")
        fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        os.fchmod(fd, 0o600)
        os.close(fd)
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS messages (
                scope TEXT, id TEXT, conversation TEXT, received INTEGER,
                outcome TEXT, first_seen REAL, result_ticket TEXT, PRIMARY KEY(scope, id));
            CREATE TABLE IF NOT EXISTS links (
                scope TEXT, conversation TEXT, company TEXT, PRIMARY KEY(scope, conversation));
            CREATE TABLE IF NOT EXISTS claims (
                scope TEXT, conversation TEXT, ticket TEXT UNIQUE, expires REAL, data TEXT,
                PRIMARY KEY(scope, conversation));
        ''')

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK")
            raise

    def plan(self, metadata, reconsider=False):
        """Reserve one trigger per changed conversation without reading message bodies."""
        messages = {}
        for item in metadata:
            message = {"id": identifier(item["id"]), "conversation_id": identifier(item["conversation_id"]),
                       "internal_date": timestamp(item["internal_date"])}
            previous = messages.get(message["id"])
            if previous is not None and previous != message:
                raise ValueError("Conflicting message metadata")
            messages[message["id"]] = message
        jobs = []
        with self.transaction():
            self.db.execute("DELETE FROM claims WHERE expires < ?", (time.time(),))
            for pending in self.db.execute("SELECT * FROM messages WHERE scope=? AND (outcome='pending' OR (? AND outcome='review'))", (self.scope, reconsider)):
                messages.setdefault(pending["id"], {"id": pending["id"], "conversation_id": pending["conversation"], "internal_date": pending["received"]})
            groups = {}
            for message in messages.values():
                row = self.db.execute("SELECT outcome FROM messages WHERE scope=? AND id=?", (self.scope, message["id"])).fetchone()
                if row and row["outcome"] != "pending" and not (reconsider and row["outcome"] == "review"):
                    continue
                groups.setdefault(message["conversation_id"], []).append(message)
            for conversation, group in sorted(groups.items(), key=lambda pair: min(m["internal_date"] for m in pair[1])):
                if self.db.execute("SELECT 1 FROM claims WHERE scope=? AND conversation=?", (self.scope, conversation)).fetchone():
                    continue
                trigger = max(group, key=lambda m: (m["internal_date"], m["id"]))
                related = {conversation}
                link = self.db.execute("SELECT company FROM links WHERE scope=? AND conversation=?", (self.scope, conversation)).fetchone()
                if link:
                    related.update(row[0] for row in self.db.execute("SELECT conversation FROM links WHERE scope=? AND company=?", (self.scope, link[0])))
                ticket = uuid.uuid4().hex
                job = {"ticket": ticket, "trigger_id": trigger["id"], "trigger_date": trigger["internal_date"],
                       "conversation_ids": sorted(related)}
                self.db.execute("INSERT INTO claims VALUES(?,?,?,?,?)", (self.scope, conversation, ticket, time.time() + 900, json.dumps(job)))
                for message in group:
                    self.db.execute("INSERT INTO messages VALUES(?,?,?,?,?,?,NULL) ON CONFLICT(scope,id) DO UPDATE SET outcome='pending'",
                                    (self.scope, message["id"], conversation, message["internal_date"], "pending", time.time()))
                jobs.append(job)
        return jobs

    def claim(self, ticket):
        row = self.db.execute("SELECT * FROM claims WHERE scope=? AND ticket=? AND expires>=?", (self.scope, ticket, time.time())).fetchone()
        if row is None:
            raise ValueError("Missing or expired reader assignment")
        return row

    def report(self):
        counts = {row[0]: row[1] for row in self.db.execute("SELECT outcome,count(*) FROM messages WHERE scope=? GROUP BY outcome", (self.scope,))}
        first = self.db.execute("SELECT min(first_seen) FROM messages WHERE scope=? AND outcome='review'", (self.scope,)).fetchone()[0]
        return {"processed": counts.get("processed", 0), "review_required": counts.get("review", 0),
                "retryable": counts.get("pending", 0), "oldest_review_days": int((time.time() - first) / 86400) if first else 0}

    def review_items(self):
        return [dict(row) for row in self.db.execute("""SELECT id,conversation AS conversation_id,
                    received AS internal_date,result_ticket FROM messages WHERE scope=? AND outcome='review'
                    ORDER BY received,id""", (self.scope,))]


def reader_payload(job, conversations, applications):
    if not isinstance(conversations, list) or len(conversations) != len(job["conversation_ids"]) or {c["id"] for c in conversations} != set(job["conversation_ids"]):
        raise ValueError("The assignment requires complete linked conversations")
    items = []
    seen = set()
    for conversation in conversations:
        if conversation.get("complete") is not True or type(conversation.get("message_count")) is not int or conversation["message_count"] != len(conversation["messages"]):
            raise ValueError("A complete conversation is required")
        for message in conversation["messages"]:
            key = identifier(message["id"])
            if key in seen or message.get("direction") not in {"incoming", "outgoing"} or not isinstance(message.get("body"), str):
                raise ValueError("Invalid conversation message")
            seen.add(key)
            items.append({**message, "internal_date": timestamp(message["internal_date"]), "conversation_id": conversation["id"]})
    items.sort(key=lambda m: (m["internal_date"], m["id"]))
    trigger = next((m for m in items if m["id"] == job["trigger_id"]), None)
    if trigger is None or trigger["internal_date"] != job["trigger_date"]:
        raise ValueError("The assigned trigger is missing or changed")
    handles = {f"m{i+1}": message for i, message in enumerate(items)}
    conversation_handles = {key: f"c{i+1}" for i, key in enumerate(sorted(job["conversation_ids"]))}
    return {
        "trigger": next(key for key, message in handles.items() if message["id"] == job["trigger_id"]),
        "messages": [{"handle": key, "conversation": conversation_handles[message["conversation_id"]],
                      "received_at": datetime.fromtimestamp(message["internal_date"] / 1000, timezone.utc).isoformat(),
                      "direction": message["direction"], "body": message["body"],
                      "headers": message.get("headers", {})} for key, message in handles.items()],
        "applications": [{key: record[key] for key in ("company", "role", "status")} for record in applications],
    }, handles


def validate_result(result, handles):
    if not isinstance(result, dict) or set(result) != {"classification", "company", "role", "event", "evidence", "reason", "security_flags"}:
        raise ValueError("Invalid reader result fields")
    if result["classification"] not in {"related", "unrelated", "review"} or result["reason"] not in REASONS:
        raise ValueError("Invalid reader outcome")
    if any(value is not None and not isinstance(value, str) for value in (result["company"], result["role"])):
        raise ValueError("Invalid match fields")
    if result["event"] is not None and result["event"] not in records.EVENTS:
        raise ValueError("Invalid lifecycle event")
    if result["evidence"] is not None and result["evidence"] not in handles:
        raise ValueError("Evidence is outside the assignment")
    if not isinstance(result["security_flags"], list) or any(flag not in SECURITY_FLAGS for flag in result["security_flags"]):
        raise ValueError("Invalid security finding")


def process(store, ticket, conversations, classify):
    try:
        claim = store.claim(ticket)
        job = json.loads(claim["data"])
        applications = records.load_records(store.workspace)
        payload, handles = reader_payload(job, conversations, applications)
        supplied = {message["id"]: message for message in handles.values()}
        for conversation in job["conversation_ids"]:
            for known in store.db.execute("SELECT * FROM messages WHERE scope=? AND conversation=?", (store.scope, conversation)):
                message = supplied.get(known["id"])
                if not message or message["internal_date"] != known["received"] or message["conversation_id"] != known["conversation"]:
                    raise ValueError("Known conversation history is missing or changed")
        result = classify(payload)
        validate_result(result, handles)
        with store.transaction():
            store.claim(ticket)
            match = records.match_record(records.load_records(store.workspace), result["company"], result["role"])
            linked = {row[0] for conversation in job["conversation_ids"] for row in
                      store.db.execute("SELECT company FROM links WHERE scope=? AND conversation=?", (store.scope, conversation))}
            conflict = bool(linked) and (not match or linked != {match["path"].parent.name})
            if conflict:
                result = {**result, "classification": "review", "reason": "conflict"}
                match = None
            if match and result["classification"] != "unrelated":
                known = {row[0] for row in store.db.execute("SELECT conversation FROM links WHERE scope=? AND company=?", (store.scope, match["path"].parent.name))}
                required = known | set(job["conversation_ids"])
                if required != set(job["conversation_ids"]):
                    job["conversation_ids"] = sorted(required)
                    store.db.execute("UPDATE claims SET data=? WHERE ticket=?", (json.dumps(job), ticket))
                    return {"outcome": "needs_context", "conversation_ids": job["conversation_ids"]}
            outcome = "review"
            if result["classification"] == "unrelated":
                outcome = "unrelated"
            elif result["classification"] == "related" and match and result["event"] and result["evidence"]:
                evidence = handles[result["evidence"]]
                event_date = datetime.fromtimestamp(evidence["internal_date"] / 1000, timezone.utc).date().isoformat()
                outcome = records.transition(match, result["event"], event_date)
                if outcome == "review":
                    result["reason"] = "conflict"
            elif result["classification"] == "related" and not match:
                result["reason"] = "unmatched"
            if outcome in {"updated", "unchanged"}:
                records.sync_index(store.workspace)
            safe = {"outcome": outcome, "company": match["path"].parent.name if match else None,
                    "proposed_status": records.EVENTS[result["event"]][0] if result["event"] else None,
                    "reason": result["reason"], "security_flags": sorted(set(result["security_flags"]))}
            destination = store.directory / "results"
            if destination.is_symlink():
                raise ValueError("Symlink result directory is not allowed")
            destination.mkdir(mode=0o700, exist_ok=True)
            destination.chmod(0o700)
            records.atomic_write(destination / f"{ticket}.json", json.dumps(safe).encode())
            for message in handles.values():
                store.db.execute("""INSERT INTO messages VALUES(?,?,?,?,?,?,?) ON CONFLICT(scope,id) DO UPDATE SET
                                 outcome=CASE WHEN messages.outcome='processed' AND excluded.outcome='review'
                                 THEN 'processed' ELSE excluded.outcome END, result_ticket=excluded.result_ticket""",
                                 (store.scope, message["id"], message["conversation_id"], message["internal_date"], "review" if outcome == "review" else "processed", time.time(), ticket))
            if match and result["classification"] != "unrelated":
                for conversation in job["conversation_ids"]:
                    store.db.execute("INSERT INTO links VALUES(?,?,?) ON CONFLICT(scope,conversation) DO UPDATE SET company=excluded.company",
                                     (store.scope, conversation, match["path"].parent.name))
            store.db.execute("DELETE FROM claims WHERE scope=? AND ticket=?", (store.scope, ticket))
            return safe
    except BaseException:
        store.db.execute("DELETE FROM claims WHERE scope=? AND ticket=?", (store.scope, ticket))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "process", "report", "review-items", "start-date"])
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--scope", required=True, help="Stable connection and authorized search scope identifier")
    parser.add_argument("--reconsider", action="store_true")
    parser.add_argument("--stream", action="store_true", help="Read one JSON line; emit readiness before stdin")
    parser.add_argument("--runtime", choices=["codex", "claude"], default="codex")
    args = parser.parse_args()
    store = Store(args.workspace, args.scope)
    def request():
        if args.stream:
            if sys.stdin.isatty():
                import termios
                if termios.tcgetattr(sys.stdin.fileno())[3] & (termios.ECHO | termios.ICANON):
                    raise RuntimeError("The body bridge requires echo and canonical buffering disabled")
            print('{"ready":true}', flush=True)
            return json.loads(sys.stdin.readline())
        return json.load(sys.stdin)
    if args.command == "plan":
        result = store.plan(request(), args.reconsider)
    elif args.command == "process":
        from email_reader import read
        assignment = request()
        result = process(store, assignment["ticket"], assignment["conversations"], lambda payload: read(payload, args.runtime))
    elif args.command == "start-date":
        applied = [record["applied"] for record in records.load_records(args.workspace) if record["applied"]]
        result = {"start_date": (min(applied) if applied else (datetime.now(timezone.utc) - timedelta(days=30)).date()).isoformat()}
    elif args.command == "review-items":
        result = store.review_items()
    else:
        result = store.report()
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error, RuntimeError):
        print('{"outcome":"retryable","stage":"email_tracking"}', file=sys.stderr)
        raise SystemExit(1)
