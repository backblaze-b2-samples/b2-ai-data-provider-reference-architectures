"""Versioned dataset manifest with per-file checksums. Deterministic for identical content."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

RELEASE_DIRS = ("images", "annotations")  # what ships to customers; CVAT's manifest.jsonl stays internal
RELEASE_FILES = ("README.md", "croissant.json")
ENCODING_FORMATS = {".json": "application/json", ".md": "text/markdown", ".png": "image/png"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(src: Path, dataset: str, version: str) -> dict:
    content_paths = [
        p
        for d in RELEASE_DIRS
        for p in sorted((src / d).rglob("*")) if p.is_file()
    ] + [src / name for name in RELEASE_FILES if (src / name).is_file()]
    files = [
        {
            "path": p.relative_to(src).as_posix(),
            "size": p.stat().st_size,
            "sha256": sha256_file(p),
            "encoding_format": ENCODING_FORMATS.get(p.suffix.lower(), "application/octet-stream"),
        }
        for p in content_paths
    ]
    # No timestamps: re-running on the same content yields the same bytes (idempotent publish).
    fingerprint = hashlib.sha256(
        "".join(f"{f['path']}:{f['sha256']}\n" for f in files).encode()
    ).hexdigest()
    return {
        "schema_version": "2.0.0",
        "id": f"{dataset}@{version}",
        "dataset": dataset,
        "version": version,
        "annotation_format": "COCO 1.0",
        "modalities": ["image"],
        "license": "MIT",
        "provenance": {
            "source_type": "synthetic",
            "generated_by": "cvat-b2-dataset-pipeline",
            "inputs": [],
        },
        "quality": {
            "status": "pending",
            "validator": "cvat_b2_pipeline.validate",
            "checks": [
                "annotation-structure",
                "category-references",
                "bounding-boxes",
                "image-annotation-coverage",
                "sha256",
            ],
        },
        "statistics": {
            "file_count": len(files),
            "total_bytes": sum(item["size"] for item in files),
        },
        "integrity": {"algorithm": "sha256", "content_fingerprint": fingerprint},
        "fingerprint": fingerprint,
        "files": files,
    }


def dumps(manifest: dict) -> bytes:
    return json.dumps(manifest, indent=1, sort_keys=True).encode()
