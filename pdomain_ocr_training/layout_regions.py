"""Read the labeler's ``regions/labels.json`` export."""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

from pdomain_book_contracts.annotation import RegionRole

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pdomain_book_contracts.layout.text_hints import LayoutStructure

LAYOUT_REGIONS_SCHEMA = "pdomain.layout-regions"
LAYOUT_REGIONS_VERSION = 1
LAYOUT_STRUCTURE_SCHEMA = "pdomain.layout-structure"
LAYOUT_STRUCTURE_VERSION = 1
LAYOUT_CLASS_NAMES: tuple[str, ...] = tuple(role.value for role in RegionRole)

_CLASS_INDEX = {name: index for index, name in enumerate(LAYOUT_CLASS_NAMES)}


class LayoutBox(TypedDict):
    """Pixel box from the region export: x, y, width, height."""

    x: int
    y: int
    width: int
    height: int


class LayoutRegionExample(TypedDict):
    """One confirmed region, with its role's class index."""

    region_id: str
    role: str
    class_id: int
    box: LayoutBox
    member_word_signatures: list[list[float | bool | None]]
    structure: NotRequired[LayoutStructure]


class LayoutPageExample(TypedDict):
    """One exported page and the detection image written beside it."""

    prefix: str
    page_index: int
    image_path: str
    width: int
    height: int
    regions: list[LayoutRegionExample]


def load_layout_export(export_dir: Path) -> list[LayoutPageExample]:
    """Load ``regions/labels.json`` and pair each page with its detection image."""
    path = export_dir / "regions" / "labels.json"
    if not path.is_file():
        raise FileNotFoundError(f"layout regions file is missing: {path}")
    document = _parse_document(path)
    pages: list[LayoutPageExample] = []
    seen_prefixes: set[str] = set()
    seen_images: set[Path] = set()
    for item in document:
        page = _parse_page(item, export_dir)
        if page["prefix"] in seen_prefixes:
            raise ValueError(f"layout regions file repeats prefix {page['prefix']!r}")
        image = Path(page["image_path"])
        if image in seen_images:
            raise ValueError(f"layout pages resolve to the same image: {image}")
        seen_prefixes.add(page["prefix"])
        seen_images.add(image)
        pages.append(page)
    structures = load_layout_structures(export_dir, pages=pages)
    for page in pages:
        for region in page["regions"]:
            key = (page["prefix"], page["page_index"], region["region_id"])
            structure = structures.get(key)
            if structure is not None:
                region["structure"] = structure
    return pages


def load_layout_structures(
    export_dir: Path,
    *,
    pages: Sequence[LayoutPageExample],
) -> dict[tuple[str, int, str], LayoutStructure]:
    """Load and validate optional reviewed structure beside a region export."""
    path = export_dir / "regions" / "structure.json"
    if not path.exists():
        return {}
    if not path.is_file():
        raise ValueError(f"layout structure path is not a file: {path}")
    from pdomain_book_contracts.layout.text_hints import LayoutStructure

    records = _parse_structure_document(path)
    target_counts: dict[tuple[str, int, str], int] = {}
    for page in pages:
        for region in page["regions"]:
            key = (page["prefix"], page["page_index"], region["region_id"])
            target_counts[key] = target_counts.get(key, 0) + 1
    ambiguous_targets = [key for key, count in target_counts.items() if count > 1]
    if ambiguous_targets:
        raise ValueError(
            f"layout structure file has an ambiguous duplicate region target {ambiguous_targets[0]!r}"
        )
    known_regions = set(target_counts)
    structures: dict[tuple[str, int, str], LayoutStructure] = {}
    for record in records:
        mapping = _object_dict(record, "structure region")
        key = (
            _layout_str(
                _required(mapping, "prefix", "structure region prefix"), "structure prefix"
            ),
            _layout_int(
                _required(mapping, "page_index", "structure region page_index"),
                "structure page_index",
            ),
            _layout_str(
                _required(mapping, "region_id", "structure region region_id"),
                "structure region_id",
            ),
        )
        if key in structures:
            raise ValueError(f"layout structure file has duplicate join key {key!r}")
        if key not in known_regions:
            raise ValueError(f"layout structure file has an unknown region join key {key!r}")
        structure = _object_dict(
            _required(mapping, "structure", "structure region structure"),
            "structure region structure",
        )
        try:
            structures[key] = LayoutStructure.from_dict(structure)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"layout structure {key!r} is invalid: {exc}") from exc
    return structures


def _json_value(text: str) -> object:
    # json.loads is typed as Any. The parsers below check every field.
    return json.loads(text)  # pyright: ignore[reportAny]


def _object_dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"layout regions {label} must be an object")
    raw: dict[object, object] = value  # pyright: ignore[reportUnknownVariableType]
    mapping: dict[str, object] = {}
    for key, item in raw.items():
        if not isinstance(key, str):
            raise TypeError(f"layout regions {label} has a non-string key")
        mapping[key] = item
    return mapping


def _object_list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise TypeError(f"layout regions {label} must be a list")
    raw: list[object] = value  # pyright: ignore[reportUnknownVariableType]
    return list(raw)


def _required(mapping: dict[str, object], key: str, label: str) -> object:
    if key not in mapping:
        raise ValueError(f"layout regions {label} is missing")
    return mapping[key]


