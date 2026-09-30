"""B2 access over the S3-compatible API: idempotent uploads, verification, presigning."""
from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from . import layout
from .config import Config
from .manifest import sha256_file

MB = 1 << 20


class StorageError(Exception):
    pass


class Collision(StorageError):
    """Same key already holds different content and overwrite is not allowed."""


def make_client(cfg: Config):
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint,
        region_name=cfg.region,
        aws_access_key_id=cfg.key_id,
        aws_secret_access_key=cfg.key,
        config=BotoConfig(
            signature_version="s3v4",
            retries={"max_attempts": 5, "mode": "standard"},  # backoff on 429/503
            # SDK default CRC checksums are not needed by B2; send them only when required.
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def _code(err: ClientError) -> str:
    return err.response.get("Error", {}).get("Code", "")


def check_bucket(client, bucket: str) -> None:
    """Fail fast with an actionable message. Bucket names are globally unique on B2."""
    try:
        client.head_bucket(Bucket=bucket)
    except ClientError as e:
        if _code(e) in ("403", "AccessDenied"):
            raise StorageError(
                f"bucket '{bucket}' is not accessible: it belongs to another account, "
                "or the key is not scoped to it"
            ) from e
        if _code(e) in ("404", "NoSuchBucket"):
            raise StorageError(f"bucket '{bucket}' does not exist; create it first") from e
        raise


def _stored_sha(client, bucket: str, key: str) -> str | None:
    try:
        return client.head_object(Bucket=bucket, Key=key)["Metadata"].get("sha256", "")
    except ClientError as e:
        if _code(e) in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def _lock_args(lock_days: int | None) -> dict:
    if not lock_days:
        return {}
    until = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=lock_days)
    return {"ObjectLockMode": "GOVERNANCE", "ObjectLockRetainUntilDate": until}


def _guard(existing: str | None, sha: str, key: str, overwrite: bool) -> bool:
    """True if an upload is needed. Identical content is skipped so reruns add no versions."""
    if existing == sha:
        return False
    if existing is not None and not overwrite:
        raise Collision(f"{key} already exists with different content")
    return True


def put_file(client, bucket, key, path: Path, *, overwrite=True, lock_days=None,
             multipart_mb=64) -> str:
    sha = sha256_file(path)
    if not _guard(_stored_sha(client, bucket, key), sha, key, overwrite):
        return "skipped"
    client.upload_file(  # multipart above the threshold
        str(path), bucket, key,
        ExtraArgs={"Metadata": {"sha256": sha}, **_lock_args(lock_days)},
        Config=TransferConfig(multipart_threshold=multipart_mb * MB,
                              multipart_chunksize=max(multipart_mb, 5) * MB),
    )
    return "uploaded"


def put_bytes(client, bucket, key, data: bytes, sha: str, *, overwrite=True, lock_days=None) -> str:
    if not _guard(_stored_sha(client, bucket, key), sha, key, overwrite):
        return "skipped"
    client.put_object(Bucket=bucket, Key=key, Body=data, Metadata={"sha256": sha},
                      **_lock_args(lock_days))
    return "uploaded"


def upload_tree(client, bucket, items: list[tuple[str, Path]], *, workers=4, **kw) -> dict[str, int]:
    """Upload (key, path) pairs with a bounded pool; parallelism is per file, not per part."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda kp: put_file(client, bucket, kp[0], kp[1], **kw), items))
    return {s: results.count(s) for s in ("uploaded", "skipped")}


def verify_release(client, bucket, dataset, version, manifest) -> list[str]:
    """Compare remote size and stored checksum against the manifest."""
    errors = []
    base = layout.release_prefix(dataset, version)
    for f in manifest["files"]:
        try:
            head = client.head_object(Bucket=bucket, Key=base + f["path"])
        except ClientError as e:
            errors.append(f"{f['path']}: {_code(e)}")
            continue
        if head["ContentLength"] != f["size"] or head["Metadata"].get("sha256") != f["sha256"]:
            errors.append(f"{f['path']}: remote content differs from manifest")
    return errors


def load_manifest(client, bucket, dataset, version) -> dict:
    try:
        body = client.get_object(Bucket=bucket, Key=layout.release_manifest_key(dataset, version))
    except ClientError as e:
        if _code(e) in ("404", "NoSuchKey"):
            raise StorageError(f"release {dataset}/{version} not found (manifest missing)") from e
        raise
    return json.loads(body["Body"].read())


def presign_get(client, bucket, key, ttl: int) -> str:
    return client.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl)
