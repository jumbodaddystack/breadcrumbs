"""Tests for `crumb remember decision|attempt` (Phase 3).

Run with:  python -m pytest tests/
       or:  python tests/test_remember.py
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402


def init_store(tmp: str) -> Path:
    root = Path(tmp)
    crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
    return root / crumb.MEMORY_DIRNAME


def run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = crumb.main(argv)
    return code, buf.getvalue()


class RememberDecisionTests(unittest.TestCase):
    def test_decision_creates_valid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(
                [
                    "remember", "decision", "--project", tmp,
                    "--title", "Use repo-local Markdown as source of truth",
                    "--set", "Context", "needed durable memory",
                    "--set", "Decision", "use markdown with frontmatter",
                    "--evidence", "commit", "abc1234",
                    "--tags", "memory,architecture",
                ]
            )
            self.assertEqual(code, 0)
            files = list((mem / "decisions").glob("*.md"))
            self.assertEqual(len(files), 1)
            # the new record validates clean
            findings = crumb.run_validate(mem)
            self.assertEqual([f for f in findings if f["status"] == "fail"], [])

    def test_filename_id_agreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            run(
                [
                    "remember", "decision", "--project", tmp,
                    "--title", "Adopt a monorepo", "--evidence", "pr", "#42",
                ]
            )
            path = next((mem / "decisions").glob("*.md"))
            meta, _ = crumb.parse_frontmatter(path.read_text())
            rid, slug = crumb.derive_identity(path.stem, "decision")
            self.assertEqual(meta["id"], rid)
            self.assertEqual(meta["slug"], slug)
            self.assertEqual(meta["type"], "decision")
            # quoted #-ref round-trips
            self.assertEqual(meta["evidence"], [{"type": "pr", "ref": "#42"}])

    def test_same_day_slug_dedupe(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            for _ in range(2):
                run(["remember", "decision", "--project", tmp, "--title", "Same Title", "--confidence", "low"])
            names = {p.name for p in (mem / "decisions").glob("*.md")}
            self.assertEqual(len(names), 2)
            self.assertTrue(any(n.endswith("same-title.md") for n in names))
            self.assertTrue(any(n.endswith("same-title-2.md") for n in names))

    def test_json_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            init_store(tmp)
            code, out = run(
                ["remember", "decision", "--project", tmp, "--title", "X", "--confidence", "low", "--json"]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["type"], "decision")
            self.assertTrue(payload["id"].startswith("dec_"))


class RememberAttemptTests(unittest.TestCase):
    def test_attempt_creates_valid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(
                [
                    "remember", "attempt", "--project", tmp,
                    "--title", "Tried a sqlite store",
                    "--set", "Problem", "needed a store",
                    "--set", "Result", "too heavy",
                    "--confidence", "low",
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(len(list((mem / "attempts").glob("*.md"))), 1)
            self.assertEqual([f for f in crumb.run_validate(mem) if f["status"] == "fail"], [])

    def test_named_attempt_flags_fill_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(
                [
                    "remember", "attempt", "--project", tmp,
                    "--title", "gradle daemon stop breaks build",
                    "--problem", "build hung",
                    "--tried", "./gradlew --stop",
                    "--result", "R.jar lock error",
                    "--why", "daemon held a lock",
                    "--do-not-retry", "unless lockfile cleared",
                    "--evidence", "commit", "abc1234",
                ]
            )
            self.assertEqual(code, 0)
            path = next((mem / "attempts").glob("*.md"))
            _, body = crumb.parse_frontmatter(path.read_text())
            rec = crumb.Record(path, "attempt", {}, body)
            self.assertEqual(rec.sections["Problem"], "build hung")
            self.assertEqual(rec.sections["Tried"], "./gradlew --stop")
            self.assertEqual(rec.sections["Why It Failed / Succeeded"], "daemon held a lock")
            self.assertEqual(rec.sections["Do Not Retry Unless"], "unless lockfile cleared")
            self.assertEqual([f for f in crumb.run_validate(mem) if f["status"] == "fail"], [])

    def test_named_flag_overrides_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            run(
                [
                    "remember", "attempt", "--project", tmp,
                    "--title", "override check",
                    "--set", "Problem", "from set",
                    "--problem", "from flag",
                    "--confidence", "low",
                ]
            )
            path = next((mem / "attempts").glob("*.md"))
            _, body = crumb.parse_frontmatter(path.read_text())
            rec = crumb.Record(path, "attempt", {}, body)
            self.assertEqual(rec.sections["Problem"], "from flag")


class EvidenceEnforcementTests(unittest.TestCase):
    def test_no_evidence_no_low_confidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(["remember", "decision", "--project", tmp, "--title", "No evidence here"])
            self.assertEqual(code, 2)
            # nothing written
            self.assertEqual(list((mem / "decisions").glob("*.md")), [])

    def test_low_confidence_allows_no_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(
                ["remember", "decision", "--project", tmp, "--title", "Low conf ok", "--confidence", "low"]
            )
            self.assertEqual(code, 0)
            self.assertEqual(len(list((mem / "decisions").glob("*.md"))), 1)

    def test_evidence_allows_default_confidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = init_store(tmp)
            code, _ = run(
                ["remember", "attempt", "--project", tmp, "--title", "Has evidence",
                 "--evidence", "command", "npm test"]
            )
            self.assertEqual(code, 0)
            path = next((mem / "attempts").glob("*.md"))
            meta, _ = crumb.parse_frontmatter(path.read_text())
            self.assertEqual(meta["confidence"], "medium")


class RememberMisuseTests(unittest.TestCase):
    def test_unknown_section_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            init_store(tmp)
            code, _ = run(
                ["remember", "decision", "--project", tmp, "--title", "X", "--confidence", "low",
                 "--set", "Nonsense", "value"]
            )
            self.assertEqual(code, 2)

    def test_no_store_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run(["remember", "decision", "--project", tmp, "--title", "X", "--confidence", "low"])
            self.assertEqual(code, 2)

    def test_bare_remember_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            init_store(tmp)
            code = crumb.main(["remember", "--project", tmp])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
