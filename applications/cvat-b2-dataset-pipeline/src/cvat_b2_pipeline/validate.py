"""Release-contract and COCO quality gates; an empty error list means pass."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator

from .manifest import sha256_file


@lru_cache(maxsize=1)
def release_validator():
    resource = files("cvat_b2_pipeline").joinpath("schemas").joinpath("release-manifest.schema.json")
    schema = json.loads(resource.read_text())
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def validate_manifest(manifest: dict) -> list[str]:
    return [
        "manifest " + "/".join(str(part) for part in error.absolute_path) + ": " + error.message
        for error in release_validator().iter_errors(manifest)
    ]


def _finite_number(value) -> bool:
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def validate_dataset(src: Path, manifest: dict) -> list[str]:
    errors = validate_manifest(manifest)
    if errors:
        return errors
    try:
        coco = json.loads((src / "annotations/instances.json").read_text(), parse_constant=_reject_constant)
    except (OSError, ValueError) as error:
        return [f"annotations/instances.json: {error}"]
    if not isinstance(coco, dict):
        return ["COCO export must be an object"]
    for name in ("images", "categories", "annotations"):
        if not isinstance(coco.get(name), list):
            errors.append(f"COCO {name} must be an array")
    if errors:
        return errors

    if not coco["images"] or not coco["categories"]:
        return ["COCO export must contain images and categories"]

    def records(name, required):
        valid = {}
        for index, record in enumerate(coco[name]):
            if not isinstance(record, dict) or not required <= record.keys():
                errors.append(f"{name}[{index}]: missing required fields {', '.join(sorted(required))}")
                continue
            identifier = record["id"]
            if type(identifier) is not int or identifier < 0:
                errors.append(f"{name}[{index}]: id must be a non-negative integer")
                continue
            if identifier in valid:
                errors.append(f"duplicate {name} ids: {identifier}")
            valid[identifier] = record
        return valid

    images = records("images", {"id", "file_name", "width", "height"})
    categories = records("categories", {"id", "name"})
    annotations = records("annotations", {"id", "image_id", "category_id", "bbox"})
    shipped = {file["path"] for file in manifest["files"]}
    usable_images = {}
    for identifier, image in images.items():
        if not isinstance(image["file_name"], str) or not image["file_name"]:
            errors.append(f"image {identifier}: file_name must be a non-empty string")
            continue
        if f"images/{image['file_name']}" not in shipped:
            errors.append(f"image listed in annotations but missing: {image['file_name']}")
        if any(type(image[axis]) is not int or image[axis] <= 0 for axis in ("width", "height")):
            errors.append(f"image {identifier}: width and height must be positive integers")
            continue
        usable_images[identifier] = image
    for identifier, category in categories.items():
        if not isinstance(category["name"], str) or not category["name"]:
            errors.append(f"category {identifier}: name must be a non-empty string")

    annotated = set()
    for identifier, annotation in annotations.items():
        image_id, category_id = annotation["image_id"], annotation["category_id"]
        if type(image_id) is not int or image_id not in usable_images:
            errors.append(f"annotation {identifier}: unknown image_id {image_id}")
            continue
        image = usable_images[image_id]
        annotated.add(image_id)
        if type(category_id) is not int or category_id not in categories:
            errors.append(f"annotation {identifier}: unknown category_id {category_id}")
        bbox = annotation["bbox"]
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_finite_number(v) for v in bbox):
            errors.append(f"annotation {identifier}: bbox must contain four finite numbers")
            continue
        x, y, width, height = bbox
        if (width <= 0 or height <= 0 or x < 0 or y < 0
                or x + width > image["width"] or y + height > image["height"]):
            errors.append(f"annotation {identifier}: bbox outside image bounds")
    errors += [f"image without annotations: {image['file_name']}"
               for identifier, image in usable_images.items() if identifier not in annotated]
    for file in manifest["files"]:
        try:
            if sha256_file(src / file["path"]) != file["sha256"]:
                errors.append(f"checksum mismatch: {file['path']}")
        except OSError:
            errors.append(f"cannot read release file: {file['path']}")
    return errors
