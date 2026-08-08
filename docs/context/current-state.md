---
Status: active
Owner: CT
Created: 2026-07-14
Last verified: 2026-08-08
---

# Current state

## Agent Index

- **Status:** active
- **Last verified:** 2026-08-08
- **Read when:** starting repository work or checking current operational risk.
- **Search terms:** current state, CI, OCR training, active risks.

## What matters now

The package ships DocTR detection and recognition training plus synchronous
evaluation behind the optional `train` extra. The public configuration and
runner contracts remain torch-free. See
[`docs/architecture/00-overview.md`](../architecture/00-overview.md).

## In-flight work

No product implementation is recorded as in flight. Documentation lifecycle
metadata and retrieval governance are active.

## Test health

The 2026-07-14 baseline `make ci` run passed all hooks, Ruff, basedpyright, and
129 tests. No red or flaky test is recorded.

## Current risks

The upstream owner of the glyph-feature sidecar remains undecided. The contract
and required key format are recorded in [`intent-map.md`](intent-map.md).

Master branch protection requires status contexts that predate the repo's
rename from `pd-ocr-training` to `pdomain-ocr-training`, so no pull request —
including the weekly `dep-refresh` PR — can merge. See
[dep-refresh cannot auto-land](../issues/2026-08-08-dep-refresh-cannot-auto-land.md).
