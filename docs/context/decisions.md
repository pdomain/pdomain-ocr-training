---
Status: active
Owner: CT
Created: 2026-07-14
Last verified: 2026-11-07
---

# Durable decisions

## Agent Index

- **Status:** active
- **Last verified:** 2026-11-07
- **Read when:** investigating changed direction, retired documents, or durable rationale.
- **Search terms:** decisions, implementation deviations, tombstones, retirement.

### 2026-07-14 — Preserve shipped evaluation deviations in current architecture

- **Context:** The completed backend plan projected a single-threshold IoU
  approximation and reuse of `detect.evaluate()`.
- **Decision:** Keep the shipped private lazy backend and its dedicated
  detection loop with a true 0.50–0.95 COCO threshold sweep as current truth in
  [`docs/architecture/00-overview.md`](../architecture/00-overview.md).
- **Rationale:** The implementation improved metric fidelity without changing
  the torch-free boundary or synchronous runner contract.
- **Evidence:** Commit `5960fc9`; `pdomain_ocr_training/_eval_backend.py`;
  `tests/test_eval_backend.py`; `tests/test_eval_backend_wiring.py`.
- **Remaining work:** Optional real-dataset GPU smoke testing remains deferred
  in [`intent-map.md`](intent-map.md).

### 2026-07-14 — Implementation verified: Real DocTR eval backend plan

- **Old path:** `docs/archive/plans/2026-05-22-doctr-eval-backend.md`
- **Outcome:** Implementation verified; deletion is pending the doc-retirer gate.
- **Superseded by:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** Pending the doc-retirer gate.
- **Rationale kept:** This file's preceding deviation decision and the current
  architecture preserve the durable design.
- **Remaining work:** Optional GPU smoke testing is deferred in
  [`intent-map.md`](intent-map.md).

### 2026-07-14 — Implementation verified: Glyph-feature eval slicing design

- **Old path:** `docs/specs/2026-05-22-glyph-feature-eval-slicing-design.md`
- **Outcome:** Implementation verified; deletion is pending the doc-retirer gate.
- **Superseded by:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** Pending the doc-retirer gate.
- **Rationale kept:** The architecture preserves the serialized dependency
  boundary, basename crop-id join, and slice semantics.
- **Remaining work:** Sidecar-writer ownership remains a needs-owner-decision
  item in [`intent-map.md`](intent-map.md).

### 2026-07-14 — Retirement completed: Real DocTR eval backend plan

- **Context:** The prior entry recorded verified implementation while the
  retirement gate was pending. This entry supersedes that pending state.
- **Old path:** `docs/archive/plans/2026-05-22-doctr-eval-backend.md`
- **Outcome:** Implemented and deleted after promotion.
- **Replacement:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** The retirement commit containing this entry; use
  `git log -- docs/archive/plans/2026-05-22-doctr-eval-backend.md`.
- **Retained rationale:** The current architecture and the evaluation-deviation
  decision above preserve the torch-free boundary and true COCO sweep.
- **Rationale:** The plan contained no other unique durable content; its
  execution checklist would add stale retrieval noise.
- **Evidence:** Commit `5960fc9`; [`docs/architecture/00-overview.md`](../architecture/00-overview.md);
  `tests/test_eval_backend.py`; `tests/test_eval_backend_wiring.py`.
- **Remaining work:** Optional GPU smoke testing remains deferred.

### 2026-07-14 — Retirement completed: Glyph-feature eval slicing design

- **Context:** The prior entry recorded verified implementation while the
  retirement gate was pending. This entry supersedes that pending state.
- **Old path:** `docs/specs/2026-05-22-glyph-feature-eval-slicing-design.md`
- **Outcome:** Implemented and deleted after promotion.
- **Replacement:** [`docs/architecture/00-overview.md`](../architecture/00-overview.md)
- **Removal commit:** The retirement commit containing this entry; use
  `git log -- docs/specs/2026-05-22-glyph-feature-eval-slicing-design.md`.
- **Retained rationale:** A serialized sidecar avoids a direct
  `pdomain-book-tools` dependency, and basename crop-id keying prevents slice
  misalignment when validation samples are filtered or reordered. The intent
  map preserves the unresolved upstream writer ownership.
- **Rationale:** Code, tests, and current architecture preserve the shipped
  contract without retaining speculative design scaffolding.
- **Evidence:** Commits `ee08319`, `fccc594`, and `ad904c3`;
  [`docs/architecture/00-overview.md`](../architecture/00-overview.md);
  `tests/test_glyph_slice_emission.py`.
- **Remaining work:** Decide upstream glyph sidecar writer ownership.

### 2026-11-07 — Code validation of the existing decisions

- The evaluation backend still uses the 0.50–0.95 IoU threshold sweep and lazy
  imports. The local suite passed all 139 tests today.
- The September 18 [glyph-sidecar ADR](../decisions/2026-09-18-glyph-sidecar-writer.md)
  resolved the writer question left open in the July entries. The labeler's
  `core/jobs/handlers/glyph_sidecar.py` writes reviewed-word entries; training's
  `_eval_backend._emit_glyph_slices` consumes them and excludes missing crops.
- The July entries remain historical records. Their pending writer item is
  superseded by that existing ADR.

### 2026-11-09 Retired: Fine-grained typography phase-one handoff (2026-08-21)

- Old path: `docs/handoff/2026-08-21-115334-fine-grained-typography-phase-one.md`
- Outcome: superseded
- Superseded by: the [typography model design](../specs/2026-08-21-fine-grained-typography-model-design.md),
  [current state](current-state.md) and [intent map](intent-map.md)
- Removal commit: `3ae6a925`
- Rationale kept: Phase one shipped. `pdomain-book-contracts` holds the typography types and the F2
  tokenizer, parser and project rules, released v0.1.0 through v0.3.0. `pdomain-source-data` exists,
  and the labeler implements typography review. The design spec records the handoff's decisions and
  rejected approaches. That covers per-field fusion, the four label states and model ordering.
- Remaining work: training and synthesis, already in current state and the intent map
