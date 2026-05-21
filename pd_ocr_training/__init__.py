"""DocTR OCR model training pipeline for the pd-* OCR suite."""

from pd_ocr_training.local import LocalTrainingRunner
from pd_ocr_training.protocols import (
    DetectionConfig,
    ITrainingRunner,
    RecognitionConfig,
    TrainingEvent,
)

__version__ = "0.1.0"
__all__ = [
    "DetectionConfig",
    "ITrainingRunner",
    "LocalTrainingRunner",
    "RecognitionConfig",
    "TrainingEvent",
]
