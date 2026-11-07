---
Status: active
Owner: CT
Created: 2026-05-21
Last verified: 2026-11-07
---

# pdomain-ocr-training

Repository guidance starts at [`AGENTS.md`](AGENTS.md). Current system behavior
is in [`docs/architecture/00-overview.md`](docs/architecture/00-overview.md),
with documentation navigation in [`docs/README.md`](docs/README.md) and release
history in [`CHANGELOG.md`](CHANGELOG.md).

DocTR OCR model training and evaluation pipeline for the `pdomain-*` OCR suite.

This package owns detection and recognition model fine-tuning, layout training, dataset management, model export, and evaluation. Its public configuration and runner interfaces import without loading Torch, so a web process can use those interfaces without loading the training runtime.

Supersedes the legacy `pd-ocr-trainer` repo.

## Install modes

The heavy training stack (torch / DocTR / matplotlib) is declared in the
`train` optional extra. However, the required `pdomain-book-tools` dependency
also installs that stack, as recorded in `uv.lock`. The base API imports without
loading Torch; the base installation is not free of Torch dependencies.

```bash
# Base API — imports without loading Torch. Exposes config models, ITrainingRunner,
# IEvalRunner, and LocalEvalRunner. Use this in a long-lived web process
# (e.g. pdomain-ocr-trainer-spa) that injects the runners but does not train.
pip install pdomain-ocr-training

# Explicit training extra — declares torch / DocTR / matplotlib and makes
# LocalTrainingRunner usable. Use this in the training worker process.
pip install 'pdomain-ocr-training[train]'
```

## Protocols and concrete runners

Three runner Protocols have concrete implementations:

| Protocol | Concrete | Install mode |
|---|---|---|
| `ITrainingRunner` | `LocalTrainingRunner` | training dependencies required; declared by `[train]` |
| `ILayoutTrainingRunner` | `LocalTrainingRunner` with a caller-supplied `LayoutModel` | training dependencies required to import the runner |
| `IEvalRunner` | `LocalEvalRunner` | base API; `[train]` dependencies required when evaluation runs |

`LocalTrainingRunner` is exported lazily — importing `pdomain_ocr_training` does
**not** load torch. Accessing it when training dependencies are unavailable raises a clear
`ImportError`. `LocalEvalRunner` is importable in the base install. Its real
evaluation entry points load DocTR only when evaluation runs, so callers need
the `[train]` dependencies for an actual evaluation.

### Torch-free usage (config models + Protocols)

```python
from pdomain_ocr_training import (
    DetectionConfig,
    DetectionEvalConfig,
    IEvalRunner,
    ITrainingRunner,
    LocalEvalRunner,
    RecognitionConfig,
    RecognitionEvalConfig,
    TrainingEvent,
)


# Type dependency-injection seams without importing torch:
def run_training(runner: ITrainingRunner, cfg: DetectionConfig) -> None:
    for event in runner.train_detection("my-run", cfg):
        print(event.kind, event.message)


def run_eval(runner: IEvalRunner, cfg: RecognitionEvalConfig) -> None:
    result = runner.evaluate_recognition("eval-001", cfg)
    print(f"CER: {result.cer:.4f}  WER: {result.wer:.4f}")
```

### Full training usage (`[train]` extra)

```python
from pdomain_ocr_training import DetectionConfig, ITrainingRunner, LocalTrainingRunner

runner: ITrainingRunner = LocalTrainingRunner()
cfg = DetectionConfig(train_path="data/train", val_path="data/val")
for event in runner.train_detection("my-run", cfg):
    print(event.kind, event.message)
```

### Layout training usage (`[train]` extra)

Layout training reads schema `pdomain.layout-regions` version 1 from each export's
`regions/labels.json`. It pairs pages with `detection/images/{prefix}_{page_index}.png`
from the same export and fails if an image is missing. The caller supplies a model
that implements `LayoutModel.train_batch`, `validate_batch`, and `save`.

```python
from pdomain_ocr_training import (
    ILayoutTrainingRunner,
    LayoutConfig,
    LayoutModel,
    LocalTrainingRunner,
)


def run_layout(model: LayoutModel) -> None:
    runner: ILayoutTrainingRunner = LocalTrainingRunner(layout_model=model)
    cfg = LayoutConfig(train_path="exports/train", val_path="exports/val")
    for event in runner.train_layout("layout-run", cfg):
        print(event.kind, event.message)
```

The task saves the supplied model's checkpoint. It does not download model weights.

### Eval usage

```python
from pdomain_ocr_training import IEvalRunner, LocalEvalRunner, RecognitionEvalConfig

runner: IEvalRunner = LocalEvalRunner()
cfg = RecognitionEvalConfig(val_path="data/val", model_path="checkpoints/best.pt")
result = runner.evaluate_recognition("eval-001", cfg)
```

Recognition evaluation also supports an optional glyph-feature sidecar. It
emits typed slices for ligatures, long s, and swashes without importing torch
into the protocol models.
