"""Layout training reads the labeler's regions/labels.json export."""

from __future__ import annotations

import json
import struct
import zlib
from typing import TYPE_CHECKING

import pytest
from pdomain_book_contracts.annotation import RegionRole

from pdomain_ocr_training.layout import train_layout_from_config
from pdomain_ocr_training.layout_regions import load_layout_export

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from pdomain_ocr_training.layout_regions import LayoutPageExample


def _png(path: Path, width: int, height: int) -> None:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + (b"\x00" * 3 * width) for _ in range(height))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def _write_export(root: Path, pages: list[dict[str, object]]) -> None:
    path = root / "regions" / "labels.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema": "pdomain.layout-regions", "version": 1, "pages": pages}),
        encoding="utf-8",
    )


def _page(prefix: str = "book_004", page_index: int = 4) -> dict[str, object]:
    return {
        "prefix": prefix,
        "page_index": page_index,
        "regions": [
            {
                "region_id": "r1",
                "role": "poetry",
                "box": {"x": 10, "y": 20, "width": 100, "height": 60},
                "member_word_signatures": [[12.0, 22.0, 40.0, 38.0, False]],
            }
        ],
    }


def _export_with_image(root: Path, page: dict[str, object] | None = None) -> None:
    item = _page() if page is None else page
    prefix = item["prefix"]
    page_index = item["page_index"]
    assert isinstance(prefix, str)
    assert isinstance(page_index, int)
    _write_export(root, [item])
    _png(root / "detection" / "images" / f"{prefix}_{page_index}.png", 200, 300)


def test_load_reads_the_region_box_role_and_detection_image(tmp_path: Path) -> None:
    _export_with_image(tmp_path)

    pages = load_layout_export(tmp_path)

    assert len(pages) == 1
    page = pages[0]
    assert page["prefix"] == "book_004"
    assert page["page_index"] == 4
    assert page["width"] == 200
    assert page["height"] == 300
    assert page["image_path"] == str(tmp_path / "detection" / "images" / "book_004_4.png")
    assert len(page["regions"]) == 1
    region = page["regions"][0]
    assert region["region_id"] == "r1"
    assert region["role"] == "poetry"
    assert region["class_id"] == list(RegionRole).index(RegionRole.POETRY)
    assert region["box"] == {"x": 10, "y": 20, "width": 100, "height": 60}
    assert region["member_word_signatures"] == [[12.0, 22.0, 40.0, 38.0, False]]


@pytest.mark.parametrize("version", [True, 1.0])
def test_load_rejects_a_boolean_or_float_version(tmp_path: Path, version: object) -> None:
    path = tmp_path / "regions" / "labels.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"schema": "pdomain.layout-regions", "version": version, "pages": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="schema"):
        load_layout_export(tmp_path)


def test_load_rejects_an_unexpected_schema(tmp_path: Path) -> None:
    path = tmp_path / "regions" / "labels.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"schema": "other", "version": 1, "pages": []}), encoding="utf-8")

    with pytest.raises(ValueError, match="schema"):
        load_layout_export(tmp_path)


def test_load_rejects_an_unknown_role(tmp_path: Path) -> None:
    page = _page()
    regions = page["regions"]
    assert isinstance(regions, list)
    region = regions[0]
    assert isinstance(region, dict)
    region["role"] = "not-a-role"
    _export_with_image(tmp_path, page)

    with pytest.raises(ValueError, match="role"):
        load_layout_export(tmp_path)


def test_load_errors_when_the_page_image_is_missing(tmp_path: Path) -> None:
    _write_export(tmp_path, [_page()])

    with pytest.raises(FileNotFoundError, match=r"book_004_4\.png"):
        load_layout_export(tmp_path)


def test_load_rejects_a_box_outside_the_image(tmp_path: Path) -> None:
    page = _page()
    _write_export(tmp_path, [page])
    _png(tmp_path / "detection" / "images" / "book_004_4.png", 20, 20)

    with pytest.raises(ValueError, match="r1"):
        load_layout_export(tmp_path)


