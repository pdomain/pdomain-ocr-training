# pd-ocr-training

DocTR OCR model training pipeline for the `pd-*` OCR suite.

This package owns all torch/DocTR training code — detection and recognition model fine-tuning, dataset management, and model export. Isolating torch here keeps every other `pd-*` SPA backend (e.g. `pd-ocr-labeler-spa`, `pd-prep-for-pgdp`) torch-free and deployment-lightweight.

Supersedes the legacy `pd-ocr-trainer` repo.
