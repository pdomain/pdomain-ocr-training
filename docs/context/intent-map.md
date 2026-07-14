---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-14
---

# Intent map

## Deferred work

- **Benchmark OCR and HTR alternatives.** Compare PP-OCRv5 through ONNX, HTR
  engines, and licensed historical datasets with the current DocTR baseline.
  Require reproducible accuracy, runtime, model-size, and license evidence
  before adding another training stack. Owner: pdomain-ocr-training, with
  pdomain-book-tools for inference integration.

- **Optional real-dataset GPU evaluation smoke test.** The current backend is
  covered by GPU-free unit tests. Add a small real DocTR dataset smoke test only
  when a stable fixture and GPU-capable CI lane exist. Status: deferred.

## Blocked work

- **Classifier runner contract for trainer SPA.** Typeface and glyph training
  need typed configuration and runner methods before trainer SPA can expose
  them without local compatibility models. Owner: pdomain-ocr-training for the
  runner contract; pdomain-ocr-trainer-spa for orchestration. Confirm the exact
  classifier scope before implementation.

## Needs owner decision

- **Glyph sidecar writer ownership.** Decide whether dataset export or the
  trainer SPA writes the glyph-feature JSON sidecar. Either producer must use
  basenames matching DocTR validation labels. Evidence:
  `pdomain_ocr_training/_eval_backend.py`, `tests/test_glyph_slice_emission.py`,
  and commits `fccc594` and `ad904c3`.

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
