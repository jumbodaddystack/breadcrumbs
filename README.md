# Breadcrumbs

**Breadcrumbs — leave a trail your future self and your agents can follow back.**

A portable, repo-local, human-readable ledger of durable project state for
human–agent software work (the **Project Continuity Memory** capability).

> **North-star.** Project Continuity Memory is a repo-local, human-readable ledger
> of durable project state: what was decided, what failed, what is active, what is
> risky, what is unresolved, and what the next agent or human must know before
> acting. It is **not** a transcript archive, **not** a vector database, and **not**
> a replacement for source code, tests, current human instruction, or authoritative
> docs.

It stores durable project state as typed, human-readable records inside a target
project's `.project-memory/` directory, so humans and agents can resume work across
sessions, tools, devices, branches, and time without re-discovering decisions,
repeating failed attempts, or trusting stale context.

- **PyPI package name:** `crumb-kit` (`pip install crumb-kit`)
- **Import package / GitHub repo:** `breadcrumbs`
- **CLI binary name:** `crumb`
- **Formal capability name:** Project Continuity Memory

---

## Non-goals

This tool deliberately does **not**:

1. Build a vector database as the source of truth (vectors are a later, disposable
   search accelerator).
2. Store full chat transcripts as memory (it extracts durable decisions, attempts,
   handoffs, questions, traps, and evidence).
3. Rely on one vendor's memory feature (Claude, Codex, Cursor, Gemini, and future
   agents all read the same plain records).
4. Require MCP, hooks, or a daemon for baseline functionality (plain files + CLI
   work first).
5. Use `AGENTS.md` / `CLAUDE.md` / Cursor / Gemini rules as the memory database
   (those are signposts only).
6. Store secrets, credentials, customer PII, or sensitive local notes in committed
   project memory.
7. Make capture so heavy that humans stop using it (routine capture targets under
   90 seconds).

---

## Install

