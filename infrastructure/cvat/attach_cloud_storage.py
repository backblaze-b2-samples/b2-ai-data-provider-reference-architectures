"""Attach a B2 bucket to CVAT as an Amazon S3 cloud storage (POST /api/cloudstorages).

Secrets come from env only, so they stay out of argv and shell history.
Env: CVAT_URL, CVAT_API_TOKEN (Personal Access Token), B2_APPLICATION_KEY_ID,
     B2_APPLICATION_KEY, B2_BUCKET_NAME, B2_REGION [, B2_ENDPOINT].
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

REQUIRED = ("CVAT_URL", "CVAT_API_TOKEN", "B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY",
            "B2_BUCKET_NAME", "B2_REGION")


def build_payload(env: dict, display_name: str, prefix: str = "", manifests=("manifest.jsonl",)) -> dict:
    endpoint = env.get("B2_ENDPOINT") or f"https://s3.{env['B2_REGION']}.backblazeb2.com"
    # CVAT parses specific_attributes as a URL query string (parse_qsl).
    attrs = {"endpoint_url": endpoint, "region": env["B2_REGION"]}
    if prefix:
        attrs["prefix"] = prefix
    return {
        "provider_type": "AWS_S3_BUCKET",  # B2 is attached as "Amazon S3" with a custom endpoint
        "resource": env["B2_BUCKET_NAME"],
        "display_name": display_name,
        "credentials_type": "KEY_SECRET_KEY_PAIR",
        "key": env["B2_APPLICATION_KEY_ID"],
        "secret_key": env["B2_APPLICATION_KEY"],
        "specific_attributes": urllib.parse.urlencode(attrs),
        "manifests": list(manifests),
    }


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--prefix", default="")
    a = ap.parse_args(argv)
    missing = [n for n in REQUIRED if not os.environ.get(n)]
    if missing:
        print(f"missing required env vars: {', '.join(missing)}", file=sys.stderr)
        return 1
    req = urllib.request.Request(
        os.environ["CVAT_URL"].rstrip("/") + "/api/cloudstorages",
        data=json.dumps(build_payload(os.environ, a.name, a.prefix)).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {os.environ['CVAT_API_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as resp:  # HTTPError propagates; body may hold field errors
        print(f"created cloud storage id={json.load(resp)['id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
