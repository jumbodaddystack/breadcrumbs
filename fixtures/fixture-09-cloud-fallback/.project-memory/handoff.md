# Project Handoff

_Last updated: 2026-06-19T17:00:00-05:00_
_Branch: main_
_Commit: a1b2c3d_

## Current Focus

Plain-file portability.

## Next Action

Verify a CLI-less agent can resume from the committed files.

## Blockers / Open Questions

_(none)_

## Active Decisions To Respect

dec_20260610_markdown-source-of-truth

## Failed Attempts To Avoid

att_20260612_sqlite-store

## Known Traps

_(none)_

## Likely Relevant Files

- continuity.py
- .project-memory/generated/resume-packet.md

## Verification Commands

- python -m unittest discover -s tests

## Stale If

- HEAD moves more than ~15 commits past a1b2c3d
