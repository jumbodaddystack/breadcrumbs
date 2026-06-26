# Project Handoff

_Last updated: 2026-05-20T17:45:00-05:00_
_Branch: main_
_Commit: a1b2c3d_

## Current Focus

Resume packet assembly — turning captured memory into a bounded boot summary.

## Next Action

Implement `build_resume_packet` and bound it to 5k tokens.

## Blockers / Open Questions

Waiting on a decision about the default staleness threshold (see open-questions.md).

## Active Decisions To Respect

dec_20260510_markdown-source-of-truth

## Failed Attempts To Avoid

att_20260512_sqlite-store-too-heavy

## Known Traps

trap_token_estimate

## Likely Relevant Files

- continuity.py — the resume command lives here
- templates/project-memory/generated/resume-packet.md — the projection it writes

## Verification Commands

- python -m unittest discover -s tests

## Stale If

- HEAD moves more than ~15 commits past a1b2c3d
- the resume packet format changes
