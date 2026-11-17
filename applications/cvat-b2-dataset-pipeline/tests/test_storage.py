import datetime as dt
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from botocore.exceptions import ClientError

from cvat_b2_pipeline import storage

B = "test-cvat-b2-bucket"


def test_put_file_idempotent_and_no_extra_versions(s3, tmp_path):
    s3.put_bucket_versioning(Bucket=B, VersioningConfiguration={"Status": "Enabled"})
    f = tmp_path / "a.bin"; f.write_bytes(b"x" * 10)
    assert storage.put_file(s3, B, "k", f) == "uploaded"
    assert storage.put_file(s3, B, "k", f) == "skipped"
    assert len(s3.list_object_versions(Bucket=B)["Versions"]) == 1


def test_collision_refused_when_overwrite_false(s3, tmp_path):
    f = tmp_path / "a.bin"; f.write_bytes(b"one")
    storage.put_file(s3, B, "k", f, overwrite=False)
    f.write_bytes(b"two")
    with pytest.raises(storage.Collision):
        storage.put_file(s3, B, "k", f, overwrite=False)


def test_multipart_path(s3, tmp_path):
    f = tmp_path / "big.bin"; f.write_bytes(b"a" * (11 * storage.MB))
    # threshold 5 MB forces multipart; chunk size floor is 5 MB
    assert storage.put_file(s3, B, "big", f, multipart_mb=5) == "uploaded"
    assert s3.head_object(Bucket=B, Key="big")["ContentLength"] == 11 * storage.MB


def test_check_bucket_missing(s3):
    with pytest.raises(storage.StorageError, match="does not exist"):
        storage.check_bucket(s3, "no-such-bucket-xyz")


def test_lock_args_only_when_requested():
    assert storage._lock_args(None) == {}
    a = storage._lock_args(7)
    assert a["ObjectLockMode"] == "GOVERNANCE" and "ObjectLockRetainUntilDate" in a


def test_presign_get_has_expiry_and_no_secret(s3, cfg):
    url = storage.presign_get(s3, B, "k", 600)
    assert "Expires=600" in url or "X-Amz-Expires=600" in url
    assert cfg.key not in url


@pytest.mark.parametrize("kind", ["file", "bytes"])
def test_existing_object_gains_retention_without_an_extra_version(s3, tmp_path, kind):
    bucket = "retention-test-bucket"
    s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
    data = b"same bytes"
    path = tmp_path / "payload.bin"
    path.write_bytes(data)
    sha = hashlib.sha256(data).hexdigest()
    def put(**kwargs):
        if kind == "file":
            return storage.put_file(s3, bucket, "payload", path, overwrite=False, **kwargs)
        return storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False, **kwargs)
    assert put() == "uploaded"
    version = s3.head_object(Bucket=bucket, Key="payload")["VersionId"]
    assert put(lock_days=1) == "skipped"
    head = s3.head_object(Bucket=bucket, Key="payload", VersionId=version)
    assert head["ObjectLockMode"] == "GOVERNANCE"
    assert head["ObjectLockRetainUntilDate"] >= dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1, seconds=-2)
    assert len(s3.list_object_versions(Bucket=bucket)["Versions"]) == 1


@pytest.mark.parametrize("mode,days", [("GOVERNANCE", 3), ("COMPLIANCE", 3), ("COMPLIANCE", 0.5)])
def test_retention_never_weakens_existing_protection(s3, mode, days):
    bucket = "retention-test-bucket"
    s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
    data = b"protected"
    sha = hashlib.sha256(data).hexdigest()
    until = dt.datetime.now(dt.timezone.utc).replace(microsecond=0) + dt.timedelta(days=days)
    s3.put_object(Bucket=bucket, Key="payload", Body=data, Metadata={"sha256": sha},
                  ObjectLockMode=mode, ObjectLockRetainUntilDate=until)
    assert storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False, lock_days=1) == "skipped"
    head = s3.head_object(Bucket=bucket, Key="payload")
    assert head["ObjectLockMode"] == mode
    assert head["ObjectLockRetainUntilDate"] >= until


def test_missing_retention_visibility_fails_instead_of_reporting_success(s3, monkeypatch):
    bucket = "retention-test-bucket"
    s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
    data = b"protected"
    sha = hashlib.sha256(data).hexdigest()
    storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False)
    def denied_retention(**kwargs):
        raise ClientError({"Error": {"Code": "AccessDenied"}}, "GetObjectRetention")
    monkeypatch.setattr(s3, "get_object_retention", denied_retention)
    with pytest.raises(storage.StorageError, match="readFileRetentions"):
        storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False, lock_days=1)


@pytest.mark.parametrize("kind", ["file", "bytes"])
def test_new_upload_applies_retention(s3, tmp_path, kind):
    bucket = "retention-test-bucket"
    s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
    data = b"new protected object"
    if kind == "file":
        path = tmp_path / "payload.bin"
        path.write_bytes(data)
        result = storage.put_file(s3, bucket, "payload", path, overwrite=False, lock_days=1)
    else:
        result = storage.put_bytes(s3, bucket, "payload", data, hashlib.sha256(data).hexdigest(),
                                   overwrite=False, lock_days=1)
    assert result == "uploaded"
    assert s3.head_object(Bucket=bucket, Key="payload")["ObjectLockMode"] == "GOVERNANCE"


def test_unconfirmed_retention_update_fails(s3, monkeypatch):
    bucket = "retention-test-bucket"
    s3.create_bucket(Bucket=bucket, ObjectLockEnabledForBucket=True)
    data = b"existing object"
    sha = hashlib.sha256(data).hexdigest()
    storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False)
    monkeypatch.setattr(s3, "put_object_retention", lambda **kwargs: {})
    with pytest.raises(storage.StorageError, match="cannot verify requested retention"):
        storage.put_bytes(s3, bucket, "payload", data, sha, overwrite=False, lock_days=1)


def test_concurrent_no_overwrite_bytes_do_not_create_two_versions(s3, monkeypatch):
    s3.put_bucket_versioning(Bucket=B, VersioningConfiguration={"Status": "Enabled"})
    started, finish = threading.Event(), threading.Event()
    second_read = threading.Event()
    identity = threading.local()
    put_object = s3.put_object
    stored_sha = storage._stored_sha
    def observed_head(*args):
        if getattr(identity, "second", False):
            second_read.set()
        return stored_sha(*args)
    def paused_put(**kwargs):
        started.set()
        assert finish.wait(10)
        return put_object(**kwargs)
    monkeypatch.setattr(s3, "put_object", paused_put)
    monkeypatch.setattr(storage, "_stored_sha", observed_head)
    def put(data):
        identity.second = data == b"other"
        return storage.put_bytes(s3, B, "concurrent", data, hashlib.sha256(data).hexdigest(), overwrite=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(put, b"first")
        assert started.wait(10)
        second = pool.submit(put, b"other")
        try:
            assert not second_read.wait(0.2), "the second existence check must wait for the first write"
        finally:
            finish.set()
        assert first.result(timeout=10) == "uploaded"
        with pytest.raises(storage.Collision):
            second.result(timeout=10)
    assert len(s3.list_object_versions(Bucket=B)["Versions"]) == 1
