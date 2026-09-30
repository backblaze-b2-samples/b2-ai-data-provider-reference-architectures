import json

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
