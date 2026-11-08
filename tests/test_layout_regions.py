"""Layout training reads the labeler's regions/labels.json export."""

from __future__ import annotations

import json
import struct
import zlib
from typing import TYPE_CHECKING

import pytest
from pdomain_book_contracts.annotation import RegionRole

from pdomain_ocr_training.layout import train_layout_from_config
from pdomain_ocr_training.layout_regions import load_layout_export, load_layout_structures

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


def _write_structures(root: Path, regions: list[object]) -> None:
    path = root / "regions" / "structure.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "pdomain.layout-structure",
                "version": 1,
                "regions": regions,
            }
        ),
        encoding="utf-8",
    )


def _structure_record(
    *,
    prefix: str = "book_004",
    page_index: int = 4,
    region_id: str = "r1",
) -> dict[str, object]:
    return {
        "prefix": prefix,
        "page_index": page_index,
        "region_id": region_id,
        "structure": {
            "kind": "poetry",
            "lines": [
                {
                    "text": "First line",
                    "word_ids": ["word-1", "word-2"],
                    "word_signatures": ["word-1@12,22,40,38", "word-2@42,22,70,38"],
                    "stanza_index": 0,
                    "indent_hint": "2em",
                }
            ],
            "column_group_id": "left-column",
            "column_index": 0,
            "reading_order": 0,
        },
    }


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


def test_load_keeps_legacy_region_dictionaries_when_structure_is_absent(tmp_path: Path) -> None:
    _export_with_image(tmp_path)

    pages = load_layout_export(tmp_path)

    assert "structure" not in pages[0]["regions"][0]
    assert load_layout_structures(tmp_path, pages=pages) == {}


def test_load_attaches_reviewed_structure_to_its_matching_region(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    _write_structures(tmp_path, [_structure_record()])

    pages = load_layout_export(tmp_path)

    structure = pages[0]["regions"][0].get("structure")
    assert structure is not None
    assert structure.to_dict() == _structure_record()["structure"]


def test_load_allows_partial_structure_coverage(tmp_path: Path) -> None:
    first = _page()
    second = _page(prefix="book_005", page_index=5)
    _write_export(tmp_path, [first, second])
    _png(tmp_path / "detection" / "images" / "book_004_4.png", 200, 300)
    _png(tmp_path / "detection" / "images" / "book_005_5.png", 200, 300)
    _write_structures(tmp_path, [_structure_record()])

    pages = load_layout_export(tmp_path)

    assert "structure" in pages[0]["regions"][0]
    assert "structure" not in pages[1]["regions"][0]


def test_load_attaches_column_flow_to_one_of_multiple_regions_on_a_page(tmp_path: Path) -> None:
    page = _page()
    regions = page["regions"]
    assert isinstance(regions, list)
    regions.append(
        {
            "region_id": "r2",
            "role": "paragraph",
            "box": {"x": 120, "y": 20, "width": 70, "height": 60},
            "member_word_signatures": [],
        }
    )
    _export_with_image(tmp_path, page)
    record = _structure_record(region_id="r2")
    structure = record["structure"]
    assert isinstance(structure, dict)
    structure["kind"] = "column_flow"
    structure["lines"] = []
    _write_structures(tmp_path, [record])

    pages = load_layout_export(tmp_path)

    assert "structure" not in pages[0]["regions"][0]
    attached = pages[0]["regions"][1].get("structure")
    assert attached is not None
    assert attached.kind == "column_flow"
    assert attached.column_group_id == "left-column"


def test_load_rejects_structure_for_an_unknown_region(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    _write_structures(tmp_path, [_structure_record(region_id="missing")])

    with pytest.raises(ValueError, match="unknown region"):
        load_layout_export(tmp_path)


@pytest.mark.parametrize(
    ("prefix", "page_index"),
    [("other_book", 4), ("book_004", 99)],
)
def test_load_rejects_structure_for_an_unknown_page(
    tmp_path: Path,
    prefix: str,
    page_index: int,
) -> None:
    _export_with_image(tmp_path)
    _write_structures(tmp_path, [_structure_record(prefix=prefix, page_index=page_index)])

    with pytest.raises(ValueError, match="unknown region"):
        load_layout_export(tmp_path)


def test_load_rejects_duplicate_structure_join_keys(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    _write_structures(tmp_path, [_structure_record(), _structure_record()])

    with pytest.raises(ValueError, match="duplicate"):
        load_layout_export(tmp_path)


def test_load_rejects_structure_for_a_duplicate_region_target(tmp_path: Path) -> None:
    page = _page()
    regions = page["regions"]
    assert isinstance(regions, list)
    regions.append(dict(regions[0]))
    _export_with_image(tmp_path, page)
    _write_structures(tmp_path, [_structure_record()])

    with pytest.raises(ValueError, match="ambiguous"):
        load_layout_export(tmp_path)


def test_load_rejects_a_structure_file_with_an_unexpected_schema(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    path = tmp_path / "regions" / "structure.json"
    path.write_text(json.dumps({"schema": "other", "version": 1, "regions": []}), encoding="utf-8")

    with pytest.raises(ValueError, match=r"structure.*schema"):
        load_layout_export(tmp_path)


def test_load_rejects_malformed_reviewed_structure(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    record = _structure_record()
    record["structure"] = {"lines": "not-a-list"}
    _write_structures(tmp_path, [record])

    with pytest.raises(ValueError, match="invalid"):
        load_layout_export(tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("stanza_index", -1),
        ("word_ids", []),
        ("measured_indent", float("inf")),
    ],
)
def test_load_uses_shared_validation_for_malformed_structure_fields(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    _export_with_image(tmp_path)
    record = _structure_record()
    structure = record["structure"]
    assert isinstance(structure, dict)
    lines = structure["lines"]
    assert isinstance(lines, list)
    line = lines[0]
    assert isinstance(line, dict)
    line[field] = value
    if field == "word_ids":
        line["word_signatures"] = []
    _write_structures(tmp_path, [record])

    with pytest.raises(ValueError, match="invalid"):
        load_layout_export(tmp_path)


def test_load_rejects_a_non_object_structure_record(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    _write_structures(tmp_path, ["not-an-object"])

    with pytest.raises(TypeError, match=r"structure region.*object"):
        load_layout_export(tmp_path)


def test_load_rejects_a_structure_path_that_is_not_a_file(tmp_path: Path) -> None:
    _export_with_image(tmp_path)
    (tmp_path / "regions" / "structure.json").mkdir()

    with pytest.raises(ValueError, match="not a file"):
        load_layout_export(tmp_path)


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


def test_train_layout_forwards_reviewed_structure_to_the_model(tmp_path: Path) -> None:
    train_dir = tmp_path / "train"
    val_dir = tmp_path / "val"
    _export_with_image(train_dir)
    _export_with_image(val_dir)
    _write_structures(train_dir, [_structure_record()])
    _write_structures(val_dir, [_structure_record()])
    model = _RecordingModel()

    train_layout_from_config(
        train_path=train_dir,
        val_path=val_dir,
        epochs=1,
        output_dir=tmp_path / "out",
        name="layout-run",
        model=model,
    )

    trained_structure = model.trained[0]["regions"][0].get("structure")
    validated_structure = model.validated[0]["regions"][0].get("structure")
    assert trained_structure is not None
    assert validated_structure is not None
    assert trained_structure.to_dict() == _structure_record()["structure"]
    assert validated_structure.to_dict() == _structure_record()["structure"]


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
