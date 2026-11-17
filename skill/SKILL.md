---
name: b2-ai-data-provider
description: Design or review Backblaze B2 storage for AI data providers, including CVAT, Label Studio, Dataloop DDOE, Supervisely, FiftyOne, or Roboflow workflows, validation, versioned releases, customer delivery, and refresh. Use for dataset storage boundaries, key scoping, release contracts, Object Lock, presigned delivery, or event-driven dataset pipelines.
---

# B2 for AI data providers

Choose a workflow from the bundled [architecture catalog](references/architecture-catalog.md), which also lists related B2 sample applications. For release manifests, dataset cards, Croissant metadata, and delivery bundles, read [release contract](references/release-contract.md).

For changing service behavior, limits, and setup steps, use the canonical [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage). Link pricing claims to [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) instead of copying numbers.

## Rules
- Use the S3-compatible API. Derive `https://s3.<region>.backblazeb2.com` from `B2_REGION`; never hardcode region or endpoint.
- Env: `B2_APPLICATION_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET_NAME`, `B2_REGION`, optional `B2_ENDPOINT`. Secrets in gitignored 0600 `.env`; never print keys.
- A key scopes to one bucket + one prefix + capabilities. Design roles around that (ingest-writer, cvat-source-reader, cvat-export-writer, validator-reader, publisher, delivery-signer). Master key only for provisioning.
- Bucket names are globally unique; expect collisions.
- Released versions: Object Lock (governance default; compliance and enabling lock are irreversible), `manifest.json` written last, never overwrite a version.
- Delivery: short-TTL presigned URLs from a read-only prefix-scoped key; treat URL lists as secrets. Cloud Replication is bucket-to-bucket DR, not delivery.
- Lifecycle uses B2 semantics (hide, then delete). Events: webhook, at-least-once, verify `X-Bz-Event-Notification-Signature`, ack fast, be idempotent.
- Link to B2 pricing; do not restate numbers.
- CVAT: provider Amazon S3 + Endpoint URL. Keep CVAT's databases and UI caching off B2.
- Label Studio: Amazon S3 source and target storage + S3 Endpoint. Choose presigned browser reads with narrow CORS or proxy delivery through Label Studio; keep its database and queues off B2.
- Dataloop DDOE: configure the On-Prem S3 API integration with the regional B2 endpoint and bucket region; separate read-only source data from writable platform derivatives.
- Supervisely: distinguish instance-wide remote storage from team imports and remote links; configure the `minio` provider with endpoint `s3.<region>.backblazeb2.com` and record whether the selected flow links or copies objects.
- FiftyOne Enterprise: configure the MinIO cloud credential profile with `endpoint_url=https://s3.<region>.backblazeb2.com` and the bucket region; use one canonical media path form across App, SDK, and operators; do not store expiring URLs as durable sample paths.
- Roboflow: use presigned-URL API imports for bounded batches, or a Roboflow Datasource configured with the B2 endpoint (path-style off) for continuous sync. Treat imported objects as copies across a processor boundary.
- Overdrive only for sustained high-throughput reads; otherwise Standard B2.

## Release contract

- Keep `manifest.json` deterministic and operational: identity, version, provenance class, validation status, counts, content fingerprint, and per-file SHA-256.
- Keep buyer-facing rights, consent, limitations, sensitive-data posture, bias, and intended use in a dataset card.
- Add Croissant JSON-LD for machine discovery and ML loading.
- Generate delivery manifests on demand; they contain expiring bearer URLs and must not be stored with the release.

## Verify

When operating inside the full repository, use its `AGENTS.md` validation commands. When this skill is installed by itself, use the linked product and integration documentation for configuration and service behavior.
