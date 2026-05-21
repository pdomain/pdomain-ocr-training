# CLAUDE — pd-ocr-training

DocTR OCR model training pipeline (detection + recognition) for the `pd-*`
suite. Extracted from the legacy `pd-ocr-trainer` repo.

## Why a separate package

`torch` and `DocTR` are heavy ML dependencies. Isolating them here keeps every
other `pd-*` SPA backend torch-free. Only the future `pd-ocr-trainer-spa`
depends on this package.

## Package layout

```text
pd_ocr_training/
    __init__.py      # Public API re-exports
    protocols.py     # ITrainingRunner Protocol + TrainingEvent / DetectionConfig / RecognitionConfig
    local.py         # LocalTrainingRunner — callback→iterator bridge (strict-lint-compliant)
    detect.py        # Verbatim-moved DocTR detection training (legacy; per-file-ignores active)
    recog.py         # Verbatim-moved DocTR recognition training (legacy; per-file-ignores active)
    datasets.py      # ExportManager (legacy; per-file-ignores active)
    utils.py         # Shared training utilities (legacy; per-file-ignores active)
```

`detect.py`, `recog.py`, `datasets.py`, and `utils.py` are verbatim moves from
the legacy repo. They carry `ANN`, `D`, `BLE`, and `S` per-file-ignores in
`pyproject.toml` pending an annotation follow-up pass. `protocols.py` and
`local.py` are new, strict-lint-compliant code.

## Ops-style contract

Consumers depend on the `ITrainingRunner` Protocol, not the concrete modules:

```python
from pd_ocr_training import ITrainingRunner, LocalTrainingRunner, DetectionConfig

runner: ITrainingRunner = LocalTrainingRunner()
cfg = DetectionConfig(train_path="data/train", val_path="data/val")
for event in runner.train_detection("my-run", cfg):
    print(event.kind, event.message)
```

## Dev commands

```bash
make setup          # uv sync --group dev + install pre-commit hooks
make lint           # ruff check --fix
make lint-check     # ruff format --check + ruff check (CI-exact, no fix)
make format         # ruff format pd_ocr_training tests
make typecheck      # basedpyright pd_ocr_training --level error
make test           # uv run pytest -n auto
make ci             # setup → pre-commit → lint-check → typecheck → test
make build          # uv build
make clean          # rm dist .venv .pytest_cache .ruff_cache .ci-ai.log htmlcov
```

Run any command with `uv run` directly if preferred:

```bash
uv run pytest tests/ -v
uv run ruff check .
uv run basedpyright pd_ocr_training --level error
```

## docs/ folder

This repo follows the workspace docs/ template — see [`docs/README.md`](docs/README.md). Active
folders: `architecture/`, `decisions/`, `plans/`, `process/`, `research/`,
`runbooks/`, `specs/`, `templates/`, `usage/`, plus parallel `archive/`
subfolders.

**Superpowers redirect.** When a superpowers skill (e.g. `brainstorming`,
`writing-plans`) instructs you to save to `docs/superpowers/specs/<file>.md`
or `docs/superpowers/plans/<file>.md`, save to `docs/specs/<file>.md` or
`docs/plans/<file>.md` instead. There is no `docs/superpowers/` subdirectory
in this repo.
