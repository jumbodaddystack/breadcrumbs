---
id: dec_20260610_session-parser-contract
type: decision
slug: session-parser-contract
title: Freeze the session parser contract before touching middleware
status: active
created_at: 2026-06-10T11:00:00-05:00
updated_at: 2026-06-10T11:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 9f8e7d6
dirty_files: []
confidence: high
privacy: repo-safe
review_status: reviewed
reviewed_by: alex
supersedes: []
superseded_by: null
expires_at: null
tags:
  - auth
  - session
evidence:
  - type: commit
    ref: 9f8e7d6
  - type: file
    ref: src/auth/session.ts
---

## Context
Freeze the session parser contract before touching middleware.

## Options Considered
Several; see rationale.

## Decision
Lock the session parser interface; consumers depend on its shape.

## Rationale
The auth middleware reads the parsed session; changing both at once broke us before.

## Consequences
Tracked in follow-up records.

## What Not To Retry
See the related attempt record.

## Evidence
- commit 9f8e7d6

## Stale / Review Conditions
Revisit if the component contract changes.