def test_load_keeps_a_page_with_no_regions(tmp_path: Path) -> None:
    page = _page()
    page["regions"] = []
    _export_with_image(tmp_path, page)

    pages = load_layout_export(tmp_path)

    assert pages[0]["regions"] == []


def test_load_accepts_a_null_word_signature_flag(tmp_path: Path) -> None:
    page = _page()
    regions = page["regions"]
    assert isinstance(regions, list)
    region = regions[0]
    assert isinstance(region, dict)
    region["member_word_signatures"] = [[1, 2, 3, 4, None]]
    _export_with_image(tmp_path, page)

    pages = load_layout_export(tmp_path)

    assert pages[0]["regions"][0]["member_word_signatures"] == [[1.0, 2.0, 3.0, 4.0, None]]


def test_load_rejects_a_repeated_prefix(tmp_path: Path) -> None:
    page = _page()
    _write_export(tmp_path, [page, page])
    _png(tmp_path / "detection" / "images" / "book_004_4.png", 200, 300)

    with pytest.raises(ValueError, match="prefix"):
        load_layout_export(tmp_path)


def test_load_rejects_a_prefix_that_leaves_the_image_directory(tmp_path: Path) -> None:
    page = _page(prefix="../secret", page_index=1)
    _write_export(tmp_path, [page])

    with pytest.raises(ValueError, match="prefix"):
        load_layout_export(tmp_path)


class _RecordingModel:
    def __init__(self) -> None:
        self.trained: list[LayoutPageExample] = []
        self.validated: list[LayoutPageExample] = []
        self.saved: Path | None = None

    def train_batch(self, examples: Sequence[LayoutPageExample]) -> float:
        self.trained.extend(examples)
        return 0.25

    def validate_batch(self, examples: Sequence[LayoutPageExample]) -> float:
        self.validated.extend(examples)
        return 0.5

    def save(self, path: Path) -> None:
        self.saved = path


def test_train_layout_gives_the_model_the_loaded_pages(tmp_path: Path) -> None:
    train_dir = tmp_path / "train"
    val_dir = tmp_path / "val"
    _export_with_image(train_dir)
    _export_with_image(val_dir)
    model = _RecordingModel()
    events: list[dict[str, object]] = []

    train_layout_from_config(
        train_path=train_dir,
        val_path=val_dir,
        epochs=1,
        output_dir=tmp_path / "out",
        name="layout-run",
        model=model,
        progress_hook=events.append,
    )

    assert [page["prefix"] for page in model.trained] == ["book_004"]
    assert model.trained[0]["regions"][0]["role"] == "poetry"
    assert [page["prefix"] for page in model.validated] == ["book_004"]
    assert model.saved == tmp_path / "out" / "layout-run.pt"
    assert events[-1]["event"] == "epoch_end"
    assert events[-1]["epoch"] == 1


def test_train_layout_rejects_a_checkpoint_name_that_leaves_the_output_directory(
    tmp_path: Path,
) -> None:
    model = _RecordingModel()

    with pytest.raises(ValueError, match="checkpoint name"):
        train_layout_from_config(
            train_path=tmp_path / "train",
            val_path=tmp_path / "val",
            epochs=1,
            output_dir=tmp_path / "out",
            name="../outside",
            model=model,
        )

    assert model.saved is None
    assert model.trained == []


class _NanLossModel(_RecordingModel):
    def train_batch(self, examples: Sequence[LayoutPageExample]) -> float:
        return float("nan")


def test_train_layout_stops_when_a_batch_loss_is_not_finite(tmp_path: Path) -> None:
    train_dir = tmp_path / "train"
    val_dir = tmp_path / "val"
    _export_with_image(train_dir)
    _export_with_image(val_dir)

    with pytest.raises(ValueError, match="finite"):
        train_layout_from_config(
            train_path=train_dir,
            val_path=val_dir,
            epochs=1,
            output_dir=tmp_path / "out",
            name="layout-run",
            model=_NanLossModel(),
        )


def test_train_layout_refuses_to_download_weights(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="weights"):
        train_layout_from_config(
            train_path=tmp_path / "train",
            val_path=tmp_path / "val",
            epochs=1,
            output_dir=tmp_path / "out",
            name="layout-run",
            model=None,
        )
