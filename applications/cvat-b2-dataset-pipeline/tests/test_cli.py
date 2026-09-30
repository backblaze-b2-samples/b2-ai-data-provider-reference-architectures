import json
import os
import stat

from cvat_b2_pipeline import cli, layout

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
