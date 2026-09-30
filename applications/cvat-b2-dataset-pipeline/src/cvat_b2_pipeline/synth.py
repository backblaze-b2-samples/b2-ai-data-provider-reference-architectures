"""Deterministic synthetic images with COCO annotations (the CVAT COCO 1.0 export shape)."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw

CATEGORIES = [{"id": 1, "name": "box"}, {"id": 2, "name": "disc"}]
SIZE = (320, 240)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_dataset_metadata(out: Path, count: int) -> None:
    card = f"""---
pretty_name: Synthetic Toy Object Detection Dataset
license: mit
task_categories:
  - object-detection
tags:
  - synthetic
  - image
  - coco
  - mlcroissant
---

# Synthetic Toy Object Detection Dataset

{count} deterministic PNG images and COCO 1.0 annotations used to test the reference release pipeline without customer data or external downloads.

## Intended use

- Exercise ingestion, annotation validation, immutable release publishing and presigned delivery.
- Provide a small fixture for unit and integration tests.
- Demonstrate the release manifest, dataset card and Croissant metadata contracts.

This dataset is not suitable for model training, benchmarking, fairness evaluation or production quality assessment.

## Composition and provenance

- Modality: image.
- Files: {count} PNG images and one COCO annotation file.
- Generation: deterministic local shapes produced by `cvat_b2_pipeline.synth`; no real people, customer data or downloaded source material.
- Annotations: generated with the images and validated for category references, bounding boxes, coverage and checksums.
- Release version: `v1`.

## Rights and sensitive data

The fixture is distributed under the [MIT license](https://spdx.org/licenses/MIT.html). It contains no intentionally collected personal information, biometric identifiers or licensed third-party media.

## Machine-readable metadata

- [Croissant JSON-LD](croissant.json)
- `manifest.json`, written last by the publisher, supplies the release identity and per-file integrity data.
"""
    (out / "README.md").write_text(card)

    distribution = []
    for i, path in enumerate(sorted((out / "images").glob("*.png")), start=1):
        distribution.append({
            "@type": "cr:FileObject",
            "@id": f"image-{i}",
            "name": path.name,
            "contentUrl": f"images/{path.name}",
            "contentSize": f"{path.stat().st_size} B",
            "encodingFormat": "image/png",
            "sha256": _sha256(path),
        })
    annotations = out / "annotations" / "instances.json"
    distribution.append({
        "@type": "cr:FileObject",
        "@id": "annotations",
        "name": "instances.json",
        "contentUrl": "annotations/instances.json",
        "contentSize": f"{annotations.stat().st_size} B",
        "encodingFormat": "application/json",
        "sha256": _sha256(annotations),
    })
    croissant = {
        "@context": {
            "@language": "en",
            "@vocab": "https://schema.org/",
            "cr": "http://mlcommons.org/croissant/",
            "dct": "http://purl.org/dc/terms/",
            "sc": "https://schema.org/",
        },
        "@type": "sc:Dataset",
        "name": "Synthetic Toy Object Detection Dataset",
        "description": f"{count} deterministic synthetic PNG images with COCO 1.0 object-detection annotations for testing a B2 dataset release pipeline.",
        "dct:conformsTo": "http://mlcommons.org/croissant/1.0",
        "version": "v1",
        "license": "https://spdx.org/licenses/MIT.html",
        "url": "https://www.backblaze.com/docs/cloud-storage-ai-machine-learning",
        "creator": {
            "@type": "sc:Organization",
            "name": "Backblaze, Inc.",
            "url": "https://www.backblaze.com/",
        },
        "datePublished": "2026-09-29",
        "keywords": ["synthetic", "object detection", "COCO", "Backblaze B2"],
        "distribution": distribution,
    }
    (out / "croissant.json").write_text(json.dumps(croissant, indent=2) + "\n")


def generate(out: Path, count: int, seed: int = 0) -> None:
    """Write images, COCO/CVAT manifests, a dataset card, and Croissant metadata."""
    rng = random.Random(seed)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "annotations").mkdir(parents=True, exist_ok=True)
    images, annotations, manifest = [], [], ['{"version":"1.1"}', '{"type":"images"}']
    for i in range(1, count + 1):
        name = f"img_{i:04d}"
        img = Image.new("RGB", SIZE, (rng.randrange(256),) * 3)
        draw = ImageDraw.Draw(img)
        for _ in range(rng.randint(1, 3)):
            cat = rng.choice(CATEGORIES)["id"]
            w, h = rng.randint(20, 100), rng.randint(20, 100)
            x, y = rng.randint(0, SIZE[0] - w), rng.randint(0, SIZE[1] - h)
            shape = draw.rectangle if cat == 1 else draw.ellipse
            shape([x, y, x + w, y + h], fill=(255, 0, 0) if cat == 1 else (0, 0, 255))
            annotations.append(
                {"id": len(annotations) + 1, "image_id": i, "category_id": cat,
                 "bbox": [x, y, w, h], "area": w * h, "iscrowd": 0}
            )
        img.save(out / "images" / f"{name}.png")
        images.append({"id": i, "file_name": f"{name}.png", "width": SIZE[0], "height": SIZE[1]})
        # Fields follow CVAT's dataset_manifest images format (checksum is optional).
        manifest.append(json.dumps(
            {"name": name, "extension": ".png", "width": SIZE[0], "height": SIZE[1]},
            separators=(",", ":"),
        ))
    coco = {"info": {"description": "synthetic"}, "categories": CATEGORIES,
            "images": images, "annotations": annotations}
    (out / "annotations" / "instances.json").write_text(json.dumps(coco, indent=1, sort_keys=True))
    (out / "manifest.jsonl").write_text("\n".join(manifest) + "\n")
    _write_dataset_metadata(out, count)
