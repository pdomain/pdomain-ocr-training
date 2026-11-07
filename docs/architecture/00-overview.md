---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-11-07
Kind: architecture
---

# Architecture: pdomain-ocr-training

## Agent Index

- **Kind:** architecture
- **Status:** active
- **Last verified:** 2026-11-07
- **Read when:** understanding shipped training, evaluation, and torch-free boundaries.
- **Search terms:** OCR training architecture, DocTR evaluation, runner protocols, glyph slices.

**Status:** Validated against code and the local test suite on 2026-11-07.

## Purpose

`pdomain-ocr-training` owns the reusable torch/DocTR OCR model-training and
evaluation implementation for the `pdomain-*` suite. It keeps configuration,
event, and runner contracts importable without loading Torch. The training extra
declares the heavy runtime, but the required `pdomain-book-tools` dependency also
installs it transitively. Consumers use those typed contracts at their boundaries.
The trainer SPA's worker also instantiates `LocalTrainingRunner` as its concrete
local implementation; torch remains outside the long-lived web process.

## Module layout

```text
pdomain_ocr_training/
    __init__.py      Public API re-exports (lazy for LocalTrainingRunner)
    protocols.py     ITrainingRunner + IEvalRunner Protocols; all config + result models
    local.py         LocalTrainingRunner — callback→generator bridge
    local_eval.py    LocalEvalRunner — synchronous eval wrapper
    _eval_backend.py Real DocTR detection and recognition evaluation
    detect.py        Verbatim-moved DocTR detection training (legacy; per-file-ignores)
    recog.py         Verbatim-moved DocTR recognition training (legacy; per-file-ignores)
    layout_regions.py  Reader for the labeler's regions/labels.json export
    layout.py        Layout training loop; the caller supplies the model
    datasets.py      ExportManager — on-disk dataset layout manager (legacy)
    utils.py         Shared training utilities (legacy)
```

## Install modes

```bash
pip install pdomain-ocr-training          # Base API; heavy transitive dependencies
pip install 'pdomain-ocr-training[train]' # Explicit training dependencies
```

The base API exposes all typed models, three runner Protocols, and `LocalEvalRunner`.
`LocalTrainingRunner` is available lazily — `import pdomain_ocr_training` never
imports torch; accessing `LocalTrainingRunner` without the training dependencies raises a clear
`ImportError`. The import tests block Torch and DocTR to validate that boundary;
they do not prove that dependency installation excludes those packages. The
base package's `pdomain-book-tools` dependency includes them in `uv.lock`.

## Protocols

### ITrainingRunner

Training is long-running and streams progress across many epochs. The Protocol
returns `Iterator[TrainingEvent]`. `LocalTrainingRunner` bridges the legacy
DocTR callback-style training loops into that iterator via a thread + Queue.

```text
pdomain-ocr-trainer-spa                pdomain-ocr-training
─────────────────       inject        ─────────────────────
ITrainingRunner  ◄──────────────── LocalTrainingRunner
                                        │
                                    thread bridge
                                        │
                                   detect.main() / recog.main()
```

Supported methods:

- `train_detection(profile, config) -> Iterator[TrainingEvent]`
- `train_recognition(profile, config) -> Iterator[TrainingEvent]`

`ILayoutTrainingRunner` is a separate protocol. An existing detection and
recognition runner stays an `ITrainingRunner`. The layout protocol has one method:

- `train_layout(profile, config) -> Iterator[TrainingEvent]`

`train_layout` reads `regions/labels.json` from a labeler export directory.
Each page's image is `detection/images/{prefix}_{page_index}.png` in that
same directory. The caller passes the model. The run does not download
DocTR or PP-DocLayout weights.

### IEvalRunner

Eval is a single synchronous forward pass — no epoch loop, no progress stream.
The Protocol returns result objects directly. `LocalEvalRunner` delegates to
real DocTR evaluation entry points that remain replaceable in tests.

```text
pdomain-ocr-trainer-spa                pdomain-ocr-training
─────────────────       inject        ─────────────────────
IEvalRunner      ◄──────────────── LocalEvalRunner
                                        │
                                   evaluate_detection_from_config()
                                   evaluate_recognition_from_config()
```

Supported methods:

- `evaluate_detection(profile, config) -> DetectionEvalResult`
- `evaluate_recognition(profile, config) -> RecognitionEvalResult`

The entry points load DocTR predictors, evaluate detection or recognition data,
and return typed results. Recognition evaluation can load a glyph-feature JSON
sidecar when the caller enables slicing. It joins sidecar entries to validation
samples by basename crop id and emits one `EvalSlice` for `long_s`, `swash`,
and each distinct `ligature:<kind>`. Samples without sidecar data are excluded
from positive and negative denominators. CER and WER deltas are null when
either side is empty, and a slice has low support when its positive count is
less than 30.

## Config and result models

All models live in `protocols.py` and are Pydantic v2 `BaseModel`s.

**Training:**

- `DetectionConfig` — train/val paths + DocTR hyperparameters
- `RecognitionConfig` — train/val paths + DocTR hyperparameters
- `LayoutConfig` — train/val export directories for layout training
- `TrainingEvent` — streaming event (`kind`, `message`, optional metrics)

**Eval:**

- `DetectionEvalConfig` — val path, model checkpoint path
- `RecognitionEvalConfig` — val path, model checkpoint path
- `DetectionEvalResult` — precision, recall, f1, IoU metrics, slices
- `RecognitionEvalResult` — CER, WER, exact-match rate, slices
- `EvalSlice` — per-feature recognition breakdown; detection slices remain empty
- `GlyphFeatureSet` — torch-free recognition-crop metadata for glyph slicing

## Shipped evaluation evidence

- Code: `pdomain_ocr_training/local_eval.py`,
  `pdomain_ocr_training/_eval_backend.py`,
  `pdomain_ocr_training/protocols.py`
- Tests: `tests/test_eval_backend_wiring.py`,
  `tests/test_glyph_slice_emission.py`, `tests/test_eval_protocols.py`
- Verified: 2026-11-07 against the current source and the local test suite

## Legacy modules

`detect.py`, `recog.py`, `datasets.py`, and `utils.py` are verbatim moves from
the legacy `pd-ocr-trainer` repo. They carry per-file-ignores in `pyproject.toml`
(`ANN`, `D`, `BLE`, `S`, plus several additional families for `detect.py` /
`recog.py`) pending an annotation follow-up pass. Do not rewrite them as part
of unrelated tasks.

## Error handling

- `ITrainingRunner`: exceptions are wrapped in `kind="error"` `TrainingEvent`s
  so the streaming caller always gets a clean iterator.
- `IEvalRunner`: exceptions propagate directly. The consumer decides how to
  surface them (API error response, log, etc.).

## ADRs

- [`IEvalRunner` protocol decision](../decisions/2026-05-21-ieval-runner-protocol.md)
  — rationale for a sibling Protocol rather than extending `ITrainingRunner`.
