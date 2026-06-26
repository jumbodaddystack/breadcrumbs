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


# --------------------------------------------------------------------------- #
# Group 3 — secret scan + privacy vocabulary
# --------------------------------------------------------------------------- #
def _matches_any_secret(sample: str) -> bool:
    return any(pat.search(sample) for _, pat in crumb.SECRET_PATTERNS)


class SecretScanAndPrivacyTests(unittest.TestCase):
    def test_M7_openai_project_key(self):
        self.assertTrue(_matches_any_secret("OPENAI_KEY=sk-proj-" + "A1b2" * 10))

    def test_M7_github_fine_grained_pat(self):
        self.assertTrue(_matches_any_secret("creds: github_pat_" + "A1b2c3D4e5" * 3))

    def test_M7_stripe_secret_key(self):
        self.assertTrue(_matches_any_secret("STRIPE=sk_live_" + "A1b2c3D4e5f6g7h8"))

    def test_M6_privacy_typo_is_flagged_by_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            mem = root / crumb.MEMORY_DIRNAME
            (mem / "decisions" / "2026-06-25-typo.md").write_text(
                "---\n"
                "id: dec_20260625_typo\n"
                "type: decision\n"
                "slug: typo\n"
                "status: active\n"
                "created_at: 2026-06-25T10:00:00-05:00\n"
                "confidence: low\n"
                "privacy: secret-prohibitted\n"  # typo — must NOT silently pass
                "---\n## Context\nx\n## Decision\ny\n",
                encoding="utf-8",
            )
            findings = crumb.run_validate(mem)
            privacy_fails = [f for f in findings
                             if f["check"] == "privacy" and f["status"] == "fail"]
            self.assertTrue(privacy_fails, "typo'd privacy value should fail validate")


# --------------------------------------------------------------------------- #
# Group 4 — guard / search correctness
# --------------------------------------------------------------------------- #
class GuardSearchTests(unittest.TestCase):
    def test_M9_norm_files_drops_empty_basename_for_trailing_slash(self):
        out = crumb._norm_files(["src/auth/"])
        self.assertNotIn("", out)

    def test_M9_unrelated_dirs_do_not_match_via_empty_basename(self):
        a = crumb._norm_files(["build/"])
        b = crumb._norm_files(["logs/"])
        self.assertEqual(a & b, set())  # no spurious "" overlap

    def _file_item(self, files):
        return {
            "id": "x", "kind": "decision", "status": "active", "title": "t",
            "tags": set(), "specific": set(), "branch": None, "record": None,
            "do_not_retry": False, "files": crumb._norm_files(files),
        }

    def test_M10_distinct_files_same_basename_count_separately(self):
        item = self._file_item(["src/a/config.ts", "src/b/config.ts"])
        q_files = crumb._norm_files(["src/a/config.ts", "src/b/config.ts"])
        res = crumb._score_item(item, set(), q_files, Path("."), "main", 9999, min_keyword=2)
        self.assertIsNotNone(res)
        # both distinct files must be cited and scored, not collapsed to one
        self.assertEqual(len(res["matched_files"]), 2)
        self.assertEqual(res["score"], crumb.GUARD_W_FILE * 2 + crumb.GUARD_W_STATUS_ACTIVE)

    def test_M10_basename_variant_of_same_file_not_double_counted(self):
        item = self._file_item(["src/a/config.ts"])
        q_files = crumb._norm_files(["src/a/config.ts"])
        res = crumb._score_item(item, set(), q_files, Path("."), "main", 9999, min_keyword=2)
        self.assertEqual(len(res["matched_files"]), 1)

    def test_H5_open_question_drives_guard_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            crumb.main(["init", "--project", str(root), "--session-tracking", "full"])
            mem = root / crumb.MEMORY_DIRNAME
            (mem / "open-questions.md").write_text(
                "# Open Questions\n\n"
                "## Q: Should the payments reconciliation ledger be rewritten?\n"
                "- opened: 2026-06-25\n"
                "- status: open\n\n"
                "Touches src/payments/ledger.py — unresolved.\n",
                encoding="utf-8",
            )
            result = crumb.guard(
                mem, root,
                "rewrite the payments reconciliation ledger",
                files=["src/payments/ledger.py"],
            )
            ids = [m["id"] for m in result["matches"]]
            self.assertTrue(any(i.startswith("q:") for i in ids),
                            f"open question should reach verdict matches; got {ids}")
            self.assertNotEqual(result["verdict"], "PROCEED")


