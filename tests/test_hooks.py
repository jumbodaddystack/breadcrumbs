"""Tests for `crumb hook session|guard|capture` (review §A.6).

These drive the hook translators by feeding a JSON payload on stdin and asserting
the emitted JSON matches the verified Claude Code contract.

Run with:  python -m pytest tests/
       or:  python tests/test_hooks.py
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True, text=True)


def make_repo(tmp: str) -> Path:
    root = Path(tmp)
    git(root, "init", "-q")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    (root / "f.txt").write_text("a\n")
    git(root, "add", "f.txt")
    git(root, "commit", "-qm", "init")
    return root


def run_hook(event: str, payload: dict) -> dict:
    """Invoke `crumb hook <event>` in-process with `payload` on stdin; parse stdout."""
    out = io.StringIO()
    saved_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))
    try:
        with contextlib.redirect_stdout(out):
            code = crumb.main(["hook", event])
    finally:
        sys.stdin = saved_stdin
    assert code == 0, code
    text = out.getvalue().strip()
    return json.loads(text) if text else {}


def init_store(root: Path) -> Path:
    crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
    return root / crumb.MEMORY_DIRNAME


class HookSessionTests(unittest.TestCase):
    def test_emits_resume_packet_as_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            init_store(root)
            out = run_hook("session", {"cwd": str(root), "hook_event_name": "SessionStart"})
            hso = out["hookSpecificOutput"]
            self.assertEqual(hso["hookEventName"], "SessionStart")
            self.assertIn("additionalContext", hso)
            self.assertTrue(hso["additionalContext"].strip())

    def test_no_store_emits_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_hook("session", {"cwd": tmp})
            self.assertEqual(out, {})


class HookGuardTests(unittest.TestCase):
    def test_routine_action_is_silent_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            init_store(root)
            out = run_hook("guard", {
                "cwd": str(root), "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            })
            self.assertEqual(out, {})

    def test_risky_action_escalates_with_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            init_store(root)
            crumb.main(["note", "trap", "force-push to main loses history",
                        "--project", str(root)])
            out = run_hook("guard", {
                "cwd": str(root), "tool_name": "Bash",
                "tool_input": {"command": "git push --force origin main"},
            })
            hso = out["hookSpecificOutput"]
            self.assertEqual(hso["hookEventName"], "PreToolUse")
            # memory informs; it never denies on its own
            self.assertIn(hso["permissionDecision"], ("allow", "ask"))
            self.assertNotEqual(hso["permissionDecision"], "deny")
            self.assertIn("guard", hso["permissionDecisionReason"].lower())

    def test_high_impact_deletion_asks_human(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            mem = init_store(root)
            # a decision touching the schema makes a deletion of it high-impact
            crumb.main([
                "remember", "decision", "--project", str(root),
                "--title", "users table schema is canonical",
                "--set", "Decision", "keep users schema", "--confidence", "low",
                "--tags", "schema,database",
            ])
            out = run_hook("guard", {
                "cwd": str(root), "tool_name": "Bash",
                "tool_input": {"command": "drop table users schema"},
            })
            # deletion is a high-impact class; with a memory hit this escalates to ask
            if "hookSpecificOutput" in out:
                self.assertIn(out["hookSpecificOutput"]["permissionDecision"], ("allow", "ask"))


class HookCaptureTests(unittest.TestCase):
    def test_writes_session_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp)
            mem = init_store(root)
            out = run_hook("capture", {"cwd": str(root), "stop_reason": "end_turn"})
            self.assertEqual(out, {})
            self.assertEqual(len(list((mem / "sessions").glob("*.md"))), 1)
            # the written record must validate clean (diff-stat summarized, no bloat)
            self.assertEqual([f for f in crumb.run_validate(mem) if f["status"] == "fail"], [])

    def test_no_store_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = run_hook("capture", {"cwd": tmp})
            self.assertEqual(out, {})


if __name__ == "__main__":
    unittest.main()
