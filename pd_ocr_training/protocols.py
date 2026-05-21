"""Training runner Protocol and supporting data models for pd-ocr-training.

Design rationale
----------------
The ``ITrainingRunner`` Protocol mirrors the workspace idiom established in
``pd-ocr-ops`` (see ``pd_ocr_ops.gpu.protocols``): a ``@runtime_checkable``
``Protocol`` defines the contract; a ``Local*`` implementation ships
separately (Task 6) so consumer apps depend only on the interface.

Config-type decision
--------------------
The existing entry points in ``detect.py`` and ``recog.py`` already expose
stable, well-documented keyword-argument surfaces via ``detect_from_config``
and ``train_from_config``.  We capture these as typed pydantic ``BaseModel``
classes (``DetectionConfig`` / ``RecognitionConfig``) rather than raw
``dict[str, object]`` because:

1. Typed models give IDE completion and inline validation.
2. The parameter shapes are stable (no dynamic keys).
3. Pydantic v2 is already a workspace dependency (used throughout pd-ocr-ops).

The two configs are intentionally separate because the tasks have different
required parameters: detection uses ``rotation`` and ``input_size=1024``;
recognition uses ``vocab`` and ``input_size=32``.

Progress design
---------------
``ITrainingRunner`` methods return ``Iterator[TrainingEvent]`` so that callers
can consume events synchronously via a ``for`` loop.  ``LocalTrainingRunner``
(Task 6) will implement this by bridging the existing callback-style
``progress_hook`` into a thread-safe queue and draining it as a generator.

The ``from __future__ import annotations`` import is intentionally absent here
because ``runtime_checkable`` Protocol isinstance() checks require the method
names to be inspectable at runtime without string-form annotations.
"""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 — pydantic requires Path at model-build time
from typing import TYPE_CHECKING, runtime_checkable

from pydantic import BaseModel, Field
from typing_extensions import Protocol

if TYPE_CHECKING:
    from collections.abc import Iterator


# ---------------------------------------------------------------------------
# Progress event
# ---------------------------------------------------------------------------


class TrainingEvent(BaseModel):
    """A single progress event emitted during a training run.

    Attributes:
        kind: Event category.  One of ``"log"``, ``"epoch"``, ``"metric"``,
            ``"done"``, or ``"error"``.
        message: Human-readable description of the event.
        progress: Optional normalized progress in ``[0.0, 1.0]``; present on
            ``"epoch"`` and ``"done"`` events.
        data: Optional structured payload (e.g. loss, lr, recall values).
    """

    kind: str
    message: str
    progress: float | None = None
    data: dict[str, object] | None = None


# ---------------------------------------------------------------------------
# Typed training config models
# ---------------------------------------------------------------------------


class DetectionConfig(BaseModel):
    """Configuration for a detection training run.

    Maps directly onto the parameters of ``detect.detect_from_config``.

    Attributes:
        train_path: Path to the training data folder (must contain
            ``images/`` and ``labels.json``).
        val_path: Path to the validation data folder (same layout).
        arch: DocTR detection architecture name, e.g. ``"db_resnet50"``.
        epochs: Number of training epochs.
        batch_size: Training batch size.
        lr: Initial learning rate.
        weight_decay: L2 weight-decay coefficient.
        optimizer: Optimizer name; one of ``"adam"`` or ``"adamw"``.
        scheduler: LR scheduler; one of ``"cosine"``, ``"onecycle"``,
            or ``"poly"``.
        input_size: Square input image size in pixels (height == width).
        rotation: Whether to train with rotated bounding-box polygons.
        workers: Number of DataLoader worker processes.
        amp: Enable PyTorch Automatic Mixed Precision.
        early_stop: Enable early stopping.
        early_stop_epochs: Patience (epochs without improvement) before
            stopping.
        early_stop_delta: Minimum improvement delta for early stopping.
        output_dir: Directory where model checkpoints are written.
        device: GPU device index; ``None`` selects the default device.
        pretrained: Initialise from pretrained weights before fine-tuning.
        name: Experiment name used as the checkpoint filename stem.
    """

    train_path: str | Path
    val_path: str | Path
    arch: str = "db_resnet50"
    epochs: int = 100
    batch_size: int = 2
    lr: float = 0.002
    weight_decay: float = 0.0
    optimizer: str = "adam"
    scheduler: str = "poly"
    input_size: int = 1024
    rotation: bool = False
    workers: int = 4
    amp: bool = False
    early_stop: bool = False
    early_stop_epochs: int = 5
    early_stop_delta: float = 0.01
    output_dir: str | Path = Field(default=".")
    device: int | None = None
    pretrained: bool = True
    name: str | None = None


