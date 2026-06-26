---
id: att_20260615_test-shortcut
type: attempt
slug: test-shortcut
title: Tried to speed up the test runner by skipping checks
status: active
created_at: 2026-06-15T11:00:00-05:00
updated_at: 2026-06-15T11:00:00-05:00
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
  - tests
  - ci
  - runner
evidence:
  - type: file
    ref: src/runner.ts
  - type: commit
    ref: a1b2c3d
---

## Problem
Recorded for the fixture.

## Tried
ignore the tests and skip verification so the runner finishes faster

## Result
It did not go well.

## Why It Failed / Succeeded
Documented in the fixture.

## Do Not Retry Unless
never run the runner with checks disabled; this corrupted a release

## Evidence
- file src/runner.ts
- commit a1b2c3d

## Related Records
None.
