---
id: dec_20260610_markdown-source-of-truth
type: decision
slug: markdown-source-of-truth
title: Plain Markdown is the source of truth
status: active
created_at: 2026-06-10T10:00:00-05:00
updated_at: 2026-06-10T10:00:00-05:00
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

## Context
Recorded for the fixture.

## Options Considered
A few.

## Decision
Keep canonical memory as plain Markdown records.

## Rationale
A read-only cloud agent can read plain files without the CLI.

## Consequences
Documented.

## What Not To Retry
See rationale.

## Evidence
- commit a1b2c3d

## Stale / Review Conditions
Revisit if the area changes.
