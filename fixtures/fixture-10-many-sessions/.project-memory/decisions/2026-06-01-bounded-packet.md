---
id: dec_20260601_bounded-packet
type: decision
slug: bounded-packet
title: The resume packet is hard-bounded
status: active
created_at: 2026-06-01T10:00:00-05:00
updated_at: 2026-06-01T10:00:00-05:00
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
  - resume
  - bounding
evidence:
  - type: commit
    ref: a1b2c3d
---

## Context
Recorded for the fixture.

## Options Considered
A few.

## Decision
Cap the resume packet at 5,000 tokens and prioritise current/handoff/active decisions.

## Rationale
A packet that grows with history stops being paste-anywhere; bound it.

## Consequences
Documented.

## What Not To Retry
See rationale.

## Evidence
- commit a1b2c3d

## Stale / Review Conditions
Revisit if the area changes.
