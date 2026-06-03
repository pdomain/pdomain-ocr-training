from __future__ import annotations

import importlib
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

import pdomain_ocr_training


def test_version_matches_installed_metadata() -> None:
    try:
        metadata_version = version("pdomain-ocr-training")
    except PackageNotFoundError:
        assert pdomain_ocr_training.__version__ == "0.0.0+unknown"
        return

    assert pdomain_ocr_training.__version__ == metadata_version


def test_version_falls_back_when_metadata_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    original_module = sys.modules.get("pdomain_ocr_training")

    def missing_version(distribution_name: str) -> str:
        if distribution_name == "pdomain-ocr-training":
            raise PackageNotFoundError
        return version(distribution_name)

    monkeypatch.setattr("importlib.metadata.version", missing_version)
    sys.modules.pop("pdomain_ocr_training", None)
    try:
        imported = importlib.import_module("pdomain_ocr_training")
        assert imported.__version__ == "0.0.0+unknown"
    finally:
        sys.modules.pop("pdomain_ocr_training", None)
        if original_module is not None:
            sys.modules["pdomain_ocr_training"] = original_module


def test_version_is_exposed() -> None:
    assert pdomain_ocr_training.__version__
    assert isinstance(pdomain_ocr_training.__version__, str)
