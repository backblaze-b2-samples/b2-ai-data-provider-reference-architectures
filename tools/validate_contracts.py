#!/usr/bin/env python3
"""Validate catalog, manifest examples, schemas, and generated sample metadata."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
APP_SRC = ROOT / "applications" / "cvat-b2-dataset-pipeline" / "src"
sys.path.insert(0, str(APP_SRC))

from cvat_b2_pipeline import manifest  # noqa: E402


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def validate(instance: dict, schema_path: str) -> None:
    schema = load_json(schema_path)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    ).validate(instance)


def main() -> int:
    catalog = yaml.safe_load((ROOT / "catalog" / "architectures.yaml").read_text())
    validate(catalog, "schemas/architecture-catalog.schema.json")

    release = load_json("manifests/release-manifest.example.json")
    validate(release, "schemas/release-manifest.schema.json")
    assert release["fingerprint"] == release["integrity"]["content_fingerprint"]
    assert release["statistics"]["file_count"] == len(release["files"])
    assert release["statistics"]["total_bytes"] == sum(item["size"] for item in release["files"])

    generated = manifest.build(ROOT / "testdata" / "synthetic-toy", "synthetic-toy", "v1")
    generated["quality"]["status"] = "passed"
    assert generated == release, "release-manifest.example.json is stale"

    delivery = load_json("manifests/delivery-manifest.example.json")
    validate(delivery, "schemas/delivery-manifest.schema.json")

    croissant = load_json("testdata/synthetic-toy/croissant.json")
    assert croissant["dct:conformsTo"] == "http://mlcommons.org/croissant/1.0"
    for required in ("@context", "@type", "description", "license", "name", "url", "creator", "datePublished", "distribution"):
        assert required in croissant, f"Croissant metadata missing {required}"
    annotation = next(item for item in croissant["distribution"] if item["@id"] == "annotations")
    expected_sha = next(item["sha256"] for item in release["files"] if item["path"] == "annotations/instances.json")
    assert annotation["sha256"] == expected_sha

    load_json("codemeta.json")
    print("catalog and dataset contracts valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
