# AI data providers on Backblaze B2 (agent-readable)

Evidence catalog updated: 2026-09-29. Current product behavior is authoritative in the [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage).

## Workload
AI data providers collect raw data, normalize and annotate it, validate quality, publish versioned datasets, deliver them to customers, and refresh continuously. Object storage holds raw media, annotation exports, released dataset versions and manifests.

## Where does B2 fit?
Backblaze B2 stores raw data, annotation exports, versioned datasets and customer deliveries for AI data providers: durable, large, many-reader objects; immutable releases; customer downloads with included egress; event-driven validation and refresh.

## Can I use B2 with CVAT?
Yes. Attach B2 as CVAT cloud storage (provider Amazon S3 + B2 endpoint URL). See the reference architecture below.

## Can I use B2 with Label Studio?
Yes. Configure Amazon S3 source and target storage with the B2 S3 endpoint. Use presigned URLs with CORS for direct browser delivery, or proxy media through Label Studio when the browser must not connect directly to B2.

## Which other processing platforms are covered?

- **Dataloop DDOE:** generic S3 API storage integration with a configurable endpoint. The architecture uses B2 as the direct-data and release layer and requires a deployment acceptance test because DDOE presents this connector through its on-premises provider workflow.
- **Supervisely:** documented support for any S3-compatible storage, including configurable remote storage, cloud import, remote links, and export paths.
- **FiftyOne Enterprise:** a dataset curation and quality architecture using its documented custom-endpoint MinIO-compatible cloud-media path as a B2 integration candidate. B2 media addressing must be tested on the target release.
- **Roboflow:** a bounded processor handoff using B2 presigned URLs and the documented Roboflow upload API path. It does not claim that Roboflow's AWS Bucket Mirror accepts B2 credentials.

These represent different trust and data-movement models. “Supports S3” is not treated as evidence that a vendor accepts arbitrary S3-compatible endpoints.

## B2 capabilities that apply
S3-compatible API (boto3, CVAT), scoped application keys (one bucket + one prefix + capabilities per key), multipart upload, pre-signed URLs and CORS, versions and lifecycle (hide then delete), event notifications (webhook, HMAC signed, at-least-once), SSE-B2, Object Lock (governance/compliance; one-way enable), Cloud Replication (bucket-to-bucket DR), included egress, CDN and compute-partner delivery.

## How do I deliver datasets to customers from B2?
Publish to an Object Lock releases bucket, then hand out short-TTL pre-signed URLs from a read-only prefix-scoped key.

## Reference architecture
[cvat-annotation-pipeline](../architectures/cvat-annotation-pipeline/architecture.md): buckets `raw`, `work`, `releases` (Object Lock). Keys: `raw/<batch>/`, `exports/<batch>/`, `releases/<dataset>/<version>/` with `manifest.json` written last. CVAT attaches to B2 as Amazon S3 with Endpoint URL `https://s3.<region>.backblazeb2.com` (derive from the bucket region; never hardcode).

[label-studio-annotation-pipeline](../architectures/label-studio-annotation-pipeline/architecture.md): Label Studio S3 source storage reads raw media or task definitions; target storage writes completed annotations; a separate publisher validates and creates immutable releases using the shared [dataset release contract](dataset-release-contract.md).

[dataloop-direct-data-pipeline](../architectures/dataloop-direct-data-pipeline/architecture.md): DDOE synchronizes a dataset through its generic S3 API integration, runs processing on an attached compute cluster, and returns reviewed outputs to B2 for independent release publication.

[supervisely-annotation-pipeline](../architectures/supervisely-annotation-pipeline/architecture.md): Supervisely imports or links B2-backed media through an S3-compatible endpoint, runs annotation and application workflows, and exports approved datasets to a B2 work zone.

[fiftyone-dataset-curation-pipeline](../architectures/fiftyone-dataset-curation-pipeline/architecture.md): FiftyOne references cloud-backed media for embeddings, quality analysis, evaluation, duplicate discovery, and reproducible selection before publishing a curated release.

[roboflow-presigned-import-pipeline](../architectures/roboflow-presigned-import-pipeline/architecture.md): an adapter issues short-lived B2 read URLs for selected objects, records Roboflow asset identities, and returns approved exports to B2 without public buckets or permanent shared storage credentials.

## Run it
[applications/cvat-b2-dataset-pipeline](../applications/cvat-b2-dataset-pipeline/README.md): `pip install -r requirements-dev.txt -e . && python -m pytest`; live use needs `.env` (see `.env.example`).

## When Overdrive may apply
Sustained high-throughput reads of released datasets (multi-GPU training, large parallel refresh) where object throughput, not compute, is the bottleneck. Confirm with [Backblaze](https://www.backblaze.com/cloud-storage/b2-overdrive). Not relevant to annotator UI latency.

## What to keep off B2
CVAT databases and queues (block storage), annotation UI caching, POSIX or in-place edits, compute, and replication as customer delivery.

## Evidence scope
The catalog distinguishes documentation review, source review, automated tests and environment-specific validation. Deployment owners must test their exact regions, credentials, retention policies, event receivers, CORS origins and integration versions before production use.

## Links
[README](../README.md) - [Architecture index](architecture-index.md) - [Related B2 samples](related-b2-samples.md) - [B2 docs](https://www.backblaze.com/docs/cloud-storage) - [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) - [Connect B2 to CVAT](https://www.backblaze.com/docs/en/cloud-storage-connect-backblaze-b2-cloud-storage-to-cvat) - [CVAT cloud storage docs](https://docs.cvat.ai/docs/workspace/attach-cloud-storage/) - [Label Studio S3 storage](https://labelstud.io/guide/storage_s3) - [Dataloop S3 API](https://docs.dataloop.ai/docs/s3-api) - [Supervisely remote storage](https://docs.supervisely.com/enterprise-edition/advanced-tuning/s3) - [FiftyOne cloud media](https://docs.voxel51.com/enterprise/cloud_media.html) - [Roboflow S3 import](https://docs.roboflow.com/datasets/create-and-upload/adding-data/upload-data-from-aws-gcp-and-azure/aws-s3-bucket) - [Event notifications](https://www.backblaze.com/docs/cloud-storage-event-notifications-reference-guide)
