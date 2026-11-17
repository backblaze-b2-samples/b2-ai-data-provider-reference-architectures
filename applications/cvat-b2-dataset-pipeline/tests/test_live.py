"""Live B2 checks (key scoping, Object Lock). Opt-in: RUN_B2_LIVE_TESTS=1 plus a .env."""
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("RUN_B2_LIVE_TESTS") != "1",
                                reason="set RUN_B2_LIVE_TESTS=1 with B2 credentials")


def test_live_release_roundtrip(tmp_path):
    from cvat_b2_pipeline import cli, layout, storage, synth
    from cvat_b2_pipeline.config import load
    synth.generate(tmp_path, 3, seed=1)
    ver = "t" + os.urandom(4).hex()  # unique version; do not reuse locked versions
    assert cli.main(["release", "--src", str(tmp_path), "--dataset", "live-test", "--version", ver]) == 0
    lock_days = os.environ.get("B2_LIVE_LOCK_DAYS")
    if lock_days:
        assert cli.main(["release", "--src", str(tmp_path), "--dataset", "live-test", "--version", ver,
                         "--lock-days", lock_days]) == 0
        cfg = load()
        client = storage.make_client(cfg)
        release = storage.load_manifest(client, cfg.bucket, "live-test", ver)
        prefix = layout.release_prefix("live-test", ver)
        for key in ["manifest.json", *(file["path"] for file in release["files"])]:
            head = client.head_object(Bucket=cfg.bucket, Key=prefix + key)
            retention = client.get_object_retention(Bucket=cfg.bucket, Key=prefix + key,
                                                     VersionId=head["VersionId"])["Retention"]
            assert retention["Mode"] in {"GOVERNANCE", "COMPLIANCE"}
            assert "RetainUntilDate" in retention
    assert cli.main(["deliver", "--dataset", "live-test", "--version", ver,
                     "--out", str(tmp_path / "d.json")]) == 0