# --------------------------------------------------------------------------- #
# Group 5 — capture / handoff fidelity
# --------------------------------------------------------------------------- #
import subprocess  # noqa: E402


class CaptureHandoffTests(unittest.TestCase):
    def _git(self, root, *args):
        subprocess.run(["git", *args], cwd=root, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def test_M3_renamed_file_records_destination_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._git(root, "init")
            self._git(root, "config", "user.email", "t@t")
            self._git(root, "config", "user.name", "t")
            (root / "old.txt").write_text("hello\n")
            self._git(root, "add", "-A")
            self._git(root, "commit", "-m", "init")
            self._git(root, "mv", "old.txt", "new.txt")
            dirty = crumb.git_dirty_files(root)
            self.assertIn("new.txt", dirty)
            self.assertNotIn("old.txt -> new.txt", dirty)

    def test_M4_handoff_preserves_user_added_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            (mem / "handoff.md").write_text(
                "# Project Handoff\n\n## Current Focus\nold focus\n\n"
                "## My Custom Section\nvaluable user notes\n",
                encoding="utf-8",
            )
            crumb.update_handoff(mem, "main", "abc1234", "new focus", "do x")
            text = (mem / "handoff.md").read_text(encoding="utf-8")
            self.assertIn("My Custom Section", text)
            self.assertIn("valuable user notes", text)

    def test_M5_no_commits_does_not_clobber_recently_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            mem = Path(tmp)
            (mem / "current.md").write_text(
                "# Current State\n\n## Current Focus\nf\n\n"
                "## Recently Changed\n- real prior summary\n\n## Watch Out For\nw\n",
                encoding="utf-8",
            )
            crumb.update_current(mem, "f2", "_(no new commits)_")
            text = (mem / "current.md").read_text(encoding="utf-8")
            self.assertIn("real prior summary", text)
            self.assertNotIn("_(no new commits)_", text)

    def test_M5b_autolink_is_not_treated_as_placeholder(self):
        self.assertFalse(crumb._is_placeholder("<https://wiki/internal>"))
        # genuine angle-bracket template stub still detected
        self.assertTrue(crumb._is_placeholder("<describe the current focus>"))


# --------------------------------------------------------------------------- #
# Group 6 — resume packet disclosure
# --------------------------------------------------------------------------- #
class ResumePacketTests(unittest.TestCase):
    def _packet(self, **over):
        p = {
            "source": {"commit": "abc", "inputs_hash": "h", "generated_at": "t"},
            "project": {"name": "p", "path": "/p", "branch": "main",
                        "commit": "abc", "dirty_state": "clean"},
            "current_focus": "", "next_action": "", "fast": False,
            "active_decisions": [], "failed_attempts": [], "known_traps": [],
            "open_questions": [], "likely_files": [], "verification": [],
            "warnings": [], "omitted": {},
        }
        p.update(over)
        return p

    def test_M8_omitted_note_shown_when_section_fully_trimmed(self):
        packet = self._packet(verification=[], omitted={"verification": 3})
        md = crumb.render_packet_markdown(packet)
        # the section is empty but 3 were trimmed — the disclosure must survive
        self.assertIn("3 more omitted", md)

    def test_M8_no_spurious_note_when_nothing_omitted(self):
        packet = self._packet(verification=[], omitted={})
        md = crumb.render_packet_markdown(packet)
        self.assertNotIn("omitted", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
