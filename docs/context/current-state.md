---
Status: active
Owner: CT
Created: 2026-07-14
Last verified: 2026-11-13
---

# Current state

## Agent Index

- **Status:** active
- **Last verified:** 2026-11-13
- **Read when:** starting repository work or checking current operational risk.
- **Search terms:** current state, CI, OCR training, active risks.

## Risks: glyph-feature slices and dep-refresh

Glyph-feature slices still have no recorded run on real data. The labeler dataset
export is the sidecar writer. That was decided on 2026-09-18. The contract is in
[the ADR](../decisions/2026-09-18-glyph-sidecar-writer.md).

The backend's slice support is not wired through `LocalEvalRunner`:
`local_eval.py` drops `slice_glyph_features` and `glyph_annotations_path`
when rebuilding the configuration. Sidecar keys must also match the
backend's basename crop IDs. The
[architecture overview](../architecture/00-overview.md#ievalrunner) records
both limits. Existing slice tests exercise the backend directly.

The dep-refresh issue is not closed. On 2026-11-06 master was not branch-protected.
The GitHub workflows were already removed. Actions was still disabled. See
[dep-refresh cannot auto-land](../issues/2026-08-08-dep-refresh-cannot-auto-land.md).

## No formatting model is in this package

This package has no formatting module. Crop production has not started. The
August 21 plan is historical. The execution checklist is the phase-two plan,
and the ordered list is the [roadmap](../ROADMAP.md). Ownership is in
[Where training work lives](../architecture/suite-boundaries.md).

## Last recorded full make ci passed

The latest full `make ci` passed on 2026-11-07: hooks, formatting, Ruff,
basedpyright, and all 139 tests. The previous recorded run on 2026-07-14 passed
129 tests. No later red or flaky test is recorded here.

On 2026-11-07, a code-validation pass ran `uv run pytest -q -n 2`: all
139 tests passed. That was a test-suite run, not a full `make ci` run.
The import tests confirm that the public API does not load Torch. They do not
prove a lightweight installation: `uv.lock` shows Torch and DocTR coming through
the required `pdomain-book-tools` dependency.

## The local gate now uses just

Commit `3c0a88a` removed the Make shim after `c2d8708` added the justfile.
Both `just ci` and `AI=1 just ci` passed 156 tests, build, hooks,
typechecking, and strict docgraph during that migration on 2026-11-13.
The architecture-review worktree also passed the 156-test suite before
documentation edits. Those tests do not establish real-data GPU evaluation.

## Shipped work and the open list

Shipped detection training, recognition training, layout training, and synchronous
evaluation are in [Architecture: pdomain-ocr-training](../architecture/00-overview.md).
Layout training reads the labeler's `regions/labels.json` export and optional
reviewed `regions/structure.json` records, added in `5c5b835`. Open items are
the [roadmap](../ROADMAP.md). On 2026-11-12, `pdomain-source-data` `align_page`
still projects styles onto supplied words and does not write pixel crops.
