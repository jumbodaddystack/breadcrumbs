"""Tests for `scan-secrets` and the audit secret sub-check (Phase 6, plan §15/§17.6).

Covers Fixture 6 (token-like string fails), the individual secret shapes, the
false-positive controls (git shas, record ids, the `?token=` query-string text that
must NOT trip), and the skip rules (private/index/generated are not scanned).

Run with:  python -m unittest discover -s tests
       or:  python tests/test_secrets.py
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402

FIXTURES = REPO_ROOT / "fixtures"


def run(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = crumb.main(argv)
    return code, buf.getvalue()


def fresh_store(tmp: str) -> Path:
    crumb.main(["init", "--project", tmp, "--session-tracking", "full"])
    return Path(tmp) / crumb.MEMORY_DIRNAME


def patterns_hit(mem: Path) -> set[str]:
    return {h["pattern"] for h in crumb.scan_secrets(mem)}


# --------------------------------------------------------------------------- #
# Fixture 6 — the canonical secret leak
# --------------------------------------------------------------------------- #
class Fixture6Tests(unittest.TestCase):
    def test_scan_secrets_command_fails_nonzero(self):
        code, out = run(["scan-secrets", "--project", str(FIXTURES / "fixture-06-secret-leak")])
        self.assertEqual(code, 1, out)
        self.assertIn("possible secret", out)

    def test_scan_secrets_points_at_offending_record_and_line(self):
        mem = FIXTURES / "fixture-06-secret-leak" / ".project-memory"
        hits = crumb.scan_secrets(mem)
        self.assertTrue(hits)
        for h in hits:
            self.assertTrue(h["path"].startswith("sessions/"))
            self.assertIsInstance(h["line"], int)
            self.assertGreater(h["line"], 0)

    def test_secret_value_is_not_echoed(self):
        """We report the pattern NAME + location, never the matched secret value."""
        _, out = run(
            ["scan-secrets", "--project", str(FIXTURES / "fixture-06-secret-leak"), "--json"]
        )
        payload = json.loads(out)
        blob = json.dumps(payload)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", blob)
        self.assertNotIn("hunter2hunter2", blob)

    def test_audit_treats_secret_as_blocking(self):
        code, out = run(
            ["audit", "--project", str(FIXTURES / "fixture-06-secret-leak"), "--json"]
        )
        self.assertEqual(code, 1, out)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertGreaterEqual(payload["failed"], 1)
        self.assertTrue(any(f["check"] == "secret" for f in payload["findings"]))


# --------------------------------------------------------------------------- #
# Each secret shape is detected
# --------------------------------------------------------------------------- #
class SecretShapeTests(unittest.TestCase):
    def _scan_line(self, line: str) -> set[str]:
        with tempfile.TemporaryDirectory() as tmp:
            mem = fresh_store(tmp)
            (mem / "decisions" / "2026-06-25-x.md").write_text(line + "\n", encoding="utf-8")
            return patterns_hit(mem)

    def test_aws_access_key_id(self):
        self.assertIn("aws-access-key-id", self._scan_line("key=AKIAIOSFODNN7EXAMPLE"))

    def test_github_token(self):
        self.assertIn(
            "github-token", self._scan_line("ghp_" + "a" * 36)
        )

    def test_pem_private_key(self):
        self.assertIn("pem-private-key", self._scan_line("-----BEGIN RSA PRIVATE KEY-----"))

    def test_bearer_token(self):
        self.assertIn("bearer-token", self._scan_line("Authorization: Bearer abcdef0123456789abcdef"))

    def test_assignment_pattern(self):
        self.assertIn("secret-assignment", self._scan_line("password=correcthorsebattery123"))

    def test_jwt(self):
        jwt = "eyJhbGciOiJIUzI1Ni.eyJzdWIiOiIxMjM0NTY3.SflKxwRJSMeKKF2QT4f"
        self.assertIn("jwt", self._scan_line(jwt))


# --------------------------------------------------------------------------- #
# False-positive controls — the scanner must stay quiet on normal memory
# --------------------------------------------------------------------------- #
class FalsePositiveTests(unittest.TestCase):
    def test_clean_fixtures_have_no_secrets(self):
        for name in (
            "fixture-01-fresh-resume",
            "fixture-02-guard-true-positive",
            "fixture-03-guard-false-positive",
            "fixture-04-stale-handoff",
            "fixture-05-superseded-decision",
        ):
            mem = FIXTURES / name / ".project-memory"
            self.assertEqual(crumb.scan_secrets(mem), [], name)

    def test_query_string_token_text_is_not_a_secret(self):
        """fixture-05's '?token= query parameter' prose must not trip the scanner."""
        mem = FIXTURES / "fixture-05-superseded-decision" / ".project-memory"
        self.assertEqual(crumb.scan_secrets(mem), [])

    def test_git_shas_and_record_ids_are_not_high_entropy_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = fresh_store(tmp)
            body = (
                "commit: 7c6b5a4 a1b2c3def0123456789\n"
                "id: dec_20260605_markdown-source-of-truth\n"
                "see att_20260512_sqlite-store-too-heavy for context\n"
            )
            (mem / "decisions" / "2026-06-25-y.md").write_text(body, encoding="utf-8")
            self.assertEqual(patterns_hit(mem), set())

    def test_high_entropy_token_is_caught(self):
        """A genuinely random mixed-class 40-char blob IS flagged."""
        token = "aB3xYz9QdE7Lm2Pq8Rt6Vw1Nc4Kf0Gh5Js7Tb2Zx"  # mixed upper/lower/digit
        with tempfile.TemporaryDirectory() as tmp:
            mem = fresh_store(tmp)
            (mem / "decisions" / "2026-06-25-z.md").write_text(token + "\n", encoding="utf-8")
            self.assertIn("high-entropy-string", patterns_hit(mem))


# --------------------------------------------------------------------------- #
# Skip rules — private/index/generated are not scanned
# --------------------------------------------------------------------------- #
class SkipRuleTests(unittest.TestCase):
    def test_private_and_index_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = fresh_store(tmp)
            (mem / "private").mkdir(exist_ok=True)
            (mem / "private" / "notes.md").write_text("key=AKIAIOSFODNN7EXAMPLE\n", encoding="utf-8")
            (mem / "index").mkdir(exist_ok=True)
            (mem / "index" / "dump.md").write_text("password=correcthorsebattery123\n", encoding="utf-8")
            self.assertEqual(crumb.scan_secrets(mem), [])


class CleanStoreTests(unittest.TestCase):
    def test_scan_secrets_ok_on_fresh_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh_store(tmp)
            code, out = run(["scan-secrets", "--project", tmp])
            self.assertEqual(code, 0, out)
            self.assertIn("OK", out)

    def test_missing_store_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run(["scan-secrets", "--project", tmp])
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
