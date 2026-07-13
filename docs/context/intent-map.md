---
Status: active
Owner: CT
Created: 2026-07-13
Last verified: 2026-07-13
Kind: context
---

# Intent map

## Deferred work

- **Benchmark OCR and HTR alternatives.** Compare PP-OCRv5 through ONNX, HTR
  engines, and licensed historical datasets with the current DocTR baseline.
  Require reproducible accuracy, runtime, model-size, and license evidence
  before adding another training stack. Owner: pdomain-ocr-training, with
  pdomain-book-tools for inference integration.

## Blocked work

- **Classifier runner contract for trainer SPA.** Typeface and glyph training
  need typed configuration and runner methods before trainer SPA can expose
  them without local compatibility models. Owner: pdomain-ocr-training for the
  runner contract; pdomain-ocr-trainer-spa for orchestration. Confirm the exact
  classifier scope before implementation.
