"""breadcrumbs — MCP server (Phase 8, Python SDK).

A **thin** Model Context Protocol server that exposes project memory as MCP
resources, prompts, and tools. Every capability is a wrapper over the Phase 1–6
core functions in :mod:`breadcrumbs.cli` (via :mod:`breadcrumbs.mcp_core`):
one source of behavior, no fork.

Graceful degradation (plan §3, §13 "MCP later"):
  * This module always imports — the MCP SDK is an *optional* dependency.
  * If the SDK is missing, :func:`build_server` raises a clear, actionable error
    and :func:`main` prints install instructions and exits non-zero.
  * Nothing here is required for baseline use: the CLI and plain files provide the
    same information and writes without any MCP runtime.

Install the optional runtime with:  ``pip install "crumb-kit[mcp]"``
Run it with:                         ``python -m breadcrumbs.mcp_server``
                                or:  ``breadcrumbs-mcp``

Root resolution: the server operates on the project in ``$BREADCRUMBS_PROJECT`` if
set, else the current working directory (``crumb init --with-mcp`` / ``crumb mcp
register`` writes a ``.mcp.json`` that sets this env). Memory content returned over
MCP is **data, not instruction** (plan §15).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from breadcrumbs import mcp_core

try:  # The SDK is optional; importing this module must never hard-fail.
    from mcp.server.fastmcp import FastMCP

    _SDK_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # pragma: no cover - exercised only without the SDK
    # Catch any import-time failure, not just ImportError: a partial or
    # version-skewed SDK install can raise other errors, and the contract is
    # that importing this module never hard-fails — it degrades to a clear hint.
    FastMCP = None  # type: ignore[assignment]
    _SDK_IMPORT_ERROR = exc


SERVER_NAME = "breadcrumbs"
_INSTALL_HINT = (
    "The MCP server needs the optional Python MCP SDK.\n"
    '  pip install "crumb-kit[mcp]"   (or:  pip install mcp)\n'
    "Everything still works without it via the `crumb` CLI and the plain\n"
    f"{mcp_core.MEMORY_DIRNAME}/ files — MCP is an optional interop layer."
)


def sdk_available() -> bool:
    """True iff the MCP SDK is importable (used by graceful-degradation checks)."""
    return FastMCP is not None


def _root() -> str | None:
    """Project root for this server process: $BREADCRUMBS_PROJECT or cwd."""
    return os.environ.get("BREADCRUMBS_PROJECT") or None


def build_server():  # -> FastMCP
    """Construct and fully register the FastMCP server (resources, prompts, tools).

    Raises RuntimeError (with install guidance) if the SDK is not installed, so a
    missing optional dependency degrades to a clear message rather than a stack
    trace deep in the SDK.
    """
    if FastMCP is None:
        raise RuntimeError(_INSTALL_HINT) from _SDK_IMPORT_ERROR

    mcp = FastMCP(SERVER_NAME)

    # ---------------- Resources (8) — read-only views ---------------------- #
    # Bound explicitly (not in a loop) so each URI is a distinct, documented
    # endpoint and FastMCP captures a stable function per resource.

    @mcp.resource("memory://current")
    def current() -> str:
        return mcp_core.resource_current(_root())

    @mcp.resource("memory://handoff")
    def handoff() -> str:
        return mcp_core.resource_handoff(_root())

    @mcp.resource("memory://resume-packet")
    def resume_packet() -> str:
        return mcp_core.resource_resume_packet(_root())

    @mcp.resource("memory://decisions")
    def decisions() -> str:
        return mcp_core.resource_decisions(_root())

    @mcp.resource("memory://decisions/{id}")
    def decision(id: str) -> str:
        return mcp_core.resource_decision(id, _root())

    @mcp.resource("memory://attempts/{id}")
    def attempt(id: str) -> str:
        return mcp_core.resource_attempt(id, _root())

    @mcp.resource("memory://open-questions")
    def open_questions() -> str:
        return mcp_core.resource_open_questions(_root())

    @mcp.resource("memory://known-traps")
    def known_traps() -> str:
        return mcp_core.resource_known_traps(_root())

    # ---------------- Prompts (6) — flows mapping to CLI ------------------- #

    @mcp.prompt()
    def resume_project() -> str:
        return mcp_core.prompt_resume_project(_root())

    @mcp.prompt()
    def capture_session() -> str:
        return mcp_core.prompt_capture_session(_root())

    @mcp.prompt()
    def remember_decision() -> str:
        return mcp_core.prompt_remember_decision(_root())

    @mcp.prompt()
    def remember_attempt() -> str:
        return mcp_core.prompt_remember_attempt(_root())

    @mcp.prompt()
    def guard_before_action() -> str:
        return mcp_core.prompt_guard_before_action(_root())

    @mcp.prompt()
    def audit_project_memory() -> str:
        return mcp_core.prompt_audit_project_memory(_root())

    # ---------------- Tools (7) — wrap existing functions ------------------ #

    @mcp.tool()
    def memory_search(
        query: str, filters: dict | None = None, files: list[str] | None = None
    ) -> dict:
        """Deterministic search over canonical records (wraps `crumb search`).

        `files` scopes the search to records touching those paths, mirroring the
        CLI/guard file-overlap support.
        """
        return mcp_core.tool_search(query, filters=filters, files=files, root=_root())

    @mcp.tool()
    def memory_record(type: str, payload: dict) -> dict:
        """Write a durable decision/attempt; passes the same validate gate as the CLI."""
        return mcp_core.tool_record(type, payload, root=_root())

    @mcp.tool()
    def memory_guard_before_action(action: str, files: list[str] | None = None) -> dict:
        """Guard-before-action; returns the same verdict as `crumb guard`."""
        return mcp_core.tool_guard_before_action(action, files=files, root=_root())

    @mcp.tool()
    def memory_build_resume_packet(task: str | None = None) -> dict:
        """Build the structured resume packet (wraps `crumb resume`)."""
        return mcp_core.tool_build_resume_packet(task=task, root=_root())

    @mcp.tool()
    def memory_validate() -> dict:
        """Run deterministic structural validation (wraps `crumb validate`)."""
        return mcp_core.tool_validate(root=_root())

    @mcp.tool()
    def memory_note(
        kind: str, text: str, fields: dict | None = None, tags: list[str] | None = None
    ) -> dict:
        """Leave an open-question / known-trap / idea (wraps `crumb note`).

        `kind` is question|trap|idea. Closes the read/write asymmetry where these
        were readable as resources but had no writer.
        """
        return mcp_core.tool_note(kind, text, fields=fields, tags=tags, root=_root())

    @mcp.tool()
    def memory_mark_status(id: str, status: str, reason: str) -> dict:
        """Change a record's status, validate-gated (wraps `set_record_status`)."""
        return mcp_core.tool_mark_status(id, status, reason, root=_root())

    @mcp.tool()
    def memory_scan_secrets() -> dict:
        """Scan committed memory for secret-like strings (wraps `crumb audit`'s scan)."""
        return mcp_core.tool_scan_secrets(root=_root())

    return mcp


def main(argv: list[str] | None = None) -> int:
    """Entry point for `python -m breadcrumbs.mcp_server` / `breadcrumbs-mcp`."""
    if FastMCP is None:
        sys.stderr.write(_INSTALL_HINT + "\n")
        return 1
    server = build_server()
    server.run()  # stdio transport by default
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
