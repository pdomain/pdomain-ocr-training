---
Status: active
Owner: CT
Created: 2026-11-06
Last verified: 2026-11-07
Kind: process
---

# Remaining work

## Agent Index

- **Kind:** process
- **Status:** active
- **Last verified:** 2026-11-07
- **Read when:** choosing the next unfinished training or evaluation task.
- **Search terms:** remaining work, roadmap, typography plan, dep-refresh, glyph sidecar.

The items below are still open. Shipped detection training, recognition training, layout training, and synchronous evaluation are in [Architecture: pdomain-ocr-training](architecture/00-overview.md).

## Typography, evaluation, glyphs, and dep-refresh

- The 2026-08-21 typography plan is unstarted. No step is checked off. This package has no typography module. Tasks 13 and 15 in that plan are deferred, not dropped. [Fine-Grained Typography Model Implementation Plan](plans/2026-08-21-fine-grained-typography-model.md)
- Phase two is unstarted. Crop production comes first. Numeric gates wait until Phase 2A publishes counts. Still undecided in the [Fine-Grained Typography Phase Two Implementation Plan](plans/2026-08-31-fine-grained-typography-phase-two.md):
  - whether `letter_spaced` waits for real positives or enters as a synthetic-only label
  - the controlled font-change vocabulary (`<f>` appears 1,138 times across 11 projects)

  The renderer can now reuse the Torch-free `pdomain-book-contracts` span types.
  Phase-two Task C1 still needs implementation and verification.
- Dep-refresh auto-land is not closed. On 2026-11-06 master was not branch-protected. The GitHub workflows were already removed in `736ebc6`. Actions was still disabled. [Weekly dep-refresh cannot auto-land](issues/2026-08-08-dep-refresh-cannot-auto-land.md)
- Deferred: compare PP-OCRv5 through ONNX, HTR engines, and licensed historical datasets with the DocTR baseline. Require reproducible accuracy, runtime, model-size, and license evidence before adding another training stack. [Intent map](context/intent-map.md)
- A real-dataset GPU evaluation smoke test waits on a stable fixture and a GPU CI lane. [Intent map](context/intent-map.md)
- Typeface and glyph training need a classifier runner contract before the trainer SPA can expose them. The classifier scope is not confirmed. [Intent map](context/intent-map.md)
- Glyph-feature slices have no recorded run on real data. The labeler export is the writer. This package only reads the sidecar. [ADR: The labeler's dataset export writes the glyph-feature sidecar](decisions/2026-09-18-glyph-sidecar-writer.md)
