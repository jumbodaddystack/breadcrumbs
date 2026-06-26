"""Tests for filename-canonical record identity (Phase 2, plan §7).

Run with:  python -m pytest tests/
       or:  python tests/test_identity.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402


class IdentityTests(unittest.TestCase):
    def test_decision_prefix(self):
        self.assertEqual(
            crumb.derive_identity("2026-06-25-repo-local-memory", "decision"),
            ("dec_20260625_repo-local-memory", "repo-local-memory"),
        )

    def test_all_type_prefixes(self):
        cases = {
            "decision": "dec",
            "attempt": "att",
            "idea": "idea",
            "session": "ses",
            "trap": "trap",
            "question": "q",
        }
        for rtype, prefix in cases.items():
            rid, slug = crumb.derive_identity("2026-01-02-thing", rtype)
            self.assertEqual(rid, f"{prefix}_20260102_thing")
            self.assertEqual(slug, "thing")

    def test_slug_keeps_internal_hyphens(self):
        rid, slug = crumb.derive_identity("2026-12-31-a-b-c", "attempt")
        self.assertEqual(slug, "a-b-c")
        self.assertEqual(rid, "att_20261231_a-b-c")

    def test_non_canonical_filename_returns_none(self):
        self.assertIsNone(crumb.derive_identity("not-a-dated-file", "decision"))
        self.assertIsNone(crumb.derive_identity("2026-6-5-bad-date", "decision"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
