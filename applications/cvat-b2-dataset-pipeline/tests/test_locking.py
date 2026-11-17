"""Publisher locks coordinate independent processes and recover on process exit."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from cvat_b2_pipeline import locking

CLIENT = SimpleNamespace(meta=SimpleNamespace(endpoint_url="https://s3.example.test"))
CHILD = """
from types import SimpleNamespace
from cvat_b2_pipeline import locking
c = SimpleNamespace(meta=SimpleNamespace(endpoint_url='https://s3.example.test'))
try:
    with locking.writer_lock(c, 'bucket', 'release:toy/v1', timeout=0):
        pass
except locking.PublisherBusy:
    raise SystemExit(42)
"""


def child_env():
    return {**os.environ, "PYTHONPATH": str(Path(locking.__file__).resolve().parents[1]),
            "PYTHONDONTWRITEBYTECODE": "1"}


def test_release_lock_excludes_another_process_and_releases_afterwards(tmp_path):
    with locking.writer_lock(CLIENT, "bucket", "release:toy/v1"):
        child = subprocess.run([sys.executable, "-B", "-c", CHILD], cwd=tmp_path,
                               env=child_env(), capture_output=True, timeout=10)
        assert child.returncode == 42, child.stderr.decode()
    child = subprocess.run([sys.executable, "-B", "-c", CHILD], cwd=tmp_path,
                           env=child_env(), capture_output=True, timeout=10)
    assert child.returncode == 0, child.stderr.decode()


def test_process_exit_releases_lock(tmp_path):
    script = """
import os
from types import SimpleNamespace
from cvat_b2_pipeline import locking
c = SimpleNamespace(meta=SimpleNamespace(endpoint_url='https://s3.example.test'))
with locking.writer_lock(c, 'bucket', 'release:toy/v1', timeout=0):
    os._exit(0)
"""
    child = subprocess.run([sys.executable, "-B", "-c", script], cwd=tmp_path,
                           env=child_env(), capture_output=True, timeout=10)
    assert child.returncode == 0, child.stderr.decode()
    with locking.writer_lock(CLIENT, "bucket", "release:toy/v1", timeout=0):
        pass


def test_unusable_directory_has_an_actionable_error(tmp_path, monkeypatch):
    file = tmp_path / "occupied"
    file.write_text("not a directory")
    monkeypatch.setenv("CVAT_B2_LOCK_DIR", str(file))
    with pytest.raises(locking.PublisherLockError, match="CVAT_B2_LOCK_DIR"):
        with locking.writer_lock(CLIENT, "bucket", "release:toy/v1", timeout=0):
            pytest.fail("an unusable lock directory must block publication")
