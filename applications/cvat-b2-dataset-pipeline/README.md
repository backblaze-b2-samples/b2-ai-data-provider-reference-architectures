# cvat-b2-dataset-pipeline

Synthetic-data CLI for the [CVAT annotation pipeline](../../architectures/cvat-annotation-pipeline/architecture.md):
generate images + COCO annotations + dataset metadata -> stage raw and export objects on B2 -> validate -> publish a versioned release with checksums -> write pre-signed delivery URLs.
Uses the B2 S3-compatible API via boto3. No CVAT instance is needed; it produces the files CVAT would read (`manifest.jsonl`) and write (COCO export).

Capabilities demonstrated: S3 API, multipart (`--multipart-mb`), scoped keys, versions-safe idempotent uploads, Object Lock retention (`--lock-days`), validated release-contract metadata, pre-signed delivery manifests, and event-signature verification (`events.py`).

## B2's role

Durable store for raw media, exports and released dataset versions. B2 provides the objects, checksummed metadata, retention and direct customer download; the CLI provides validation and manifests.

## Setup

```bash
cd applications/cvat-b2-dataset-pipeline
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt -e .
python -m pytest            # moto-backed; no credentials needed
```

Create a bucket (private) and an application key scoped to it with `listFiles,readFiles,writeFiles`
(add `writeFileRetentions` only for `--lock-days`, which also needs an Object-Lock-enabled bucket; retention is a real commitment).
Bucket names are globally unique.

```bash
cp .env.example .env && chmod 600 .env     # fill in the key, bucket and B2_REGION; endpoint is derived
cvat-b2 generate --out out --count 12
cvat-b2 ingest  --src out --batch batch1
cvat-b2 release --src out --dataset toy --version v1        # add --lock-days 1 on a lock-enabled bucket
cvat-b2 deliver --dataset toy --version v1 --ttl-seconds 3600 --out delivery.json
```

Behavior: generation writes a dataset card and Croissant JSON-LD beside the media; releases include those sidecars when present. Reruns skip identical objects (no extra versions); changed content at an existing release version exits 1; validation failures exit 2 and upload nothing; `delivery.json` is written 0600 and holds bearer URLs (gitignored). Nothing prints keys or URLs.

The published `manifest.json` follows the repository's [release manifest schema](../../schemas/release-manifest.schema.json). The example [dataset release contract](../../docs/dataset-release-contract.md) also defines the dataset card, Croissant metadata and delivery manifest roles.

## Tests

`python -m pytest`: config (missing env, endpoint derivation, secret not in repr), synthetic determinism, validation gates, idempotency, collisions, multipart path, presign, CLI end to end, 0600 delivery file, event signatures.
`RUN_B2_LIVE_TESTS=1 python -m pytest tests/test_live.py` runs an environment-specific round trip using your `.env`; use it as an acceptance test for the selected bucket, region, credentials and retention policy.
moto covers S3 data operations only; key scoping, Object Lock and lifecycle need live B2.
