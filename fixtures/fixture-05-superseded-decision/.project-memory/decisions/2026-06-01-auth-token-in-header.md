---
id: dec_20260601_auth-token-in-header
type: decision
slug: auth-token-in-header
title: Move the auth token to the Authorization header
status: active
created_at: 2026-06-01T11:00:00-05:00
updated_at: 2026-06-01T11:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 2222222
dirty_files: []
confidence: high
privacy: repo-safe
review_status: reviewed
reviewed_by: alex
supersedes: [dec_20260501_auth-token-in-url]
superseded_by: null
expires_at: null
tags:
  - auth
evidence:
  - type: commit
    ref: 2222222
  - type: file
    ref: src/auth/token.ts
---

## Context
Move the auth token to the Authorization header.

## Options Considered
Several; see rationale.

## Decision
Send the auth token in the Authorization header, never the URL.

## Rationale
Tokens in URLs leak into logs and browser history.

## Consequences
Tracked in follow-up records.

## What Not To Retry
See the related attempt record.

## Evidence
- commit 2222222

## Stale / Review Conditions
Revisit if the component contract changes.
