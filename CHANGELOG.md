# Changelog

All notable changes to **crumb-kit** (the `breadcrumbs` package) are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the project
uses semantic versioning. The package version is independent of the on-disk record
`schema_version` (still `1`); `crumb --version` prints both.

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
