"""Regression tests for bugs found in the 2026-06-26 full-codebase review.

Each test is named test_<bugid>_... and reproduces a concrete defect that was
confirmed against the code before the fix. Run with:  python -m pytest tests/
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402


# --------------------------------------------------------------------------- #
# Group 1 — frontmatter parser / record IO robustness
# --------------------------------------------------------------------------- #
class ParserIORobustnessTests(unittest.TestCase):
    def test_H1_bom_prefixed_frontmatter_is_parsed(self):
        """A UTF-8 BOM before the opening fence must not hide the frontmatter."""
        meta, body = crumb.parse_frontmatter("﻿---\nstatus: active\n---\nbody\n")
        self.assertEqual(meta.get("status"), "active")
        self.assertIn("body", body)

    def test_H1_bom_in_file_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "2026-06-25-x.md"
            p.write_bytes("﻿---\nstatus: active\n---\nhi\n".encode("utf-8"))
            rec = crumb.Record.from_file(p, "decision")
            self.assertIsNone(rec.error)
            self.assertEqual(rec.meta.get("status"), "active")

    def test_H2_binary_md_is_captured_not_raised(self):
        """A non-UTF-8 .md must be captured as a Record error, not crash the walk."""
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "2026-06-25-bin.md"
            p.write_bytes(b"\xff\xfe\x00\x01 not utf-8 \x80\x81")
            rec = crumb.Record.from_file(p, "decision")  # must not raise
            self.assertIsNotNone(rec.error)
            self.assertEqual(rec.meta, {})

    def test_H2_load_records_survives_binary_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            mem = root / crumb.MEMORY_DIRNAME
            (mem / "decisions" / "2026-06-25-bin.md").write_bytes(b"\xff\xfe\x80bad")
            recs = crumb.load_records(mem)  # must not raise
            self.assertTrue(any(r.error for r in recs))

    def test_M1_quoted_scalar_with_trailing_comment_drops_quotes(self):
        self.assertEqual(crumb._parse_scalar('"abc" # a comment'), "abc")
        self.assertEqual(crumb._parse_scalar("'xy' # note"), "xy")

    def test_M1_hash_inside_quotes_still_preserved(self):
        # regression guard: the existing behavior must not break
        self.assertEqual(crumb._parse_scalar('"#42"'), "#42")

    def test_M1_unquoted_inline_comment_still_stripped(self):
        self.assertEqual(crumb._parse_scalar("active   # the default"), "active")


# --------------------------------------------------------------------------- #
# Group 2 — write-path round-trip integrity
# --------------------------------------------------------------------------- #
class WritePathRoundTripTests(unittest.TestCase):
    def test_M2a_is_map_item_is_quote_aware(self):
        self.assertFalse(crumb._is_map_item('"a: b"'))
        self.assertFalse(crumb._is_map_item("'k: v'"))
        # genuine map item still detected
        self.assertTrue(crumb._is_map_item("type: commit"))

    def test_M2a_list_scalar_with_colon_roundtrips(self):
        meta = {"tags": ["area: backend", "todo:", "plain"]}
        text = "---\n" + crumb.render_frontmatter(meta).split("---\n", 1)[1]
        parsed, _ = crumb.parse_frontmatter(text + "\nbody\n")
        self.assertEqual(parsed["tags"], ["area: backend", "todo:", "plain"])

    def test_M2b_render_scalar_rejects_newline(self):
        with self.assertRaises(ValueError):
            crumb._render_scalar("line1\nfoo: bar")

    def test_M2b_newline_title_rejected_no_record_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            rc = crumb.main([
                "remember", "decision", "--project", str(root),
                "--title", "Line1\nfoo: bar", "--confidence", "low",
            ])
            self.assertNotEqual(rc, 0)
            decisions = list((root / crumb.MEMORY_DIRNAME / "decisions").glob("*.md"))
            self.assertEqual(decisions, [])  # nothing corrupted/written


if __name__ == "__main__":
    unittest.main(verbosity=2)
