# Changelog

All notable changes to **crumb-kit** (the `breadcrumbs` package) are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the project
uses semantic versioning. The package version is independent of the on-disk record
`schema_version` (still `1`); `crumb --version` prints both.

## [Unreleased]

Resolves the six high-severity findings from the third (full-system) review
(`docs/crumb-kit-system-review-2026-07-01.md`, R1–R6).

### Fixed
- **`capture session` reindexes on write (R1)** — the session-end flow (and the
  `Stop → crumb hook capture` hook) mutates three packet inputs (session record,
  `handoff.md`, `current.md`) but was the one canonical mutation that never
  refreshed the `generated/` projections, so `crumb validate` failed on
  freshness immediately after the documented workflow.
- **Integrations-only `init` on an existing store (R2)** — `crumb init
  --with-adapter/--with-mcp/--with-hooks` against a project that already has a
  store now applies just those integrations and leaves the store untouched;
  previously it errored and steered users toward `--force`, which replaces the
  scaffold and deletes every record. The clobber-guard message now spells out
  that `--force` is destructive.
- **Round-trip-safe frontmatter re-rendering (R3)** — values containing both
  quote kinds are now emitted single-quoted with YAML `''` escaping (and parsed
  back), block lists render both scalar and map items under *any* key (scalar
  `evidence` items no longer crash; list-of-maps under generic keys no longer
  persist as Python `repr` strings), unrepresentable nesting raises instead of
  corrupting, and `set_record_status` refuses to write any rendering the parser
  would read back differently (fail-closed round-trip check).
- **Fence-aware markdown section splitting (R4)** — `## ` lines inside
  ``` / ~~~ code fences are content, not section boundaries, so `capture
  session` no longer structurally corrupts a `handoff.md`/`current.md` whose
  sections contain fenced command output.
- **MCP server on Python 3.10/3.11 (R5)** — tool schemas now use
  `typing_extensions.TypedDict` (with a stdlib fallback for SDK-less installs);
  pydantic rejects `typing.TypedDict` before Python 3.12, so `breadcrumbs-mcp`
  crashed at startup on two of the three advertised Python versions.
- **Release dry-run publishes to TestPyPI (R6)** — `release.yml` now routes
  `workflow_dispatch` to TestPyPI (environment `testpypi`) and only a published
  GitHub release to real PyPI, matching RELEASING.md; previously the documented
  "dry-run" performed an irreversible real publish.

## [0.1.4] — 2026-06-29

Resolves the high-leverage findings from the second agentic review (MCP
integration, write path, cloud portability — `docs/crumb-kit-agentic-review-2026-06-27.md`).
The CLI remains the single source of behavior; the MCP layer stays a thin wrapper
over it. The on-disk record `schema_version` is unchanged (still `1`): the new
`verification` records use the same frontmatter contract as existing record types.

### Added
- **`verification` record type (F1)** — a first-class home for "I checked X; here
  is its state", the most common agentic output, which previously had to be
  mis-filed as a decision/attempt. `crumb verify <subject> --status <outcome>
  --method <static|runtime|test> --evidence …` and the `memory_verify` MCP tool.
  The record-level `status` stays the lifecycle value; the finding-about-reality
  lives in an `outcome` field (`fixed|open|regressed|not_applicable|inconclusive`).
  Verifications are searchable (`crumb search --type verification --status open`,
  where `status` filters on the outcome) and surfaced in the resume packet under a
  new **Verifications** section, actionable outcomes first.
- **`crumb reindex` + `memory_reindex` (F2)** — explicit rebuild of the
  `generated/` projections from the canonical records.
- **`crumb mcp doctor` (F11)** — report MCP wiring (the `[mcp]` extra and
  `.mcp.json` registration) from the CLI's own help surface.
- **`crumb resume --task` (F4/F6)** — resume *for a task*: `likely_files` is scoped
  to the records that actually match it (empty + a `starting cold` note when the
  store has nothing), and the requested task is echoed above the last-session
  focus so the two are not conflated.

### Fixed
- **Reindex-on-write (F2)** — every canonical mutation (`remember`, `note`,
  `verify`, `mark-status`, and their MCP equivalents) now refreshes the
  `generated/` projections, so the static snapshots can no longer silently desync
  from the records on the write path.
- **`validate` projection-freshness check (F3)** — `validate` now fails on a
  `generated/` projection whose stamped `inputs_hash` no longer matches the live
  records, with an actionable `Run \`crumb reindex\`` hint. It no longer stays
  green (and thereby *certifies* drift) on a desynced store.

