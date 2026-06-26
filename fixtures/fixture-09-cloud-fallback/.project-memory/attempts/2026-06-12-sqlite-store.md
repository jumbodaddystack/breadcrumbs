---
id: att_20260612_sqlite-store
type: attempt
slug: sqlite-store
title: Tried a SQLite store as the source of truth
status: active
created_at: 2026-06-12T11:00:00-05:00
updated_at: 2026-06-12T11:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: a1b2c3d
dirty_files: []
confidence: high
privacy: repo-safe
review_status: unreviewed
reviewed_by: null
supersedes: []
superseded_by: null
expires_at: null
tags:
  - memory
  - portability
evidence:
  - type: commit
    ref: a1b2c3d
---

## Problem
Recorded for the fixture.

## Tried
Put decisions and attempts in a SQLite database as the canonical store.

## Result
It did not go well.

## Why It Failed / Succeeded
Documented in the fixture.

## Do Not Retry Unless
do not use a binary store unless plain-file export is automatic and reviewed

## Evidence
- commit a1b2c3d

## Related Records
None.
