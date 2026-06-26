---
id: dec_20260605_markdown-source-of-truth
type: decision
slug: markdown-source-of-truth
title: Use repo-local Markdown as the source of truth
status: active
created_at: 2026-06-05T11:00:00-05:00
updated_at: 2026-06-05T11:00:00-05:00
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
  - memory
  - architecture
evidence:
  - type: commit
    ref: 9f8e7d6
  - type: file
    ref: continuity.py
---

## Context
Use repo-local Markdown as the source of truth.

## Options Considered
Several; see rationale.

## Decision
Plain Markdown with YAML frontmatter under .project-memory/.

## Rationale
Every agent can read plain files; no vendor lock-in.

## Consequences
Tracked in follow-up records.

## What Not To Retry
See the related attempt record.

## Evidence
- commit 9f8e7d6

## Stale / Review Conditions
Revisit if the component contract changes.
