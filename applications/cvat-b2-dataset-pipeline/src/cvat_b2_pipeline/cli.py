"""cvat-b2: generate -> ingest -> release -> deliver."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from botocore.exceptions import ClientError

from . import layout, manifest, storage, synth, validate
from .config import ConfigError, load

MAX_TTL = 7 * 24 * 3600  # SigV4 presign ceiling; check B2 docs for its own limit


def cmd_generate(a, _cfg=None) -> int:
    synth.generate(Path(a.out), a.count, a.seed)
    print(f"generated {a.count} images in {a.out}")
    return 0


def cmd_ingest(a, cfg) -> int:
    """Stage raw images + CVAT manifest (CVAT source) and the annotation export (CVAT target)."""
    src, c = Path(a.src), storage.make_client(cfg)
    storage.check_bucket(c, cfg.bucket)
    raw, exp = layout.raw_prefix(a.batch), layout.export_prefix(a.batch)
    items = [(raw + p.relative_to(src).as_posix(), p) for p in sorted((src / "images").glob("*"))]
    items.append((raw + "manifest.jsonl", src / "manifest.jsonl"))
    items.append((exp + "annotations/instances.json", src / "annotations" / "instances.json"))
    print(storage.upload_tree(c, cfg.bucket, items, multipart_mb=a.multipart_mb))
    return 0


def cmd_release(a, cfg) -> int:
    """Validate, upload immutable release files, then write the manifest last as commit marker."""
    src = Path(a.src)
    m = manifest.build(src, a.dataset, a.version)
    errors = validate.validate_dataset(src, m)
    if errors:
        print("validation failed:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    m["quality"]["status"] = "passed"
    c = storage.make_client(cfg)
    storage.check_bucket(c, cfg.bucket)
    base = layout.release_prefix(a.dataset, a.version)
    opts = dict(overwrite=False, lock_days=a.lock_days)
    items = [(base + f["path"], src / f["path"]) for f in m["files"]]
    print(storage.upload_tree(c, cfg.bucket, items, multipart_mb=a.multipart_mb, **opts))
    remote_errors = storage.verify_release(c, cfg.bucket, a.dataset, a.version, m)
    if remote_errors:
        print("remote verification failed:\n  " + "\n  ".join(remote_errors), file=sys.stderr)
        return 3
    data = manifest.dumps(m)
    storage.put_bytes(c, cfg.bucket, layout.release_manifest_key(a.dataset, a.version), data,
                      hashlib.sha256(data).hexdigest(), **opts)
    print(f"released {a.dataset}/{a.version} fingerprint={m['fingerprint'][:12]}")
    return 0


def cmd_deliver(a, cfg) -> int:
    """Write pre-signed GET URLs for a release. The output file is a bearer credential."""
    if not 0 < a.ttl_seconds <= MAX_TTL:
        raise storage.StorageError(f"--ttl-seconds must be 1..{MAX_TTL}")
    c = storage.make_client(cfg)
    m = storage.load_manifest(c, cfg.bucket, a.dataset, a.version)
    base = layout.release_prefix(a.dataset, a.version)
    urls = {p: storage.presign_get(c, cfg.bucket, base + p, a.ttl_seconds)
            for p in [layout.MANIFEST_NAME] + [f["path"] for f in m["files"]]}
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=a.ttl_seconds)
    out = Path(a.out)
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({
            "schema_version": "2.0.0",
            "release_id": m.get("id", f"{a.dataset}@{a.version}"),
            "dataset": a.dataset,
            "version": a.version,
            "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
            "expires_in_seconds": a.ttl_seconds,
            "access": {"method": "GET", "credential_type": "presigned-url"},
            "urls": urls,
        }, f, indent=1)
    print(f"wrote {len(urls)} pre-signed URLs to {out} (valid {a.ttl_seconds}s)")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cvat-b2")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate"); g.set_defaults(fn=cmd_generate, needs_cfg=False)
    g.add_argument("--out", default="out"); g.add_argument("--count", type=int, default=12)
    g.add_argument("--seed", type=int, default=0)
    for name, fn in (("ingest", cmd_ingest), ("release", cmd_release)):
        s = sub.add_parser(name); s.set_defaults(fn=fn, needs_cfg=True)
        s.add_argument("--src", default="out")
        s.add_argument("--multipart-mb", type=int, default=64)
        if name == "ingest":
            s.add_argument("--batch", required=True)
        else:
            s.add_argument("--dataset", required=True); s.add_argument("--version", required=True)
            s.add_argument("--lock-days", type=int, default=None,
                           help="GOVERNANCE retention; bucket must have Object Lock enabled")
    d = sub.add_parser("deliver"); d.set_defaults(fn=cmd_deliver, needs_cfg=True)
    d.add_argument("--dataset", required=True); d.add_argument("--version", required=True)
    d.add_argument("--ttl-seconds", type=int, default=3600)
    d.add_argument("--out", default="delivery.json")
    return p


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        return a.fn(a, load() if a.needs_cfg else None)
    except (ConfigError, storage.StorageError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ClientError as e:  # code only; never echo request details
        print(f"error: B2 request failed: {e.response.get('Error', {}).get('Code')}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