## [0.1.3] — 2026-06-27

Resolves the four issues deferred from the 2026-06-26 full-codebase bug review
(#4). No behavior changes to stored data; the CLI remains the single source of
behavior.

### Fixed
- **Secret scanner** now flags a long hex token when it sits behind a credential
  label (`token:`, `Authorization:` without "Bearer", `X-…-Key:` / `X-…-Token:`
  headers) via a new `labeled-hex-secret` pattern. A bare git sha / `inputs_hash`
  digest stays unflagged, preserving the deliberate false-negative tradeoff (#5).
- **MCP tool inputs** advertise structured schemas instead of opaque `dict`:
  `memory_search` filters and `memory_record` payload are now `TypedDict`s, so the
  derived JSON Schema lists properties and marks `title` required (#6).
- **MCP error contract** unified — every tool returns `{ok: false, error}` when no
  memory store exists (matching `memory_record` / `memory_mark_status`), instead of
  some tools raising `FileNotFoundError`. The message is now project-relative and no
  longer leaks the absolute host path. Resources still raise (the correct MCP
  resource contract) but share the same message (#7).
- **Cleanup batch (#8):** clear "tabs are not allowed" parser error for tab-indented
  frontmatter; removed the `audit` double trailing newline; non-canonical
  frontmatter keys are preserved on a status change; `inputs_hash` is read only from
  the generated source-header (not a stray match in body text); manifest values are
  unquoted; no redundant identity `pass` alongside a duplicate-id fail; future-dated
  handoffs render as a clock-skew note instead of a negative age; the omitted-note
  wording distinguishes a per-section cap from the token budget.

## [0.1.2] — 2026-06-27

Implements the fixes from the 2026-06-26 agentic review. The headline change makes
the memory store get *used* automatically instead of depending on an agent
remembering to invoke the CLI.

### Added
- **`crumb init` bootstrapper** — opt-in integrations that wire the store into your
  agent, each fenced and reversible: inject a signpost block into detected
  agent-guidance files (`CLAUDE.md`/`AGENTS.md`/…), merge a `breadcrumbs` entry into
  `.mcp.json`, and install Claude Code hooks. Flags: `--with-adapter[=files]`,
  `--with-mcp`, `--with-hooks[=session,guard,capture]` (and `--no-*`),
  `--print-integrations` (dry run), `--remove-integrations` (clean reversal). On a
  TTY with none specified, `init` asks once per integration; default non-interactive
  `init` is unchanged and prints a one-line nudge.
- **`crumb doctor`** — reports integration health (adapter block, `.mcp.json`,
  hooks, resume-packet staleness); exits non-zero when a store exists but nothing is
  wired up.
- **`crumb hook session|guard|capture`** — Claude Code hook translators.
  `SessionStart` auto-loads the resume packet; the cost-aware `PreToolUse` guard runs
  a cheap local risk pre-filter (no record I/O on the common path) and surfaces
  matched memory as context but **never denies from memory alone**; `Stop` snapshots
  a session record.
- **`crumb note question|trap|idea`** plus the `memory_note` MCP tool — a
  validate-gated, projection-refreshing write-surface for the three record kinds that
  previously had no writer. Adds the `idea` body-section vocabulary.
- **`crumb schema [--json] [--template]`** — print the record contract (sections,
  vocabularies, rules) or a fill-in `remember` command skeleton, so the contract is
  discoverable without probing `--help`.
- **Named attempt flags** on `remember attempt`: `--problem`, `--tried`, `--result`,
  `--why`, `--do-not-retry`, `--related`.
- **`crumb mcp serve|register`** — surfaces the optional MCP server from the CLI.

### Changed
- `capture session` now records **Files Touched** as a one-line
  `git diff --shortstat` summary (`N files changed, +X/-Y`) instead of inlining the
  full per-file `--stat`. This removes record bloat and the self-inflicted
  high-entropy secret false-positive on path-shaped tokens.
- The secret scanner allowlists path- and CamelCase-identifier-shaped tokens
  (e.g. `MigrationV14ToV15Test`) without lowering the entropy floor; real
  base64/`=`-padded blobs still flag.

## [0.1.1] — 2026-06-26

- Packaging and metadata fixes over 0.1.0 (bundled templates, `twine`-clean
  wheel + sdist, console scripts `crumb` / `breadcrumbs-mcp`).

## [0.1.0] — 2026-06-26

- Initial release: `init`, `validate`, `remember`, `capture session`, `resume`,
  `search`, `guard`, `audit`, `scan-secrets`, and the optional MCP server.
