import json

import pytest

from cvat_b2_pipeline import manifest, synth, validate


def test_generate_is_deterministic(tmp_path):
    synth.generate(tmp_path / "a", 3, seed=7)
    synth.generate(tmp_path / "b", 3, seed=7)
    ma, mb = (manifest.build(tmp_path / d, "d", "v1") for d in "ab")
    assert ma == mb


def test_cvat_manifest_header(dataset):
    lines = (dataset / "manifest.jsonl").read_text().splitlines()
    assert lines[:2] == ['{"version":"1.1"}', '{"type":"images"}']
    assert json.loads(lines[2])["extension"] == ".png"


def test_valid_dataset_passes(dataset):
    release = manifest.build(dataset, "d", "v1")
    assert validate.validate_dataset(dataset, release) == []
    assert release["schema_version"] == "2.0.0" and release["id"] == "d@v1"
    assert release["quality"]["status"] == "pending"
    assert {"README.md", "croissant.json"} <= {item["path"] for item in release["files"]}
    assert release["statistics"]["file_count"] == len(release["files"])
    assert release["statistics"]["total_bytes"] == sum(item["size"] for item in release["files"])


def test_bad_bbox_and_unknown_category_fail(dataset):
    p = dataset / "annotations" / "instances.json"
    coco = json.loads(p.read_text())
    coco["annotations"][0]["bbox"] = [-1, 0, 10, 10]
    coco["annotations"][1]["category_id"] = 99
    p.write_text(json.dumps(coco))
    errs = validate.validate_dataset(dataset, manifest.build(dataset, "d", "v1"))
    assert any("outside image bounds" in e for e in errs)
    assert any("unknown category_id" in e for e in errs)


def test_checksum_mismatch_detected(dataset):
    m = manifest.build(dataset, "d", "v1")
    (dataset / "images" / "img_0001.png").write_bytes(b"tampered")
    assert any("checksum mismatch" in e for e in validate.validate_dataset(dataset, m))


@pytest.mark.parametrize("section", ["images", "categories", "annotations"])
def test_duplicate_ids_are_rejected(dataset, section):
    path = dataset / "annotations/instances.json"
    coco = json.loads(path.read_text())
    coco[section].append(dict(coco[section][0]))
    path.write_text(json.dumps(coco))
    errors = validate.validate_dataset(dataset, manifest.build(dataset, "toy", "v1"))
    assert any("duplicate" in error and section in error for error in errors)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, "10", None, 10**400])
def test_invalid_bbox_numbers_are_rejected(dataset, value):
    path = dataset / "annotations/instances.json"
    coco = json.loads(path.read_text())
    coco["annotations"][0]["bbox"][0] = value
    path.write_text(json.dumps(coco))
    assert validate.validate_dataset(dataset, manifest.build(dataset, "toy", "v1"))


@pytest.mark.parametrize("content", ["{", "[]", '{"images": null}',
    '{"images": [], "categories": [], "annotations": []}',
    '{"images": [null], "categories": [], "annotations": []}',
    '{"images": [], "categories": [], "annotations": [{"id": 1}]}'])
def test_malformed_annotation_structure_returns_errors(dataset, content):
    (dataset / "annotations/instances.json").write_text(content)
    assert validate.validate_dataset(dataset, manifest.build(dataset, "toy", "v1"))


@pytest.mark.parametrize("bbox", [[], [1, 2, 3], {"x": 1}, [0, 0, 1e309, 1]])
def test_bbox_shape_and_overflow_are_rejected(dataset, bbox):
    path = dataset / "annotations/instances.json"
    coco = json.loads(path.read_text())
    coco["annotations"][0]["bbox"] = bbox
    path.write_text(json.dumps(coco).replace("Infinity", "1e999"))
    assert validate.validate_dataset(dataset, manifest.build(dataset, "toy", "v1"))
