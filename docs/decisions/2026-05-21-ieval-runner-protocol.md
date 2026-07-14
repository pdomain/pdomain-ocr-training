---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-07-14
Kind: decision
---

# ADR: Add IEvalRunner -- sibling Protocol to ITrainingRunner

## Agent Index

- **Kind:** decision
- **Status:** active
- **Last verified:** 2026-07-14
- **Read when:** evaluating why training and evaluation use separate protocols.
- **Search terms:** IEvalRunner rationale, synchronous evaluation, torch-free eval.

**Date:** 2026-05-21
**Status:** Accepted
**Issue:** pdomain/pdomain-ocr-training#2

## Context

`ITrainingRunner` exposes only training entry points.  pdomain-ocr-trainer-spa M7
(models registry + eval) proved that the consumer needs an eval round-trip:
its `worker/evaluate.py` runs a single forward pass and returns overall metrics
plus a per-slice breakdown.  The production `_build_runner()` path raised a
clear not-implemented error because pdomain-ocr-training had no eval API.

## Decision

Add a sibling `IEvalRunner` Protocol alongside `ITrainingRunner`.  Keep
`ITrainingRunner` training-only (Single-Responsibility Principle).  Mirror the
multi-Protocol pattern from `pdomain-ocr-ops`
(`StageDispatcher` / `LongJobRunner`).

## Options considered

**Option A -- add `evaluate_detection` / `evaluate_recognition` to `ITrainingRunner`.**
Rejected: conflates two concerns (training is long-running + streaming; eval is
a single synchronous forward pass); forces all training stubs to implement eval
too.

**Option B (chosen) -- sibling `IEvalRunner` Protocol + `LocalEvalRunner` concrete.**
Keeps SRP; mirrors the workspace multi-Protocol idiom; allows training and eval
to be injected independently.

## Call model: synchronous, not streaming

Training returns `Iterator[TrainingEvent]` because it spans many epochs and
callers need to stream progress.  Eval is a single forward pass -- no epoch
loop, no progress stream needed.  `IEvalRunner` methods therefore return result
objects directly.  This avoids the thread-queue bridge machinery entirely.

## Result shape

Result objects carry fields aligned with the pdomain-ocr-trainer-spa M7 worker
shapes so the adapter mapping is trivial:

- **`RecognitionEvalResult`**: `cer`, `wer`, `exact_match_rate`, `slices`,
  `sample_count`, `excluded_count`, `duration_seconds`.
- **`DetectionEvalResult`**: `precision`, `recall`, `f1`, `iou_50`,
  `iou_50_95`, `slices`, `sample_count`, `excluded_count`, `duration_seconds`.
- **`EvalSlice`**: `feature`, `n_pos`, `n_neg`, `n_excluded`, `cer_pos`,
  `cer_neg`, `wer_pos`, `wer_neg`, `delta_cer`, `delta_wer`, `low_support`.

`slices: []` remains the default. Recognition evaluation can populate glyph
feature slices when a caller enables slicing and supplies a JSON sidecar.

## Error handling

Unlike `ITrainingRunner` (which wraps exceptions in `kind="error"` events),
`IEvalRunner` lets exceptions propagate directly.  The consumer decides how to
handle (log, surface in the API response, etc.).

## Torch-free contract

`LocalEvalRunner` imports no torch or DocTR module at module import time. Its
entry points load `_eval_backend` lazily and remain replaceable in tests. The
class is importable in the base install, unlike `LocalTrainingRunner`, whose
runtime implementation requires the training extra.

## Consequences

- `pdomain-ocr-trainer-spa` M7 can now inject a real `IEvalRunner` instead of a
  stub; the adapter maps `LocalEvalRunner.evaluate_recognition(profile, cfg)`
  to its existing result schema.
- M12 (typeface classifier) and M13 (glyph eval slicing) can populate
  `result.slices` without any Protocol changes.
- The torch-free base install now exports all eval config / result models and
  `IEvalRunner`, enabling the SPA web process to type-check eval results
  without pulling in the training stack.

## Supersedes / Superseded-by

This decision supersedes the absence of an evaluation runner contract. It has
not been superseded; current shipped behavior is documented in the
[`pdomain-ocr-training` architecture](../architecture/00-overview.md).
