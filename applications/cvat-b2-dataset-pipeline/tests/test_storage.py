import pytest

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