def _layout_str(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"layout regions {label} must be a string")
    return value


def _layout_int(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"layout regions {label} must be an integer")
    return value


def _parse_document(path: Path) -> list[object]:
    raw = _object_dict(_json_value(path.read_text(encoding="utf-8")), "file")
    version = raw.get("version")
    version_ok = (
        isinstance(version, int)
        and not isinstance(version, bool)
        and version == LAYOUT_REGIONS_VERSION
    )
    if raw.get("schema") != LAYOUT_REGIONS_SCHEMA or not version_ok:
        raise ValueError("layout regions file has an unexpected schema")
    try:
        return _object_list(raw.get("pages"), "pages")
    except ValueError as exc:
        raise ValueError("layout regions file has an unexpected schema") from exc


def _parse_structure_document(path: Path) -> list[object]:
    raw = _object_dict(_json_value(path.read_text(encoding="utf-8")), "structure file")
    version = raw.get("version")
    version_ok = (
        isinstance(version, int)
        and not isinstance(version, bool)
        and version == LAYOUT_STRUCTURE_VERSION
    )
    if raw.get("schema") != LAYOUT_STRUCTURE_SCHEMA or not version_ok:
        raise ValueError("layout structure file has an unexpected schema")
    try:
        return _object_list(raw.get("regions"), "structure regions")
    except ValueError as exc:
        raise ValueError("layout structure file has an unexpected schema") from exc


def _image_name(prefix: str, page_index: int) -> str:
    if "/" in prefix or "\\" in prefix or prefix == "..":
        raise ValueError(f"layout page prefix is not a file name: {prefix!r}")
    return f"{prefix}_{page_index}.png"


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    png_signature = b"\x89PNG\r\n\x1a\n"
    if len(header) < 24 or header[:8] != png_signature or header[12:16] != b"IHDR":
        raise ValueError(f"layout page image is not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    if width <= 0 or height <= 0:
        raise ValueError(f"layout page image has no pixels: {path}")
    return width, height


def _parse_box(value: object) -> LayoutBox:
    mapping = _object_dict(value, "box")
    return {
        "x": _layout_int(_required(mapping, "x", "box.x"), "box.x"),
        "y": _layout_int(_required(mapping, "y", "box.y"), "box.y"),
        "width": _layout_int(_required(mapping, "width", "box.width"), "box.width"),
        "height": _layout_int(_required(mapping, "height", "box.height"), "box.height"),
    }


def _parse_signature(value: object) -> list[float | bool | None]:
    items = _object_list(value, "word signature")
    if len(items) != 5:
        raise ValueError("layout region word signature must have 5 entries")
    parsed: list[float | bool | None] = []
    for index, item in enumerate(items):
        if index < 4:
            if isinstance(item, bool) or not isinstance(item, int | float):
                raise TypeError("layout region word signature coordinate must be a number")
            parsed.append(float(item))
            continue
        if item is not None and not isinstance(item, bool):
            raise TypeError("layout region word signature flag must be a boolean or null")
        parsed.append(item)
    return parsed


def _class_id(role: str) -> int:
    try:
        return _CLASS_INDEX[role]
    except KeyError:
        raise ValueError(f"layout region role is not a region role: {role}") from None


def _check_box(box: LayoutBox, width: int, height: int, region_id: str) -> None:
    if box["width"] <= 0 or box["height"] <= 0:
        raise ValueError(f"layout region {region_id} has an empty box")
    if (
        box["x"] < 0
        or box["y"] < 0
        or box["x"] + box["width"] > width
        or box["y"] + box["height"] > height
    ):
        raise ValueError(f"layout region {region_id} is outside the page image")


def _parse_region(value: object, width: int, height: int) -> LayoutRegionExample:
    mapping = _object_dict(value, "region")
    region_id = _layout_str(_required(mapping, "region_id", "region_id"), "region_id")
    role = _layout_str(_required(mapping, "role", "role"), "role")
    box = _parse_box(_required(mapping, "box", "box"))
    _check_box(box, width, height, region_id)
    signatures = _object_list(
        _required(mapping, "member_word_signatures", "member_word_signatures"),
        "member_word_signatures",
    )
    return {
        "region_id": region_id,
        "role": role,
        "class_id": _class_id(role),
        "box": box,
        "member_word_signatures": [_parse_signature(item) for item in signatures],
    }


def _parse_page(value: object, export_dir: Path) -> LayoutPageExample:
    mapping = _object_dict(value, "page")
    prefix = _layout_str(_required(mapping, "prefix", "prefix"), "prefix")
    page_index = _layout_int(_required(mapping, "page_index", "page_index"), "page_index")
    # The same export writes detection/images/{prefix}_{page_index}.png.
    image_path = export_dir / "detection" / "images" / _image_name(prefix, page_index)
    if not image_path.is_file():
        raise FileNotFoundError(f"layout page image is missing: {image_path}")
    width, height = _png_size(image_path)
    regions = _object_list(_required(mapping, "regions", "regions"), "regions")
    return {
        "prefix": prefix,
        "page_index": page_index,
        "image_path": str(image_path),
        "width": width,
        "height": height,
        "regions": [_parse_region(item, width, height) for item in regions],
    }
