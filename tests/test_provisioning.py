"""Connection credentials include the capability needed for bucket preflights."""
import shlex
from pathlib import Path

import pytest


@pytest.mark.parametrize("role", ["ingest-writer", "cvat-source-reader", "cvat-export-writer", "publisher"])
def test_connection_keys_can_check_bucket(role):
    readme = (Path(__file__).resolve().parents[1] / "examples/README.md").read_text()
    commands = [shlex.split(line, comments=True) for line in readme.splitlines()
                if line.startswith("b2 key create ")]
    command = next(command for command in commands if role in command)
    assert "--bucket" in command and "--name-prefix" in command
    assert {"listBuckets", "readFiles"} <= set(command[-1].split(","))
