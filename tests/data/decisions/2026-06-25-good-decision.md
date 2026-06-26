---
type: decision
title: Use repo-local Markdown as source of truth
status: active
created_at: 2026-06-25T14:30:00-05:00
updated_at: 2026-06-25T14:30:00-05:00
created_by: testuser
agent: human
project: demo
scope: project
branch: main
commit: abc1234
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
    ref: abc1234
  - type: command
    ref: npm test
---
## Context
We needed a durable, tool-independent store for project memory.

## Decision
Repo-local Markdown with YAML frontmatter is the source of truth.

## Stale / Review Conditions
Revisit if the team adopts a database-backed store.
