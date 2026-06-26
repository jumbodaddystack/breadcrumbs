---
id: dec_20260510_markdown-source-of-truth
type: decision
slug: markdown-source-of-truth
title: Use repo-local Markdown as the source of truth
status: active
created_at: 2026-05-10T11:00:00-05:00
updated_at: 2026-05-10T11:00:00-05:00
created_by: alex
agent: human
project: demo-service
scope: project
branch: main
commit: 9f8e7d6
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
  - architecture
evidence:
  - type: commit
    ref: 9f8e7d6
---

## Context
Needed a tool-independent store that agents and humans can both read.

## Options Considered
Markdown + YAML frontmatter, a SQLite database, a single-vendor memory feature.

## Decision
Plain Markdown with YAML frontmatter under `.project-memory/`.

## Rationale
Every agent can read plain files; git reviews them; there is no vendor lock-in.

## Consequences
Search needs a later disposable index; that is an acceptable tradeoff.

## What Not To Retry
Do not move the source of truth into a binary database.

## Evidence
- commit 9f8e7d6

## Stale / Review Conditions
Revisit if record volume makes plain-file scans too slow.
