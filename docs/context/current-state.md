---
Status: active
Owner: CT
Created: 2026-07-14
Last verified: 2026-11-07
---

# Current state

## Agent Index

- **Status:** active
- **Last verified:** 2026-11-07
- **Read when:** starting repository work or checking current operational risk.
- **Search terms:** current state, CI, OCR training, active risks.

## Risks: glyph-feature slices and dep-refresh

Glyph-feature slices still have no recorded run on real data. The labeler dataset
export is the sidecar writer. That was decided on 2026-09-18. The contract is in
[the ADR](../decisions/2026-09-18-glyph-sidecar-writer.md).

The dep-refresh issue is not closed. On 2026-11-06 master was not branch-protected.
The GitHub workflows were already removed. Actions was still disabled. See
[dep-refresh cannot auto-land](../issues/2026-08-08-dep-refresh-cannot-auto-land.md).

## No typography or formatting work is in flight

No typography or formatting implementation is in this package. The two typography
plans remain drafts with every step unchecked.

## Last recorded full make ci passed

The latest full `make ci` passed on 2026-11-07: hooks, formatting, Ruff,
basedpyright, and all 139 tests. The previous recorded run on 2026-07-14 passed
129 tests. No later red or flaky test is recorded here.

On 2026-11-07, a code-validation pass ran `uv run pytest -q -n 2`: all
139 tests passed. That was a test-suite run, not a full `make ci` run.
The import tests confirm that the public API does not load Torch. They do not
prove a lightweight installation: `uv.lock` shows Torch and DocTR coming through
the required `pdomain-book-tools` dependency.

## Shipped work and the open list

Shipped detection training, recognition training, layout training, and synchronous
evaluation are in [Architecture: pdomain-ocr-training](../architecture/00-overview.md).
Layout training reads the labeler's `regions/labels.json` export. Open items are
the [remaining-work list](../ROADMAP.md).
