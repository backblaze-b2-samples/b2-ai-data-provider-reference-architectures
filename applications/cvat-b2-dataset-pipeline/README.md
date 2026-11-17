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

Create a bucket (private) and an application key scoped to it with `listBuckets,listFiles,readFiles,writeFiles`
(add `writeFileRetentions,readFileRetentions` for `--lock-days`, which also needs an Object-Lock-enabled bucket).
`listBuckets` permits the client's `HeadBucket` preflight on the scoped bucket. Add `listAllBucketNames` only for tools that enumerate buckets. Bucket names are globally unique.

```bash
cp .env.example .env && chmod 600 .env     # fill in the key, bucket and B2_REGION; endpoint is derived
cvat-b2 generate --out out --count 12
cvat-b2 ingest  --src out --batch batch1
cvat-b2 release --src out --dataset toy --version v1        # add --lock-days 1 on a lock-enabled bucket
cvat-b2 deliver --dataset toy --version v1 --ttl-seconds 3600 --out delivery.json
```

Behavior: generation writes a dataset card and Croissant JSON-LD beside the media; releases include those sidecars when present. Reruns skip identical objects (no extra versions); changed content at an existing release version exits 1; validation failures exit 2 and upload nothing; new delivery files are created with mode `0600` and hold bearer URLs (gitignored). Set existing output files to mode `0600` before reuse. Nothing prints keys or URLs.

Dataset and version identifiers use lowercase letters, digits, `.`, `_`, and `-`. The CLI validates the release schema and COCO structure, unique IDs, finite bounding boxes, references, coverage, and checksums before contacting B2. The installed package includes a generated copy of the repository's release schema.

Run all releases for a bucket through one publisher host and one persistent lock directory. The CLI uses OS locks to exclude concurrent releases of the same dataset/version, and to serialize each object's existence check and write. The default directory is `~/.cache/cvat-b2/locks`; set `CVAT_B2_LOCK_DIR` to an absolute path to override it. Publisher containers on the same host must share that directory. Multiple producer hosts submit jobs to the same publisher service or queue. Keep lock files in place; the OS releases held locks when a process exits.

With `--lock-days`, reruns apply and verify retention on existing object versions without uploading duplicate versions. Longer retention and compliance mode are preserved. Failure to apply or verify retention exits with an error. See [B2 per-object retention](https://www.backblaze.com/apidocs/s3-put-object-retention).

Before publishing, the CLI compares each remote object's size and `sha256` metadata with the manifest. The published `manifest.json` follows the repository's [release manifest schema](../../schemas/release-manifest.schema.json). The example [dataset release contract](../../docs/dataset-release-contract.md) also defines the dataset card, Croissant metadata and delivery manifest roles.

## Tests

`python -m pytest`: config (missing env, endpoint derivation, secret not in repr), synthetic determinism, schema and COCO validation, idempotency, retention reruns, concurrent publishers, collisions, multipart path, presign, CLI end to end, 0600 delivery file, event signatures.
`RUN_B2_LIVE_TESTS=1 python -m pytest tests/test_live.py` runs an environment-specific round trip using your `.env`; use it as an acceptance test for the selected bucket, region, credentials and retention policy.
Add `B2_LIVE_LOCK_DAYS=1` to include applying and verifying one day of retention on the existing release versions; the bucket must have Object Lock enabled and the key must have both retention capabilities.
moto covers S3 data operations only; key scoping, Object Lock and lifecycle need live B2.
