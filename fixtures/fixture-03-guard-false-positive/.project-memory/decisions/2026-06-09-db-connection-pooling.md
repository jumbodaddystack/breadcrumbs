---
id: dec_20260609_db-connection-pooling
type: decision
slug: db-connection-pooling
title: Use a bounded database connection pool
status: active
created_at: 2026-06-09T11:00:00-05:00
updated_at: 2026-06-09T11:00:00-05:00
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
  - database
  - performance
evidence:
  - type: commit
    ref: 9f8e7d6
  - type: file
    ref: src/db/pool.ts
---

## Context
Use a bounded database connection pool.

## Options Considered
Several; see rationale.

## Decision
Cap the database connection pool at 20 and reuse connections.

## Rationale
Unbounded pooling exhausted the database under load.

## Consequences
Tracked in follow-up records.

## What Not To Retry
See the related attempt record.

## Evidence
- commit 9f8e7d6

## Stale / Review Conditions
Revisit if the component contract changes.
