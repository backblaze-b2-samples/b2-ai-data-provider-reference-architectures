"""Serialize cooperating publishers on one host using persistent OS lock files."""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

from filelock import FileLock, Timeout


class PublisherLockError(Exception):
    pass


class PublisherBusy(PublisherLockError):
    pass


@contextmanager
def writer_lock(client, bucket: str, scope: str, *, timeout: float = 30):
    # Credentials and checkout paths must not create separate locks for the same objects.
    identity = json.dumps([client.meta.endpoint_url.rstrip("/"), bucket, scope])
    name = hashlib.sha256(identity.encode()).hexdigest()
    directory = Path(os.environ.get("CVAT_B2_LOCK_DIR") or Path.home() / ".cache/cvat-b2/locks").expanduser().resolve()
    try:
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        lock = FileLock(directory / f"{name}.lock", mode=0o600)
        lock.acquire(timeout=timeout)
    except Timeout as error:
        raise PublisherBusy("another publisher is writing this release or object; retry after it finishes") from error
    except OSError as error:
        raise PublisherLockError("cannot open publisher locks; set CVAT_B2_LOCK_DIR to a writable persistent directory") from error
    try:
        yield
    finally:
        # Keep the file: unlinking it can let another process lock a different inode.
        lock.release()
