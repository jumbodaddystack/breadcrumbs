# crumb-kit (breadcrumbs) — System Review #3 (full-system: code, trust loop, distribution)

**Date:** 2026-07-01
**Reviewer:** AI agent (Claude), as the primary consumer of the tool
**Version evaluated:** `crumb-kit` 0.1.4 (record schema_version 1), source checkout at `f87aa85`
**Basis:** (a) a live end-to-end dogfood of the full CLI surface in a fresh git repo
(`init`, `remember`, `note`, `verify`, `capture --fast`, `resume`/`--fast`/`--task`,
`search`, `guard`, `audit`, `scan-secrets`, `validate`, `doctor`, all three
integrations incl. removal round-trip, and the `hook session|guard|capture`
runtime over real stdin payloads); (b) a four-track adversarial code review of
`breadcrumbs/cli.py` (5,435 lines), `mcp_core.py`, `mcp_server.py`, the test
suite, packaging, CI/release workflows, and docs — every finding below was
**confirmed by reproduction or a precise code-path argument**, not pattern-matched;
(c) the full test suite (280 passed, 1 skipped on py3.11).

> **Relationship to reviews #1 (2026-06-26) and #2 (2026-06-27).** Those reviews
> evaluated the CLI and the MCP layer as a *user*. This pass verifies their fixes
> and goes underneath: record round-trip integrity, the projection trust loop,
> the hook runtime, and the distribution pipeline. The #2 fixes largely hold —
> see §2 — but the trust loop has one remaining hole (capture), and this pass
> found a layer of integrity bugs the earlier reviews could not see from the
> command line.

---

## 1. Executive summary

**Verdict: the design is still the strongest thing in the category, and the
0.1.4 trust-loop work is real — but the system currently breaks its own trust
guarantees in four places, and two of them are in the paths the tool itself
recommends.** The session-end flow leaves `validate` red; the documented way to
wire integrations into an existing store destroys the store; the status-mutation
path can silently corrupt records that `validate` then certifies; and the MCP
server crashes at startup on two of the three Python versions it advertises.
None of these are deep design faults — every one has a small, local fix — but
together they mean 0.1.4's "capture → resume → **trust**" claim is not yet true
end-to-end.

