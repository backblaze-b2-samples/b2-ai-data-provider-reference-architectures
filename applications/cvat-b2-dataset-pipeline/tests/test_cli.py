import json
import os
import stat
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from cvat_b2_pipeline import cli, layout, manifest, storage

B = "test-cvat-b2-bucket"


def test_end_to_end_and_idempotent_rerun(s3, run, dataset, tmp_path, capsys):
    args = ["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]
    assert run(["ingest", "--src", str(dataset), "--batch", "b1"]) == 0
    assert run(args) == 0
    capsys.readouterr()
    assert run(args) == 0  # rerun uploads nothing new
    assert "'uploaded': 0" in capsys.readouterr().out
    keys = {o["Key"] for o in s3.list_objects_v2(Bucket=B)["Contents"]}
    assert layout.release_manifest_key("toy", "v1") in keys
    assert "raw/b1/manifest.jsonl" in keys and "exports/b1/annotations/instances.json" in keys
    cvat_manifest = s3.get_object(Bucket=B, Key="raw/b1/manifest.jsonl")["Body"].read().decode()
    for line in cvat_manifest.splitlines()[2:]:
        image = json.loads(line)
        assert "raw/b1/" + image["name"] + image["extension"] in keys
    release = json.loads(s3.get_object(Bucket=B, Key=layout.release_manifest_key("toy", "v1"))["Body"].read())
    assert release["quality"]["status"] == "passed"
    assert {"README.md", "croissant.json"} <= {item["path"] for item in release["files"]}


def test_release_collision_on_changed_content(s3, run, dataset, capsys):
    args = ["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]
    assert run(args) == 0
    p = dataset / "annotations" / "instances.json"
    coco = json.loads(p.read_text()); coco["info"]["description"] = "changed"
    p.write_text(json.dumps(coco))
    assert run(args) == 1
    assert "already exists with different content" in capsys.readouterr().err


def test_release_blocked_by_validation(s3, run, dataset, capsys):
    p = dataset / "annotations" / "instances.json"
    coco = json.loads(p.read_text()); coco["annotations"][0]["bbox"] = [0, 0, 0, 0]
    p.write_text(json.dumps(coco))
    assert run(["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]) == 2
    assert "Contents" not in s3.list_objects_v2(Bucket=B)


def test_deliver_writes_0600_and_prints_no_urls_or_secrets(s3, run, dataset, tmp_path, capsys, cfg):
    run(["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"])
    capsys.readouterr()
    out = tmp_path / "delivery.json"
    assert run(["deliver", "--dataset", "toy", "--version", "v1", "--out", str(out)]) == 0
    printed = capsys.readouterr()
    assert "X-Amz-Signature" not in printed.out + printed.err and cfg.key not in printed.out
    assert stat.S_IMODE(os.stat(out).st_mode) == 0o600
    urls = json.loads(out.read_text())["urls"]
    assert {"manifest.json", "annotations/instances.json", "README.md", "croissant.json"} <= urls.keys()


def test_deliver_unknown_release_and_bad_ttl(s3, run, capsys):
    assert run(["deliver", "--dataset", "nope", "--version", "v9"]) == 1
    assert run(["deliver", "--dataset", "nope", "--version", "v9", "--ttl-seconds", "0"]) == 1


def test_missing_env_exits_cleanly(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    for n in ("B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY", "B2_BUCKET_NAME", "B2_REGION"):
        monkeypatch.delenv(n, raising=False)
    assert cli.main(["deliver", "--dataset", "a", "--version", "b"]) == 1
    assert "missing required env vars" in capsys.readouterr().err


@pytest.mark.parametrize("field,value", [("--dataset", "Bad Dataset"), ("--version", "V1"),
                                        ("--dataset", "../toy"), ("--version", "")])
def test_invalid_release_identifier_is_rejected_before_storage(run, dataset, monkeypatch, field, value):
    def unexpected_client(_cfg):
        pytest.fail("invalid release must not contact storage")
    monkeypatch.setattr(storage, "make_client", unexpected_client)
    args = ["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1", field, value]
    assert run(args) == 2


@pytest.mark.parametrize("problem", ["duplicate", "non-finite", "missing-field"])
def test_bad_coco_never_uploads(run, dataset, monkeypatch, problem):
    path = dataset / "annotations/instances.json"
    coco = json.loads(path.read_text())
    if problem == "duplicate":
        coco["annotations"][1]["id"] = coco["annotations"][0]["id"]
    elif problem == "non-finite":
        coco["annotations"][0]["bbox"][0] = float("nan")
    else:
        del coco["annotations"][0]["bbox"]
    path.write_text(json.dumps(coco))
    monkeypatch.setattr(storage, "make_client", lambda _cfg: pytest.fail("invalid data must not upload"))
    assert run(["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]) == 2


@pytest.mark.parametrize("days", ["0", "-1", "3001"])
def test_invalid_retention_never_uploads(run, dataset, monkeypatch, days):
    monkeypatch.setattr(storage, "make_client", lambda _cfg: pytest.fail("invalid retention must not upload"))
    assert run(["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1", "--lock-days", days]) == 1


def test_concurrent_release_is_rejected_before_any_overwrite(s3, run, dataset, tmp_path, monkeypatch):
    other = tmp_path / "other"
    from shutil import copytree
    copytree(dataset, other)
    annotations = other / "annotations/instances.json"
    coco = json.loads(annotations.read_text())
    coco["info"]["description"] = "a competing release"
    annotations.write_text(json.dumps(coco))
    entered, finish = threading.Event(), threading.Event()
    publish = cli._publish_release

    def paused_publish(*args):
        entered.set()
        assert finish.wait(10)
        return publish(*args)

    monkeypatch.setattr(cli, "_publish_release", paused_publish)
    args = ["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(run, args)
        try:
            assert entered.wait(10)
            assert run(["release", "--src", str(other), "--dataset", "toy", "--version", "v1"]) == 1
            assert "Contents" not in s3.list_objects_v2(Bucket=B)
        finally:
            finish.set()
        assert first.result(timeout=10) == 0
    published = json.loads(s3.get_object(Bucket=B, Key=layout.release_manifest_key("toy", "v1"))["Body"].read())
    assert published["fingerprint"] == manifest.build(dataset, "toy", "v1")["fingerprint"]


def test_rerun_applies_retention_to_all_existing_versions(s3, run, dataset):
    s3.put_bucket_versioning(Bucket=B, VersioningConfiguration={"Status": "Enabled"})
    s3.put_object_lock_configuration(Bucket=B, ObjectLockConfiguration={"ObjectLockEnabled": "Enabled"})
    args = ["release", "--src", str(dataset), "--dataset", "toy", "--version", "v1"]
    assert run(args) == 0
    before = {item["Key"]: item["VersionId"] for item in s3.list_object_versions(Bucket=B)["Versions"]}
    assert run(args + ["--lock-days", "1"]) == 0
    after = {item["Key"]: item["VersionId"] for item in s3.list_object_versions(Bucket=B)["Versions"]}
    assert after == before
    for key, version in after.items():
        head = s3.head_object(Bucket=B, Key=key, VersionId=version)
        assert head["ObjectLockMode"] == "GOVERNANCE"
        assert "ObjectLockRetainUntilDate" in head
