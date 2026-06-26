"""Tests for the frontmatter parser and Record model (Phase 2).

Run with:  python -m pytest tests/
       or:  python tests/test_parser.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import crumb  # noqa: E402


FULL = """---
id: dec_20260625_x
type: decision
slug: x
title: Use repo-local Markdown
status: active
created_at: 2026-06-25T14:30:00-05:00
dirty_files: []
supersedes: []
superseded_by: null
reviewed_by:
expires_at: ~
confidence: medium
tags:
  - memory
  - architecture
evidence:
  - type: commit
    ref: abc1234
  - type: command
    ref: npm test
---
## Context
hello world

## Decision
do the thing
"""


class ParserTests(unittest.TestCase):
    def test_roundtrips_full_schema(self):
        meta, body = crumb.parse_frontmatter(FULL)
        self.assertEqual(meta["type"], "decision")
        self.assertEqual(meta["title"], "Use repo-local Markdown")
        # ISO datetime preserved verbatim as a string (no tz math)
        self.assertEqual(meta["created_at"], "2026-06-25T14:30:00-05:00")
        # inline + block empty lists
        self.assertEqual(meta["dirty_files"], [])
        self.assertEqual(meta["supersedes"], [])
        # nulls (explicit, empty, and ~)
        self.assertIsNone(meta["superseded_by"])
        self.assertIsNone(meta["reviewed_by"])
        self.assertIsNone(meta["expires_at"])
        # block list of scalars
        self.assertEqual(meta["tags"], ["memory", "architecture"])
        # block list of maps (evidence)
        self.assertEqual(
            meta["evidence"],
            [
                {"type": "commit", "ref": "abc1234"},
                {"type": "command", "ref": "npm test"},
            ],
        )
        self.assertIn("## Context", body)

    def test_no_frontmatter_returns_body_verbatim(self):
        text = "# Just a heading\n\nno frontmatter here\n"
        meta, body = crumb.parse_frontmatter(text)
        self.assertEqual(meta, {})
        self.assertEqual(body, text)

    def test_unterminated_fence_is_malformed(self):
        with self.assertRaises(crumb.FrontmatterError):
            crumb.parse_frontmatter("---\nkey: val\nno closing fence\n")

    def test_top_level_indentation_is_malformed(self):
        with self.assertRaises(crumb.FrontmatterError):
            crumb.parse_frontmatter("---\n  oops: indented\n---\nbody\n")

    def test_quoted_value_with_hash_is_preserved(self):
        meta, _ = crumb.parse_frontmatter('---\nref: "#42"\n---\n')
        self.assertEqual(meta["ref"], "#42")

    def test_inline_comment_stripped_on_unquoted_scalar(self):
        meta, _ = crumb.parse_frontmatter("---\nstatus: active   # the default\n---\n")
        self.assertEqual(meta["status"], "active")


class RecordModelTests(unittest.TestCase):
    def test_sections_split_on_h2(self):
        _, body = crumb.parse_frontmatter(FULL)
        rec = crumb.Record(Path("decisions/2026-06-25-x.md"), "decision", {}, body)
        self.assertEqual(set(rec.sections), {"Context", "Decision"})
        self.assertEqual(rec.sections["Context"], "hello world")

    def test_from_file_captures_parse_error(self):
        bad = REPO_ROOT / "tests" / "data" / "decisions" / "2026-06-25-malformed.md"
        rec = crumb.Record.from_file(bad, "decision")
        self.assertIsNotNone(rec.error)
        self.assertEqual(rec.meta, {})

    def test_load_records_walks_type_dirs(self):
        # Build a tiny store from a fresh init + a couple of fixtures.
        import tempfile, shutil  # noqa: E401

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            mem = root / crumb.MEMORY_DIRNAME
            data = REPO_ROOT / "tests" / "data"
            shutil.copy(data / "decisions" / "2026-06-25-good-decision.md", mem / "decisions")
            shutil.copy(data / "sessions" / "2026-06-25-good-session.md", mem / "sessions")
            recs = crumb.load_records(mem)
            types = sorted(r.rtype for r in recs)
            self.assertEqual(types, ["decision", "session"])
            # type filtering
            only_dec = crumb.load_records(mem, types=("decision",))
            self.assertEqual([r.rtype for r in only_dec], ["decision"])


class GlobalFlagPositionTests(unittest.TestCase):
    """Global flags must work whether placed BEFORE or AFTER the subcommand.

    Regression test for issue #3. The parent-parser globals (--project, --json,
    --plain, --verbose) were silently dropped when placed before the subcommand
    because argparse's _SubParsersAction.__call__ parses the subcommand into a
    fresh namespace and copies the subparser's *defaults* back over values the
    top-level parser already set.
    """

    def _parse(self, argv):
        return crumb.build_parser().parse_args(argv)

    def test_project_honored_before_subcommand(self):
        args = self._parse(["--project", "/tmp/store", "validate"])
        self.assertEqual(args.project, "/tmp/store")

    def test_project_honored_after_subcommand(self):
        args = self._parse(["validate", "--project", "/tmp/store"])
        self.assertEqual(args.project, "/tmp/store")

    def test_project_honored_before_nested_subcommand(self):
        args = self._parse(
            ["--project", "/tmp/store", "remember", "decision", "--title", "x"]
        )
        self.assertEqual(args.project, "/tmp/store")

    def test_json_honored_before_subcommand(self):
        self.assertTrue(self._parse(["--json", "validate"]).json)

    def test_verbose_honored_before_subcommand(self):
        self.assertTrue(self._parse(["--verbose", "validate"]).verbose)

    def test_plain_honored_before_subcommand(self):
        self.assertTrue(self._parse(["--plain", "search", "x"]).plain)

    def test_defaults_present_when_flags_absent(self):
        args = self._parse(["validate"])
        self.assertIsNone(args.project)
        self.assertFalse(args.json)
        self.assertFalse(args.plain)
        self.assertFalse(args.verbose)

    def test_global_project_targets_store_from_unrelated_cwd(self):
        """The real-world bug: from a cwd that is not the project, a global
        --project must still resolve to the store (not fail on cwd)."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            saved = os.getcwd()
            with tempfile.TemporaryDirectory() as other:
                try:
                    os.chdir(other)
                    rc = crumb.main(["--project", str(root), "validate"])
                finally:
                    os.chdir(saved)
            self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