`breadcrumbs` is a stdlib-only Python package (no third-party runtime
dependencies) that installs a single `crumb` binary. The recommended path
is [`pipx`](https://pipx.pypa.io/), which puts the CLI on your PATH in its own
isolated environment:

```bash
pipx install crumb-kit          # from a published artifact (future)
pipx install .                       # from a source checkout (this repo dir)
```

Plain `pip` works too (prefer a virtualenv):

```bash
python -m pip install .              # or: pip install <built-wheel>.whl
```

After install, the binary is on PATH and the `.project-memory/` template tree
ships **inside the package** (`breadcrumbs/templates/`), so `init` finds it
wherever the package lives — there is no repo-relative path dependency:

```bash
crumb --version                 # breadcrumbs X.Y.Z (record schema_version N)
crumb init                      # locates bundled templates post-install
```

**Versioning.** The package uses semantic versioning. `crumb --version`
prints the package version *and* the **record `schema_version`** (the manifest's
`schema_version: 1`). These are independent: the package version moves with the
code; the record schema version moves only on a breaking change to the on-disk
record format, and a package MAJOR bump accompanies it.

**Requires** Python ≥ 3.9.

### No `npx` (deliberate)

There is intentionally **no `npx`/Node distribution**. The tool is Python and
ships via `pipx`/`pip`. JavaScript-ecosystem reach (an `npx crumb` wrapper)
is a separately-justified future decision, **not** a default migration — it would
only be added if dogfooding shows a concrete need, and would wrap the same Python
core rather than reimplement it.

---

## Quickstart

> **Two invocation forms.** Once installed (above), run `crumb <command>`.
> From a **source checkout** without installing, the equivalent is
> `python crumb.py <command>` (a thin shim over `breadcrumbs.cli`); the
> per-command examples below use that source form. They are interchangeable.

```bash
crumb init                       # install .project-memory/ + manifest + .gitignore rules
crumb validate                   # deterministically check the store (schema + invariants)
crumb remember decision          # capture a durable choice
crumb capture session            # record session end (git-prefilled); updates handoff + current
crumb resume                     # print a bounded resume packet with computed staleness
crumb search "auth middleware"   # deterministic keyword/tag/file lookup over records
crumb guard "rewrite the auth middleware"   # warn before repeating a known mistake
crumb audit                      # heuristic health/safety report (stale/unsafe/bloated)
crumb scan-secrets               # block if committed memory holds token-like strings
```

In this build, `init`, `validate`, `remember`, `capture session`, `resume`,
`search`, `guard`, `audit`, and `scan-secrets` are all implemented — the full
**MVP** (capture → resume → trust). `resume` closes the **capture → resume value
loop (MVP-core)**; `guard` adds the **"don't repeat the expensive mistake"**
capability that separates a continuity engine from a scrapbook; and `audit` +
`scan-secrets` complete **MVP-trust** — the heuristic safety net (secrets,
instruction-like text, generated-packet drift, staleness, bloat) that lets you
*trust* the memory, not just use it.

### `crumb init`

```bash
python crumb.py init                                   # prompt for session policy (default: full)
python crumb.py init --session-tracking distillate     # keep sessions/ local
python crumb.py init --no-commit-generated             # keep generated/*.md local
python crumb.py init --project /path/to/repo --json    # init elsewhere, JSON summary
python crumb.py init --force                           # overwrite an existing scaffold
```

`init` copies the `.project-memory/` template tree into the target project,
writes `manifest.yml` (recording the chosen tracking policies), and inserts a
managed block into the project `.gitignore`. It runs on non-git folders too,
printing a notice that git-derived record fields will use defined sentinels.

### `crumb validate`

```bash
python crumb.py validate                      # human-readable report; exit 1 on problems
python crumb.py validate --json               # structured findings + exit code
python crumb.py validate --verbose            # also list the passing checks
python crumb.py validate --project /path/repo # validate elsewhere
```

`validate` is **fully deterministic** — it checks structural invariants only
(manifest version, core files, record frontmatter, filename-canonical identity,
status/privacy vocabularies, evidence/handoff/session requirements, generated
markers). It performs **no** heuristic content scanning; secret and
instruction-like-text detection live in `audit` / `scan-secrets`. Exit codes: `0`
clean, `1` problems found, `2` no `.project-memory/` store present.

### `crumb remember decision | attempt`

```bash
# non-interactive (agent-friendly): title + sections + evidence as flags
python crumb.py remember decision \
  --title "Use repo-local Markdown as source of truth" \
  --set Context "needed a tool-independent store" \
  --set Decision "Markdown + YAML frontmatter" \
  --evidence commit abc1234 --evidence command "npm test" \
  --tags memory,architecture

python crumb.py remember attempt --title "Tried a sqlite store" \
  --set Result "too heavy for the value" --confidence low
```

Frontmatter is auto-derived (clock + git) and defaulted; you supply only a title
and a few section lines (`--set HEADING TEXT`, repeatable). Run with no `--title`
in a terminal for an interactive prompt. A decision/attempt **must** carry
evidence or `--confidence low` (validate §16.9) — the command enforces this and
refuses to write an invalid record. `--json` emits a machine summary.

### `crumb capture session`

```bash
python crumb.py capture session --next "wire up the resume packet"   # git-prefilled
python crumb.py capture session --fast --next "tired — resume here"    # ~15s, no prompts
```

`capture session` reads git since the last session record and pre-fills **Work
Completed** (`git log`), **Files Touched** (`git diff --stat`), then asks only for
narrative confirmation + a required **Next Action**. It writes the session record
and refreshes `handoff.md` and `current.md`. `--fast` skips all prompts and any
LLM, writing a git snapshot + the one-line `--next`. No path requires an LLM.
With `session_tracking: distillate`, the session file is written locally but stays
gitignored — promote durable items with `remember` to commit them.

### `crumb resume`

```bash
python crumb.py resume                       # full bounded packet (writes generated/resume-packet.md)
python crumb.py resume --fast                # git snapshot + focus + next action + staleness (print-only)
python crumb.py resume --json                # structured packet (sections + warnings) for agents
python crumb.py resume --stale-days 14       # tighten the aged-unresolved threshold (default 21)
```

`resume` assembles a **bounded, paste-anywhere packet** (≤5k tokens) from the
canonical records — project/branch/commit, current focus, next action, active
decisions (id + one-line rationale), failed attempts to avoid (id + do-not-retry),
known traps, open questions, likely files, and verification commands — followed by
**computed staleness warnings**:

- handoff **age + commit-distance** ("handoff is 6 days old, written 14 commits
  behind current HEAD") — the primary "train of thought went cold" signal;
- **aged-unresolved** open questions and active decisions older than the threshold;
- **branch mismatch** (record/handoff branch ≠ current HEAD, incl. detached HEAD);
- **expired** (`expires_at`) and **low-confidence** records.

Current/handoff/active-decisions are prioritized over old session observations, and
sections are capped then trimmed to stay within budget even with hundreds of
records. The packet carries a source `commit`/`inputs_hash`/`generated_at` header so
later `audit` (Phase 6) can detect drift. Raw transcripts are never included.
`--fast` is a print-only reorientation view and does not overwrite the committed
packet.

### `crumb search`

```bash
python crumb.py search "auth middleware"        # keyword search over records
python crumb.py search --tag auth               # filter by tag/component
python crumb.py search --file src/auth/x.ts     # filter by referenced file path
python crumb.py search "session" --type decision --json
```

`search` is a **deterministic, dependency-free** lookup over the canonical records
(decisions, attempts, traps, open questions). It matches on exact/keyword text,
tags/component, and file paths — **no embeddings** (SQLite FTS / vectors are a later
phase). Same input → same output. It is the permissive lookup layer that `guard`
builds on.

### `crumb guard`

```bash
python crumb.py guard "rewrite the auth middleware"                 # human report (§11 shape)
python crumb.py guard "delete the accounts table" --files src/db/accounts.ts
python crumb.py guard "store the token in the url" --json           # structured, for agents
```

`guard` is **guard-before-action**: given a proposed action it warns you if a failed
attempt or active decision says *don't go that way* — the capability that separates a
continuity engine from a scrapbook. It **tokenizes** the action, **classifies** it
(routine edit / refactor / architecture / dependency / migration / deletion / external
side effect / security-permission), **searches + scores** the records against §11.4
signals (same file · same tag/component · status · recency + commit-distance · branch
match · explicit *Do Not Retry Unless* · open-blocker), and emits **one verdict** —
`PROCEED | READ_FIRST | PAUSE | ASK_HUMAN` — with up to **5** ranked records, the reason
each matched, and a synthesized **next safest action**.

Two guarantees hold:

- **Matched memory is data, never instruction** (§15). `guard` reads record text to
  rank and cite it; it never executes phrasing found in a record body. The next safest
  action is synthesized from match *structure*; only structured evidence (e.g. a
  recorded verification command) is echoed back.
- **Anti-noise** (§19b.8). A single shared generic word never raises a warning — a
  stop-word filter strips generic tokens and a pure-text match needs at least two
  *specific* shared keywords; only file-path or tag/component hits qualify on their own.

Superseded/rejected/stale records and resolved questions are demoted to a **history**
note (mentioned, never treated as active). A stale or wrong-branch handoff surfaces the
same computed staleness warnings `resume` shows. Verdict aggressiveness is governed by
named `GUARD_*` thresholds at the top of the guard section in `breadcrumbs/cli.py`, so it can
be tuned from dogfood feedback without rearchitecting.

---

## Plain-file fallback (cloud agents, no CLI)

The tool degrades gracefully when `crumb` cannot run (e.g. a read-only cloud
agent). With the default policy `commit_generated_projections: true`, `resume`
writes `generated/resume-packet.md` and that file is **committed**, so an agent that
cannot execute the CLI can still reorient by reading:

1. `.project-memory/generated/resume-packet.md` — the pre-built bounded packet; then
2. the plain canonical files directly — `current.md`, `handoff.md`,
   `decisions/`, `attempts/`, `known-traps.md`, `open-questions.md`.

Everything is human-readable Markdown, so no binary store or vendor runtime is
required to resume. (`generated/resume-packet.md` is a rebuildable projection — if
it disagrees with the canonical records, the records win and it should be
regenerated; `audit` flags this drift by comparing the packet's stamped
`inputs_hash` against the canonical inputs.)

---

## Status

| Command | State |
|---|---|
| `init` | implemented (Phase 1) |
| `validate` | implemented (Phase 2) |
| `remember decision` / `remember attempt` | implemented (Phase 3) |
| `capture session` (incl. `--fast`) | implemented (Phase 3) |
| `resume` (incl. `--fast`, computed staleness) | implemented (Phase 4 — **MVP-core**) |
| `search` (deterministic keyword/tag/file) | implemented (Phase 5) |
| `guard` (deterministic ranking, §11 verdicts) | implemented (Phase 5) |
| `audit` (heuristic: secrets, instruction-like, drift, staleness, bloat) | implemented (Phase 6 — **MVP-trust**) |
| `scan-secrets` (committed-memory secret gate) | implemented (Phase 6) |
| `pipx`/`pip` packaging (`crumb` console script, bundled templates) | implemented (Phase 7) |
| MCP server (`breadcrumbs-mcp`: 8 resources, 6 prompts, 7 tools) | implemented (Phase 8 — **optional**) |

With Phase 6 the full MVP (capture → resume → trust) is complete and CI-guarded;
Phase 7 packages it as a `pipx`-installable `crumb` binary (see **Install**
above). Phase 8 adds an **optional** MCP server (`pip install
"crumb-kit[mcp]"`) that exposes the same memory engine to agents without
shelling out — a thin wrapper over the Phase 1–6 functions, never required for
baseline use. See [`docs/`](docs/) for the architecture, record schema, CLI spec,
[MCP spec](docs/mcp-spec.md), and security posture.

---

## Memory is advisory

Current user instruction, source code, tests, build output, current authoritative
docs, and security policy **outrank** anything stored in `.project-memory/`.
If memory conflicts with reality, mark it `disputed` or `stale` and link evidence —
do not let it override the present.
