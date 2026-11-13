---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-11-13
---

# Intent map

## Agent Index

- **Status:** active
- **Last verified:** 2026-11-13
- **Read when:** checking deferred work, blocked work, or an owner decision.
- **Search terms:** intent map, deferred work, classifier runner, dep-refresh decision.

## Deferred work

Sequenced work lives in the [roadmap](../ROADMAP.md). The items below are
explicitly not in the current phase.

- **Synthetic typography in `pdomain-ocr-synth`.** Shared span types now live
  in Torch-free `pdomain-book-contracts`. The phase-two plan reuses that
  package instead of a local mirror. Renderer integration and dependency
  verification remain unimplemented in Task C1. Do this only after a real-scan
  baseline exists.

- **OCR and HTR comparison, in a new repository.** Compare PP-OCRv5 through
  ONNX, HTR engines, and licensed historical datasets with the current DocTR
  baseline. Require reproducible accuracy, runtime, model-size, and license
  evidence before adding another training stack. Do not put that comparison
  in this package. `pdomain-book-tools` remains the inference-integration
  candidate only after that evidence exists.

- **Optional real-dataset GPU evaluation smoke test.** The current backend is
  covered by GPU-free unit tests. Add a small real DocTR dataset smoke test only
  when a stable fixture and GPU-capable CI lane exist. Status: deferred.

- **Public-runner glyph slicing remains incomplete.** The backend already
  emits slices, but `local_eval.py` does not forward
  `slice_glyph_features` or `glyph_annotations_path`. The tests in
  `tests/test_glyph_slice_emission.py` call the backend directly.
  Relative-path keys allowed by the sidecar ADR also exceed the backend's
  basename join. Preserve the labeler writer decision; any repair needs
  runner-level and producer/consumer tests. This documentation pass does
  not authorize that code work.

## Blocked work

- **Classifier runner contract for trainer SPA.** Typeface and glyph training
  need a confirmed scope before any runner contract. If a classifier is built,
  it belongs in a separate model package. This package would add a runner
  contract only after that scope is confirmed. `pdomain-ocr-trainer-spa` would
  orchestrate it. Do not extend `detect.py` or `recog.py` for it.

## Needs owner decision

- **Close or restore the dep-refresh issue.** The issue file stays open.
  On 2026-11-06, `gh api repos/pdomain/pdomain-ocr-training/branches/master/protection`
  returned HTTP 404, "Branch not protected". `.github/workflows` is absent.
  Commit `736ebc6` deleted the CI, dep-refresh, nightly, release, and index-regen
  workflows. Its message says branch protection is off. The same day's
  `gh api repos/pdomain/pdomain-ocr-training/actions/permissions` returned
  `enabled: false`. That does not prove the August defects were fixed as the
  issue describes them. It does not prove GitHub CI should come back.
  Owner: decide whether
  [the issue](../issues/2026-08-08-dep-refresh-cannot-auto-land.md) is closed
  by that removal, or whether Actions and branch protection should be restored.

## Glyph sidecar writer

Glyph sidecar writer ownership was decided on 2026-09-18.
`pdomain-ocr-labeler-spa`'s dataset export writes the sidecar. It does that
because it is the only place a word's human glyph annotations and its
recognition crop filename exist at the same moment. The contract the producer
must honour is in
[the ADR](../decisions/2026-09-18-glyph-sidecar-writer.md). That contract
includes this rule: an absent crop means unknown rather than feature-free.

## Legacy-unverified sweep

- `docs/architecture/00-overview.md`: still active; verified against code,
  tests, and commit `4ab9a0e`.
- `docs/decisions/2026-05-21-ieval-runner-protocol.md`: still active; the
  sibling protocol remains implemented by commits `c855164` and `5960fc9`.
- `docs/process/lint-deviations.md`: still active; reconciled against current
  source and `pyproject.toml`.
- `docs/process/writing-style.md`: still active; referenced by `CLAUDE.md` and
  `CONVENTIONS.md`.
- The DocTR evaluation backend plan was implemented by commit `5960fc9` and
  retired during the 2026-07-14 migration. Current truth is in
  [`docs/architecture/00-overview.md`](../architecture/00-overview.md).
- The glyph-feature slicing design was implemented by commits `ee08319`,
  `fccc594`, and `ad904c3`, then retired during the 2026-07-14 migration.
  Current truth is in
  [`docs/architecture/00-overview.md`](../architecture/00-overview.md).
