"""Quality gates. Pure functions returning error strings; empty list means pass."""
from __future__ import annotations

import json
from pathlib import Path

from .manifest import sha256_file


def validate_dataset(src: Path, manifest: dict) -> list[str]:
    errors: list[str] = []
    coco = json.loads((src / "annotations" / "instances.json").read_text())
    images = {i["id"]: i for i in coco["images"]}
    if len(images) != len(coco["images"]):
        errors.append("duplicate image ids")
    categories = {c["id"] for c in coco["categories"]}
    shipped = {f["path"] for f in manifest["files"]}
    for img in images.values():
        if f"images/{img['file_name']}" not in shipped:
            errors.append(f"image listed in annotations but missing: {img['file_name']}")
    annotated = set()
    for a in coco["annotations"]:
        img = images.get(a["image_id"])
        if img is None:
            errors.append(f"annotation {a['id']}: unknown image_id {a['image_id']}")
            continue
        annotated.add(a["image_id"])
        if a["category_id"] not in categories:
            errors.append(f"annotation {a['id']}: unknown category_id {a['category_id']}")
        x, y, w, h = a["bbox"]
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > img["width"] or y + h > img["height"]:
            errors.append(f"annotation {a['id']}: bbox outside image bounds")
    errors += [f"image without annotations: {i['file_name']}"
               for i in images.values() if i["id"] not in annotated]
    for f in manifest["files"]:
        if sha256_file(src / f["path"]) != f["sha256"]:
            errors.append(f"checksum mismatch: {f['path']}")
    return errors