| # | Sev | Area | Finding | One-line fix |
|---|-----|------|---------|--------------|
| R1 | High | trust loop | `capture session` (and the Stop hook) never reindexes projections → `validate` fails immediately after the documented session-end flow | call `reindex_projections` in `cmd_capture_session` |
| R2 | High | data loss | No non-destructive path to add integrations to an existing store; the error message and `crumb doctor`'s nudge steer users to `--force`, which rmtree's all memory | let `init --with-*` on an existing store apply integrations only |
| R3 | High | record integrity | Renderer/parser asymmetry: `set_record_status` re-renders records it cannot faithfully emit — both-quotes strings truncate, list-of-maps become Python `repr` strings, scalar evidence lists crash — and `validate` passes the corrupted results | re-parse-and-compare fail-closed, or surgical `status:`/`updated_at:` line edit |
| R4 | High | content integrity | `split_md_sections` treats `## ` inside code fences as section boundaries → `capture session` structurally corrupts handoff.md/current.md that contain fenced blocks | fence-aware splitting; preserve unknown content verbatim |
| R5 | High | distribution | MCP server crashes at startup on Python 3.10/3.11 with the SDK installed (`typing.TypedDict` + pydantic < 3.12); actual floor is 3.12 vs documented 3.10 | use `typing_extensions.TypedDict` fallback (or gate); add an SDK CI job |
| R6 | High | release process | RELEASING.md's "Dry-run on TestPyPI" instructs a manual workflow run that release.yml actually publishes to **real PyPI**, irreversibly | add a TestPyPI job for `workflow_dispatch` (or fix the doc) |
| R7 | Med | trust loop | `_inputs_hash` omits `manifest.yml` (which the packet reads) → validate's freshness check can certify a genuinely drifted packet | hash the manifest too |
| R8 | Med | trust loop | Resume packet's 5k-token bound is violated by the uncapped `warnings` list; the trimmer empties every substantive section first, and a trim step can *grow* the packet | cap/trim warnings; count the omitted-note line |
| R9 | Med | automaticity | The PreToolUse guard hook's risk pre-filter is blind to trap-shaped routine commands (`pytest -n auto` trap invisible via hook; direct `guard` says READ_FIRST) — the exact near-miss class that motivated hooks in review #1; the regex even hardcodes review #1's `gradlew --stop` | emit a trap-token index into `generated/` at reindex; include it in the pre-filter |
| R10 | Med | MCP parity | `memory_build_resume_packet(task=…)` only echoes the task — it never passes `task=` to the CLI engine, so the F4/F6 `likely_files` scoping doesn't happen over MCP (spec says it does) | pass it through |
| R11 | Med | MCP parity | `memory_record` silently downgrades an explicit `confidence: high` to `low` when evidence is absent, where the CLI refuses with an error — the "no fork in behavior" contract is violated on the flagship write tool | return the same error the CLI gives |
| R12 | Med | CLI | `crumb mcp serve --project PATH` accepts and silently ignores `--project` — the server serves cwd's store, reads *and writes* going to the wrong project | export `BREADCRUMBS_PROJECT` from the flag |
| R13 | Med | hooks | `crumb hook guard` crashes with a raw traceback when `tool_input` is a truthy non-dict (every other hook path defensively returns `{}`) | `isinstance` guard |
| R14 | Med | content integrity | `update_handoff`/`update_current` silently discard content between the header and the first `## `, and collapse duplicate headings (first body lost) | preserve unknown segments |
| R15 | Med | capture | In a shallow clone, `_git_prefill`'s base falls back to the empty tree → "Files Touched" records the entire repo (repro: 25 files claimed, 2 touched) | detect shallow; bound the window |
| R16 | Med | validate | `validate` crashes (instead of reporting a finding) on a list-valued `subject` in a verification record, and on any non-UTF-8 `handoff.md`/`generated/*.md` | catch and emit findings |
| R17 | Med | validate | `SESSION_DONE_MARKERS` are raw substrings — `"done"` matches "aban**done**d", so a session describing abandoned work with no Next Action false-passes the convergence check | word-boundary match |
| R18 | Med | CI | CI never installs the `[mcp]` extra (the one test that would catch R5 self-skips — the suite's single skip) and never runs 3.9 despite `requires-python >=3.9` | add matrix jobs |
| R19 | Low | UX/noise | Fresh store emits placeholder staleness noise on every resume/guard ("branch mismatch: handoff was written on '\<branch\>'", "handoff timestamp is not parseable") until the first capture | placeholder-aware `compute_staleness` |
| R20 | Low | UX/noise | `audit` promotes every `compute_staleness` line to a warning — "handoff is 0 day(s) old, written 0 commit(s) behind" warns on a seconds-old store; the "cold" threshold only toggles a cosmetic ⚠ inside the string | gate severity on the cold flag |
| R21 | Low | records | `git_dirty_files` stores git's C-quoted form verbatim for paths with spaces/quotes/non-ASCII (`'"caf\303\251.txt"'`), which can then trigger R3 | unquote porcelain output |
| R22 | Low | notes | `note` text/fields are not newline-sanitized (embedded `\n## …` forges headings in the singleton files); duplicate trap headings accumulate with earlier bodies unreachable; `_append_md_block` deletes any user line matching `_No … yet._`; a literal `` `<!--` ``/`` `-->` `` pair in two different traps joins across blocks and deletes the trap in between from every reader | sanitize; dedupe; anchor the placeholder filter |
| R23 | Low | ordering | Lexicographic sort on ISO timestamps with heterogeneous UTC offsets picks the wrong "newest" record (`_last_session_commit`, `_by_recency`) — `now_iso()` embeds the local offset, so DST/machine moves make this real | sort on parsed datetimes |
| R24 | Low | robustness | Unborn-HEAD repos record `branch: (no-git)` alongside populated `dirty_files` (contradictory); `load_manifest` truncates values at any `#`; check-then-write record paths race; plain `write_text` (no tmp+rename) can leave truncated records; `set_record_status` writes *before* its validate gate, so a validate crash (R16) strands the mutation; a `reason` containing `-->` escapes the HTML status comment | assorted small fixes |
| R25 | Low | MCP/docs | Inconsistent tool envelope (`ok` missing on search/guard/packet successes; `clean` vs `ok`); `memory_search` spec omits `files`; dead `fast` param; `breadcrumbs-mcp --help` silently starts the server; README references `mark-status`/"mark it disputed" and mcp-spec references a supersede flow — neither exists as a CLI command | align spec + envelope; add the missing write surface |
| R26 | Low | heuristics | Instruction-like scan misses natural phrasings (`ignore failing tests`, `bypass the code review`, `ignore all prior instructions`); secret scan misses `private_key:`/`refresh_token:` labels and only globs `*.md`/`*.yml` (a `.yaml`/`.json` under memory is never scanned) | extend patterns; widen the glob |

---

## 2. Review #2 fixes — verified

Exercised live against a seeded store:

- **F1 (`verify`) — holds.** `crumb verify` writes a validated record, enforces
  evidence-or-low-confidence, surfaces in the packet's Verifications section and
  in `search --type verification`.
- **F2 (reindex-on-write) — holds for `remember`/`note`/`verify`/`mark-status`
  and all four MCP write tools** (verified at the call sites: cli.py:1514, 1637,
  1906, 2029; mcp_core.py:289). **The one canonical mutation left out is
  `capture session` — see R1.**
- **F3 (validate freshness) — holds and is load-bearing.** It is exactly this
  check that exposes R1 within seconds of a capture.
- **F4/F6 (`resume --task`) — holds on the CLI** (Requested Task echoed above
  the last-session focus; scoped `likely_files`; `starting cold` label). **Does
  not hold over MCP — see R10.**
- **F11 (MCP discoverability) — holds** (`crumb mcp serve|register|doctor` all
  present and behaving as documented).

---

## 3. What is genuinely good (verified, not assumed)

- **The guard engine survives adversarial testing.** True-positive READ_FIRST
  citing the attempt (with its do-not-retry), the decision, and the open
  question; trap match on raw command text; clean PROCEED on unrelated actions;
  PAUSE on force-push against do-not-retry memory; no reachable
  division-by-zero; the anti-noise floor and the "matched memory is data, never
  instruction" invariant both hold — `_next_safest_action` synthesizes from
  match structure and never echoes record prose.
- **The fenced managed-block machinery is robust.** Applying and removing all
  three integrations round-trips cleanly while preserving user content in
  `CLAUDE.md`, other servers in `.mcp.json`, and custom hooks in
  `.claude/settings.json`. `merge_json_file` refuses to clobber unparseable or
  non-object JSON rather than overwriting.
- **The hook runtime fails open, by design and in practice.** Malformed stdin →
  `{}` exit 0; missing store → `{}`; `hook capture` never blocks Stop;
  `hook session` injects the full packet as `additionalContext`. READ_FIRST/
  PAUSE→allow+context and ASK_HUMAN→ask, never deny — matching security.md.
- **Secret scanning is strong on real key shapes.** AWS/GitHub/Slack/Google/JWT/
  PEM/Stripe all caught; measured high-entropy false-negative rate ~0.35% on
  random mixed-class tokens; the path/identifier allowlist laundered none of the
  real-secret shapes tested.
- **argparse wiring is correct and complete.** Every flag documented in
  README/cli-spec exists and behaves as documented, including the tricky
  global-flags-after-subcommand mechanism.
- **The stdlib-only discipline, staging-swap init, `--json` everywhere, and
  meaningful exit codes** all continue to be the right calls and are correctly
  implemented (R2 is a policy gap around the staging swap, not a mechanical one).

---

## 4. The four load-bearing findings, in detail

### R1 — the session-end flow fails the tool's own validator

`cmd_capture_session` writes a session record and rewrites `handoff.md` +
`current.md` — three inputs of `_inputs_hash` — and is the only canonical
mutation that never calls `reindex_projections` (present in remember/note/
verify/mark-status/MCP paths; absent here). Reproduced end-to-end: seeded store,
`validate` green → `crumb capture session --fast --next "wire bounded queue"` →
`validate` exits 1 with `✗ [freshness] generated/resume-packet.md: stale
projection … Run 'crumb reindex'`, and `audit` flags packet-drift. With
`--with-hooks` installed, **every session end leaves the store red** until the
next resume. This directly contradicts CHANGELOG 0.1.4 ("every canonical
mutation … now refreshes the `generated/` projections") and README's "never
silently desyncs". The fix is one call; the cost of not fixing it is that the
first thing a new user's CI or next session sees after adopting the recommended
workflow is a failing trust primitive.

### R2 — the recommended wiring path destroys the store

`crumb init --with-hooks` (or `--with-mcp`, `--with-adapter`) on an existing
store hits the store-exists guard and errors with "Use `--force` to overwrite".
`--force` rmtree's `.project-memory/` after staging (cli.py:390–392) — all
decisions, attempts, verifications, traps, questions, sessions, and the
gitignored `private/` are gone, with no backup and no store-specific
confirmation. Reproduced: a 5-record store reduced to template. Worse, `crumb
doctor`'s nudge tells the user to run exactly this failing command against the
store it just examined. Committed records are recoverable from git; local-only
policy (`session_tracking: distillate`), `private/`, and non-git projects are
not. Integration application is already a separate, idempotent step internally
(`resolve_integration_plan` + `apply_integrations`) — the guard just needs to
let an integrations-only invocation through without scaffolding.

### R3 — status mutation can corrupt what validate then certifies

`parse_frontmatter` accepts a wider grammar than `render_frontmatter` can emit,
and `set_record_status` pipes parsed metadata back through the narrow renderer:

- a title containing both `"` and `'` renders unescaped and re-reads truncated
  (or loses the key entirely) — and `validate` reports **zero** problems on the
  corrupted file;
- a hand-edited list-of-maps under any non-`evidence` key (e.g. `links:`) is
  persisted as a quoted Python `repr` string — `set_record_status` returns
  `{"ok": true}` and the structure is permanently destroyed;
- a scalar `evidence` list (`- commit abc1234`, which validate accepts) crashes
  `set_record_status` with `AttributeError`.

Also in this class: the new text is written *before* `_validate_new_file` runs,
so a validate crash (R16) strands the mutation with no revert and no reindex;
and the free-text `reason` embedded in the status HTML comment can escape it via
`-->`. Cheapest robust fix: after rendering, re-parse and compare against the
intended metadata, refusing to write on mismatch (the same fail-closed posture
the newline check already takes) — or make status mutation a surgical two-line
edit instead of a full re-render.

### R4 — capture corrupts handoffs that contain code fences

`split_md_sections` splits on any line starting `## `, including inside fenced
code blocks. A handoff whose Verification Commands section contains a fenced
block with `## 12 passed` in expected output is reassembled with the fence
unterminated, the managed `## Stale If` heading injected *inside* the open
fence, and the fenced remainder demoted to a bogus trailing section — compounding
on every subsequent capture. Verification commands with `#` output markers are
exactly what this file is for. (R14 is the same rewrite path losing intro
paragraphs and duplicate-heading bodies.)

---

## 5. Distribution and process findings

- **R5:** `mcp_server.py` uses `typing.TypedDict` for tool schemas; pydantic
  hard-rejects that on Python < 3.12, so `breadcrumbs-mcp` tracebacks at startup
  on 3.10/3.11 — the very versions pyproject's `[mcp]` marker (`>=3.10`) and
  mcp-spec.md advertise. Reproduced in a 3.11 venv with mcp 1.28.1 / pydantic
  2.13.4; the same build works on 3.12. The 0.1.3 changelog's "structured
  schemas" fix (#6) is what introduced it, and CI is structurally blind to it
  (R18): the only test that exercises SDK registration self-skips without the
  SDK — the suite's single skipped test.
- **R6:** RELEASING.md's "Dry-run on TestPyPI first" says a manual *Actions →
  release → Run workflow* "publishes to **TestPyPI**"; release.yml's own header
  says "Both triggers publish to real PyPI", and the workflow has no TestPyPI
  job, no `repository-url`, no `testpypi` environment. A maintainer following
  the documented dry-run performs a permanent real publish — the exact mistake
  the doc's own last line warns cannot be undone.
- **R18:** CI runs a single Python (3.11), never installs `[mcp]`, and never
  runs 3.9 despite `requires-python >=3.9` (static analysis found no
  3.10+-at-runtime syntax, so 3.9 *probably* works — but nothing proves it).
  The bundled-template guardrail's magic numbers (18 files / 5 `.gitkeep`) are
  duplicated across ci.yml and release.yml and count files without checking
  identity.

---

## 6. Test-coverage gaps (mapped to findings)

The suite is genuinely good where it looks — 280 tests, fixture-backed,
parity-tested MCP adapters, write-gate revert tests. Every finding above sits in
an untested path. The highest-value additions, in order:

1. A **round-trip property test** for `render_frontmatter` ∘ `parse_frontmatter`
   over adversarial scalars (both quotes, `#`, unicode, empty, literal
   `null`/`true`) and a `set_record_status` rewrite-fidelity test (R3, R21, R24).
2. A **capture-then-validate** test (R1) — one assertion, catches the trust-loop
   regression class forever.
3. `update_handoff` content-preservation tests: fenced `## `, intro paragraph,
   duplicate headings (R4, R14).
4. A CI job with the `[mcp]` extra on 3.10–3.12 that builds the server and lists
   tools (R5, R18), plus a 3.9 stdlib job.
5. Budget stress with warning-heavy stores (R8); hook payload fuzzing with
   non-dict `tool_input` (R13); shallow-clone capture (R15).

---

## 7. Recommendations, ranked

1. **Close the trust loop (R1, R7, R8):** reindex in capture; hash the manifest;
   bound warnings. After this, "capture → resume → trust" is true end-to-end.
2. **Remove the data-loss footgun (R2):** integrations-only `init` on an
   existing store (or a `crumb integrate` alias); make `--force` on a non-empty
   store require an explicit second confirmation or write a timestamped backup.
   Fix doctor's nudge to a command that works.
3. **Make record mutation fail-closed (R3):** re-parse-and-compare before write,
   write via tmp+rename, validate before replacing.
4. **Fence-aware markdown handling (R4, R14, R22):** one shared splitter that
   respects fences and preserves unknown segments would fix five findings.
5. **Fix the MCP floor (R5, R10, R11, R12) and CI blindness (R18):**
   `typing_extensions` fallback (vendored or conditional), pass `task=` through,
   error on evidence-less high confidence, honor `serve --project`, add the SDK
   matrix job.
6. **Fix the release dry-run (R6)** before the next publish — either a real
   TestPyPI job on `workflow_dispatch` (the pending publisher is already
   documented) or rewrite the doc to the local-twine path it also describes.
7. **Derive hook risk from the store (R9):** the pre-filter's promise is "no
   record I/O on the common path", not "no memory"; a trap-token index emitted
   into `generated/` at reindex time keeps the budget and closes the near-miss
   class that motivated hooks in the first place.
8. **Quiet the noise (R19, R20):** placeholder-aware staleness and
   severity-gated audit warnings. A trust surface that always warns trains its
   audience to stop reading it — the same automaticity lesson as review #1, one
   level up.

---

## 8. Closing assessment

Reviews #1 and #2 asked "does it get used?" and "does the loop close?". This
review asked "does it keep its promises under stress?" — and the answer is:
almost, and fixably. The failures found are concentrated exactly where the
previous reviews' fixes stopped: capture is the one mutation outside the
reindex net; `--force` is the one destructive path outside the staging-swap
discipline; `set_record_status` is the one writer outside the validate-gated,
fail-closed posture every other writer has; and 3.10/3.11 is the one deployment
surface outside CI's vision. The pattern is consistent: the *principles* are
right and the *coverage* of those principles is incomplete. Extending four
existing disciplines to the last few call sites — rather than inventing anything
new — would make 0.1.5 the first release where the trust story survives an
adversarial pass intact.
