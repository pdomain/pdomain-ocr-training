"""Layout training over the labeler's region export."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from pdomain_ocr_training.layout_regions import load_layout_export

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_ocr_training.layout_regions import LayoutPageExample

ProgressHook = Callable[[dict[str, object]], None]


class LayoutModel(Protocol):
    """Model that trains on loaded layout pages."""

    def train_batch(self, examples: Sequence[LayoutPageExample]) -> float:
        """Train on one batch and return its loss."""
        ...

    def validate_batch(self, examples: Sequence[LayoutPageExample]) -> float:
        """Score one batch and return its loss."""
        ...

    def save(self, path: Path) -> None:
        """Write the trained checkpoint to ``path``."""
        ...


def train_layout_from_config(
    *,
    train_path: str | Path,
    val_path: str | Path,
    epochs: int,
    output_dir: str | Path,
    name: str,
    model: LayoutModel | None = None,
    progress_hook: ProgressHook | None = None,
) -> None:
    """Train ``model`` on two region exports and save ``{name}.pt``."""
    if model is None:
        raise RuntimeError(
            "Layout training does not download DocTR or PP-DocLayout weights. Pass a model."
        )
    if epochs < 1:
        raise ValueError("layout training epochs must be at least 1")
    checkpoint_name = _checkpoint_name(name)
    train_pages = load_layout_export(Path(train_path))
    val_pages = load_layout_export(Path(val_path))
    if not train_pages:
        raise ValueError(f"layout export has no pages: {train_path}")
    if not val_pages:
        raise ValueError(f"layout export has no pages: {val_path}")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, epochs + 1):
        _run_split(model.train_batch, train_pages, progress_hook, "train_batch", epoch)
        _run_split(model.validate_batch, val_pages, progress_hook, "val_batch", epoch)
        _emit(
            progress_hook,
            {
                "event": "epoch_end",
                "epoch": epoch,
                "total_epochs": epochs,
                "train_pages": len(train_pages),
                "val_pages": len(val_pages),
            },
        )
    model.save(destination / checkpoint_name)


def _run_split(
    step: Callable[[Sequence[LayoutPageExample]], float],
    pages: Sequence[LayoutPageExample],
    progress_hook: ProgressHook | None,
    event_name: str,
    epoch: int,
) -> None:
    total = len(pages)
    for index, page in enumerate(pages, start=1):
        loss = _finite_loss(step([page]))
        _emit(
            progress_hook,
            {
                "event": event_name,
                "batch": index,
                "total_batches": total,
                "loss": loss,
                "epoch": epoch,
            },
        )


def _finite_loss(loss: object) -> float:
    if isinstance(loss, bool) or not isinstance(loss, int | float) or not math.isfinite(loss):
        raise ValueError("layout batch loss must be a finite number")
    return float(loss)


def _checkpoint_name(name: str) -> str:
    if name in {"", ".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"layout checkpoint name is not a file name: {name!r}")
    return f"{name}.pt"


def _emit(progress_hook: ProgressHook | None, event: dict[str, object]) -> None:
    if progress_hook is not None:
        progress_hook(event)
