"""Live B2 checks (key scoping, Object Lock). Opt-in: RUN_B2_LIVE_TESTS=1 plus a .env."""
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("RUN_B2_LIVE_TESTS") != "1",
                                reason="set RUN_B2_LIVE_TESTS=1 with B2 credentials")


def test_live_release_roundtrip(tmp_path):
    from cvat_b2_pipeline import cli, synth
    synth.generate(tmp_path, 3, seed=1)
    ver = "t" + os.urandom(4).hex()  # unique version; do not reuse locked versions
    assert cli.main(["release", "--src", str(tmp_path), "--dataset", "live-test", "--version", ver]) == 0
    assert cli.main(["deliver", "--dataset", "live-test", "--version", ver,
                     "--out", str(tmp_path / "d.json")]) == 0
