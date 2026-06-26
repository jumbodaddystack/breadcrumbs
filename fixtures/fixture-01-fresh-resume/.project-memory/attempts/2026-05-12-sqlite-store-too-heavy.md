---
id: att_20260512_sqlite-store-too-heavy
type: attempt
slug: sqlite-store-too-heavy
title: Tried a SQLite store as the source of truth
status: active
created_at: 2026-05-12T14:00:00-05:00
updated_at: 2026-05-12T14:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 7c6b5a4
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
evidence:
  - type: commit
    ref: 7c6b5a4
---

## Problem
Wanted fast, queryable memory from day one.

## Tried
Put decisions and attempts in a SQLite database as the canonical store.

## Result
Agents without the CLI could not read memory; PR reviews became opaque.

## Why It Failed / Succeeded
A binary store breaks the plain-file portability requirement.

## Do Not Retry Unless
Do not retry a database-as-source-of-truth unless plain-file export is automatic and reviewed.

## Evidence
- commit 7c6b5a4

## Related Records
dec_20260510_markdown-source-of-truth
