# Project Handoff

_Last updated: 2026-06-18T17:45:00-05:00_
_Branch: main_
_Commit: a1b2c3d_

## Current Focus

Auth middleware + session parser integration.

## Next Action

Make a surgical change to the middleware; do not rewrite it.

## Blockers / Open Questions

_(none)_

## Active Decisions To Respect

dec_20260610_session-parser-contract

## Failed Attempts To Avoid

att_20260612_auth-middleware-rewrite

## Known Traps

_(none)_

## Likely Relevant Files

- continuity.py

## Verification Commands

- python -m unittest discover -s tests

## Stale If

- HEAD moves more than ~15 commits past a1b2c3d