class RecognitionConfig(BaseModel):
    """Configuration for a recognition training run.

    Maps directly onto the parameters of ``recog.train_from_config``.

    Attributes:
        train_path: Path to the training data folder.
        val_path: Path to the validation data folder.
        arch: DocTR recognition architecture name, e.g. ``"crnn_vgg16_bn"``.
        epochs: Number of training epochs.
        batch_size: Training batch size.
        lr: Initial learning rate.
        weight_decay: L2 weight-decay coefficient.
        optimizer: Optimizer name; one of ``"adam"`` or ``"adamw"``.
        scheduler: LR scheduler; one of ``"cosine"``, ``"onecycle"``,
            or ``"poly"``.
        input_size: Input image height in pixels (width is ``4 * input_size``).
        vocab: Vocabulary name (e.g. ``"french"``, ``"english"``) or
            ``"CUSTOM:<chars>"`` for a custom character set.
        workers: Number of DataLoader worker processes.
        amp: Enable PyTorch Automatic Mixed Precision.
        early_stop: Enable early stopping.
        early_stop_epochs: Patience (epochs without improvement) before
            stopping.
        early_stop_delta: Minimum improvement delta for early stopping.
        output_dir: Directory where model checkpoints are written.
        device: GPU device index; ``None`` selects the default device.
        pretrained: Initialise from pretrained weights before fine-tuning.
        name: Experiment name used as the checkpoint filename stem.
    """

    train_path: str | Path
    val_path: str | Path
    arch: str = "crnn_vgg16_bn"
    epochs: int = 10
    batch_size: int = 64
    lr: float = 0.001
    weight_decay: float = 0.0
    optimizer: str = "adam"
    scheduler: str = "cosine"
    input_size: int = 32
    vocab: str = "french"
    workers: int = 4
    amp: bool = False
    early_stop: bool = False
    early_stop_epochs: int = 5
    early_stop_delta: float = 0.01
    output_dir: str | Path = Field(default=".")
    device: int | None = None
    pretrained: bool = True
    name: str | None = None


# ---------------------------------------------------------------------------
# ITrainingRunner Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class ITrainingRunner(Protocol):
    """Contract for running DocTR detection and recognition training.

    Implementations yield ``TrainingEvent`` objects so callers can stream
    progress without polling.  Concrete implementations (e.g.
    ``LocalTrainingRunner``) bridge the existing ``progress_hook`` callback
    API into this iterator surface.

    Example::

        runner: ITrainingRunner = LocalTrainingRunner()
        cfg = DetectionConfig(train_path="...", val_path="...")
        for event in runner.train_detection("run-001", cfg):
            print(event.kind, event.message)
    """

    def train_detection(
        self,
        profile: str,
        config: DetectionConfig,
    ) -> Iterator[TrainingEvent]:
        """Run a detection training job and stream progress events.

        Args:
            profile: Logical identifier for this training run (used for
                logging and checkpoint naming when ``config.name`` is absent).
            config: Fully-specified detection training configuration.

        Yields:
            ``TrainingEvent`` objects during training; the final event has
            ``kind="done"`` on success or ``kind="error"`` on failure.
        """
        ...

    def train_recognition(
        self,
        profile: str,
        config: RecognitionConfig,
    ) -> Iterator[TrainingEvent]:
        """Run a recognition training job and stream progress events.

        Args:
            profile: Logical identifier for this training run.
            config: Fully-specified recognition training configuration.

        Yields:
            ``TrainingEvent`` objects during training; the final event has
            ``kind="done"`` on success or ``kind="error"`` on failure.
        """
        ...
