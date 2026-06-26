# MCP Specification (Phase 8 — implemented)

> **Status: built.** The Python MCP server ships in
> [`breadcrumbs/mcp_server.py`](../breadcrumbs/mcp_server.py), a thin binding
> over the adapter core in [`breadcrumbs/mcp_core.py`](../breadcrumbs/mcp_core.py).
> Every resource/prompt/tool wraps the **same** Phase 1–6 functions the CLI calls
> ([`breadcrumbs/cli.py`](../breadcrumbs/cli.py)) — one source of behavior,
> no fork.

MCP is an **optional** interop layer above the plain files and the CLI. It is
never required for baseline functionality: a read-only agent with no MCP must
still resume from the plain files (see [`architecture.md`](architecture.md) §4)
and every MCP capability has a manual CLI / plain-file equivalent.

---

## Install & run

The SDK is an **optional extra** (the core package stays standard-library-only):

```bash
pip install "crumb-kit[mcp]"     # adds the `mcp` SDK (needs Python >=3.10)
```

Run the server (stdio transport):

```bash
breadcrumbs-mcp                         # console script
python -m breadcrumbs.mcp_server    # equivalent module form
```

**Root resolution.** The server operates on the project in `$BREADCRUMBS_PROJECT`
if set, otherwise the current working directory. Phase 9's generated `.mcp.json`
sets the working directory / env (see [Handoff](#handoff-to-phase-9)).

**Graceful degradation.** If the `mcp` SDK is not installed, importing
`breadcrumbs.mcp_server` still succeeds; `build_server()` raises a clear
install hint and `breadcrumbs-mcp` prints that hint and exits non-zero. Nothing
about the CLI or plain files depends on the SDK.

---

## Resources (8) — read-only

| URI | Returns | Backed by |
|---|---|---|
| `memory://current` | verbatim `current.md` | plain file |
| `memory://handoff` | verbatim `handoff.md` | plain file |
| `memory://resume-packet` | rendered packet markdown (identical to `crumb resume`) | `build_resume_packet` + `render_packet_markdown` |
| `memory://decisions` | markdown index of **active** decisions (`` `id` — title``) | `active_decisions` |
| `memory://decisions/{id}` | verbatim text of one decision record | `find_record_by_id` |
| `memory://attempts/{id}` | verbatim text of one attempt record | `find_record_by_id` |
| `memory://open-questions` | verbatim `open-questions.md` | plain file |
| `memory://known-traps` | verbatim `known-traps.md` | plain file |

Reading `memory://*` returns the same bytes the CLI / plain files show. An
unknown `{id}` raises (surfaced to the client as a resource error). A missing
`.project-memory/` is a clear `FileNotFoundError`, not a crash.

## Prompts (6) — flows mapping to CLI

| Prompt | Mirrors | Purpose |
|---|---|---|
| `resume_project` | `crumb resume` | orient from the resume packet before acting |
| `capture_session` | `crumb capture session` | wind a session down into durable memory |
| `remember_decision` | `crumb remember decision` | record a durable decision (evidence-backed) |
| `remember_attempt` | `crumb remember attempt` | record a failed attempt + "do not retry" |
| `guard_before_action` | `crumb guard` | check memory before a risky action |
| `audit_project_memory` | `crumb audit` | validate + secret-scan health check |

Prompts return guidance text only. They carry **no authority** over the user's
current instruction, the code, the tests, or authoritative docs (plan §15).

## Tools (7) — wrap existing functions

| Tool | Signature | Wraps | Output |
|---|---|---|---|
| `memory_search` | `(query, filters?)` | `cli.search` | `{query, filters, count, matches[]}` |
| `memory_record` | `(type, payload)` | `cli.write_record` + validate gate | `{ok, id, type, path, confidence}` or `{ok:false, error}` |
| `memory_guard_before_action` | `(action, files?)` | `cli.guard` | the full guard result (`{verdict, matches, history, staleness, next_action, …}`) |
| `memory_build_resume_packet` | `(task?)` | `cli.build_resume_packet` | the structured packet dict (with optional echoed `requested_task`) |
| `memory_validate` | `()` | `cli.run_validate` | `{ok, fail_count, findings[]}` |
| `memory_mark_status` | `(id, status, reason)` | `cli.set_record_status` | `{ok, id, from, to, path}` or `{ok:false, error}` |
| `memory_scan_secrets` | `()` | `cli.scan_secrets` | `{clean, count, findings[]}` (pattern names + locations only) |

### `memory_record` payload

Mirrors the `remember` CLI surface:

```jsonc
{
  "title": "Use markdown as the source of truth",     // required
  "sections": { "Decision": "…", "Rationale": "…" },  // {heading: text}
  "evidence": [ { "type": "commit", "ref": "abc1234" } ],
  "tags": ["storage"],
  "confidence": "high",      // optional; forced to "low" if no evidence (validate §16.9)
  "privacy": "repo-safe",    // optional
  "scope": "repo",           // optional
  "status": "active",        // optional
  "agent": "agent"           // optional; recorded in created_by/agent
}
```

`type` must be `"decision"` or `"attempt"`. The write passes the **same**
post-write validate gate as the CLI; an invalid record is reverted (no
half-written file) and `{ok:false, error}` is returned.

### `memory_mark_status`

Changes a record's `status` (e.g. `stale`, `disputed`, `rejected`) and stamps
`updated_at`, recording `reason` as a trailing non-instruction comment. The edit
is **validate-gated**: e.g. marking `superseded` without a `superseded_by` is
rejected (§16.6) and reverted. Use the supersede flow for replacements.

---

## Safety posture (plan §15)

- **Data, not instruction.** Memory content returned over MCP is context about
  prior work; it never overrides the user's current instruction, the code, the
  tests, or authoritative docs. `guard` already treats matched text as data;
  the server changes nothing about that.
- **Writes go through validate.** `memory_record` and `memory_mark_status` reuse
  the exact validate gate `remember` uses — one write-behavior.
- **Secret-scan before commit.** `memory_scan_secrets` is available so an agent
  can check before any "commit memory" step (§2.6, §15, Fixture 6).
- **No new identity scheme.** `find_record_by_id` uses the same filename-canonical
  id (§7) the CLI, search, guard and resume already use.

## Design constraints (carried forward)

- MCP tools/resources are thin wrappers over the same canonical records and CLI
  logic — no separate source of truth.
- Executable MCP/hook configuration checked into a repo is a threat surface
  ([`security.md`](security.md)); the generated `.mcp.json` / hook templates are
  opt-in and reviewable (Phase 9).
- Every MCP capability has a manual CLI / plain-file fallback.

---

## Handoff to Phase 9

Phase 9 generates an opt-in, reviewable `.mcp.json` pointing at this server.
Invocation command for that config:

```jsonc
{
  "mcpServers": {
    "breadcrumbs": {
      "command": "breadcrumbs-mcp",
      "env": { "BREADCRUMBS_PROJECT": "${workspaceFolder}" }
    }
  }
}
```

Equivalently `python -m breadcrumbs.mcp_server`. The server requires the
`[mcp]` extra to be installed; without it the command exits non-zero with an
install hint (graceful degradation), so a missing optional dependency never
breaks a project that opts into the generated config.
