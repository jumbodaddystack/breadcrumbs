---
id: att_20260612_auth-middleware-rewrite
type: attempt
slug: auth-middleware-rewrite
title: Tried a full rewrite of the auth middleware around the new session parser
status: active
created_at: 2026-06-12T14:00:00-05:00
updated_at: 2026-06-12T14:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 7c6b5a4
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
evidence:
  - type: commit
    ref: 7c6b5a4
  - type: file
    ref: src/auth/middleware.ts
  - type: command
    ref: npm test -- auth.middleware.test.ts
---

## Problem
Tried a full rewrite of the auth middleware around the new session parser.

## Tried
Rewrote the auth middleware from scratch to consume the new session parser.

## Result
Broke tenant resolution; sessions intermittently failed to authenticate.

## Why It Failed / Succeeded
The session parser contract was still in flux, so the rewrite chased a moving target.

## Do Not Retry Unless
Do not retry a full auth middleware rewrite unless the session parser contract is frozen and reviewed first.

## Evidence
- commit 7c6b5a4

## Related Records
See the related decision.
