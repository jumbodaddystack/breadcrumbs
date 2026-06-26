---
id: dec_20260501_auth-token-in-url
type: decision
slug: auth-token-in-url
title: Pass the auth token in the URL query string
status: superseded
created_at: 2026-05-01T11:00:00-05:00
updated_at: 2026-05-01T11:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 1111111
dirty_files: []
confidence: high
privacy: repo-safe
review_status: reviewed
reviewed_by: alex
supersedes: []
superseded_by: dec_20260601_auth-token-in-header
expires_at: null
tags:
  - auth
evidence:
  - type: commit
    ref: 1111111
  - type: file
    ref: src/auth/token.ts
---

## Context
Pass the auth token in the URL query string.

## Options Considered
Several; see rationale.

## Decision
Send the auth token as a ?token= query parameter.

## Rationale
Simplest to wire up for the first prototype.

## Consequences
Tracked in follow-up records.

## What Not To Retry
See the related attempt record.

## Evidence
- commit 1111111

## Stale / Review Conditions
Revisit if the component contract changes.
