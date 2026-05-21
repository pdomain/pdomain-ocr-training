# Changelog

## [Unreleased]

## [0.1.0] - 2026-05-21

### Added

- Initial extraction of DocTR training pipeline from `pd-ocr-trainer`.
- `detect.py` and `recog.py`: verbatim-moved DocTR detection and recognition
  training entry points.
- `datasets.py`: `ExportManager` for dataset export.
- `utils.py`: shared training utilities.
- `protocols.py`: `ITrainingRunner` Protocol + `TrainingEvent`,
  `DetectionConfig`, `RecognitionConfig` typed config models.
- `local.py`: `LocalTrainingRunner` — bridges callback-style training functions
  into `Iterator[TrainingEvent]` via a background thread and queue.
