# B2 reference architectures for AI data providers

How AI data providers use Backblaze B2 across collection, normalization, dataset versioning, quality validation, publishing, customer delivery and continuous downstream refresh. Documentation first, with the smallest runnable code that proves it.

Start with the [architecture index](docs/architecture-index.md), [agent-readable summary](docs/ai-data-providers.md), or portable [agent skill](skill/SKILL.md). Current B2 product behavior is documented at [backblaze.com/docs](https://www.backblaze.com/docs/cloud-storage).

## Where does Backblaze B2 fit for AI data providers?

Backblaze B2 stores raw data, annotation exports, versioned datasets and customer deliveries for AI data providers.

- **Store in B2:** raw media, annotation exports, released dataset versions, manifests.
- **Deliver from B2:** pre-signed URLs, included egress, CDN and compute-partner paths.
- **Protect in B2:** Object Lock, versions, checksummed manifests, Cloud Replication for DR.
- **Automate with B2:** event notifications for validation and refresh.
- **Keep elsewhere:** annotation-tool databases and caches (block storage), running compute (bring your own or a compute partner).

Pricing, egress terms and limits change: see [B2 pricing](https://www.backblaze.com/cloud-storage/pricing) and the [B2 docs](https://www.backblaze.com/docs/cloud-storage).

## Architectures

<!-- catalog:architectures:start -->
| Architecture | Purpose | Resources |
|---|---|---|
| [Annotate images and video, then publish versioned datasets](architectures/cvat-annotation-pipeline/architecture.md) | Collect images, annotate in CVAT, validate COCO exports, publish immutable dataset versions, and deliver them directly from B2. | [app](applications/cvat-b2-dataset-pipeline/README.md) · [deployment](infrastructure/cvat/README.md) |
| [Annotate multimodal data with separate source and target storage](architectures/label-studio-annotation-pipeline/architecture.md) | Sync source objects into Label Studio, write completed annotations to target storage, validate them, and publish customer-ready dataset versions on B2. | [deployment](https://labelstud.io/guide/storage_s3) |
| [Process datasets in place and publish governed releases](architectures/dataloop-direct-data-pipeline/architecture.md) | Connect Dataloop DDOE to B2 through its generic S3 API integration, process datasets without making the platform the system of record, and publish governed releases back to B2. | [deployment](https://docs.dataloop.ai/docs/s3-api) |
| [Transform and annotate remote media, then release immutable datasets](architectures/supervisely-annotation-pipeline/architecture.md) | Connect Supervisely to B2 through its configurable S3-compatible storage paths, annotate or transform remote media, and publish immutable dataset releases. | [deployment](https://docs.supervisely.com/enterprise-edition/advanced-tuning/s3) |
| [Curate datasets and publish quality evidence with each release](architectures/fiftyone-dataset-curation-pipeline/architecture.md) | Reference B2-backed media from FiftyOne Enterprise, curate and evaluate datasets on compute, and publish selected samples, labels, and quality evidence as immutable releases. | [deployment](https://docs.voxel51.com/enterprise/cloud_media.html) |
| [Import to a training platform via presigned URLs and return approved exports](architectures/roboflow-presigned-import-pipeline/architecture.md) | Select B2 objects, give Roboflow time-limited read URLs for API import, process the copied assets in Roboflow, and return approved exports to governed B2 releases. | [deployment](https://docs.roboflow.com/datasets/create-and-upload/adding-data/upload-data-from-aws-gcp-and-azure/aws-s3-bucket) |
<!-- catalog:architectures:end -->

## Third-party integrations

<!-- catalog:integrations:start -->
| Tool | Role | How it connects to B2 | Architecture |
|---|---|---|---|
| [CVAT](https://docs.cvat.ai/docs/workspace/attach-cloud-storage/) | Image and video annotation, review, and dataset export | Amazon S3 cloud storage with a Backblaze B2 endpoint URL | [Annotate images and video, then publish versioned datasets](architectures/cvat-annotation-pipeline/architecture.md) |
| [Label Studio](https://labelstud.io/guide/storage_s3) | Multimodal task import, annotation, review, and annotation export | Amazon S3 source and target storage with the Backblaze B2 S3 endpoint | [Annotate multimodal data with separate source and target storage](architectures/label-studio-annotation-pipeline/architecture.md) |
| [Dataloop DDOE](https://docs.dataloop.ai/docs/s3-api) | Dataset synchronization, preprocessing, annotation, applications, pipelines, and AI workloads | Generic S3 API storage integration configured with the regional Backblaze B2 endpoint; B2-specific acceptance testing is required | [Process datasets in place and publish governed releases](architectures/dataloop-direct-data-pipeline/architecture.md) |
| [Supervisely](https://docs.supervisely.com/enterprise-edition/advanced-tuning/s3) | Image and video annotation, review, transformation, application execution, and dataset import or export | S3-compatible remote storage or team cloud storage configured with the regional Backblaze B2 endpoint | [Transform and annotate remote media, then release immutable datasets](architectures/supervisely-annotation-pipeline/architecture.md) |
| [FiftyOne Enterprise](https://docs.voxel51.com/enterprise/installation.html) | Dataset visualization, search, curation, embeddings, duplicate analysis, model evaluation, and selection | Candidate custom-endpoint connection through FiftyOne's documented MinIO-compatible cloud-media configuration; validate B2 addressing and media access before adoption | [Curate datasets and publish quality evidence with each release](architectures/fiftyone-dataset-curation-pipeline/architecture.md) |
| [Roboflow](https://docs.roboflow.com/datasets/create-and-upload/adding-data/upload-data-from-aws-gcp-and-azure/aws-s3-bucket) | Computer-vision upload, annotation, preprocessing, augmentation, dataset versioning, training, and export | One-time or scripted import through B2 presigned URLs submitted to the Roboflow API; this architecture does not claim B2 support in Roboflow Bucket Mirror | [Import to a training platform via presigned URLs and return approved exports](architectures/roboflow-presigned-import-pipeline/architecture.md) |
<!-- catalog:integrations:end -->

## Sample applications

| Name | Capabilities demonstrated | Path |
|---|---|---|
| cvat-b2-dataset-pipeline | S3 API, multipart, idempotent uploads, scoped keys, Object Lock retention, presigned delivery, event signature check | [applications/cvat-b2-dataset-pipeline](applications/cvat-b2-dataset-pipeline/README.md) |

### Related Backblaze B2 samples

| Sample | Demonstrates |
|---|---|
| [SAM 2 Mask Dataset Builder](https://github.com/backblaze-b2-samples/sam2-mask-dataset-builder) | Versioned COCO segmentation masks and derived artifacts from B2-backed images and video |
| [MMAction2 Action Dataset Builder](https://github.com/backblaze-b2-samples/mmaction2-action-dataset-builder) | Video segmentation, automated labeling, train/validation/test splits, and versioned releases |
| [NeMo Curator Training Data](https://github.com/backblaze-b2-samples/nemo-curator-training-data) | Deduplication, quality filtering, PII redaction, lineage, and versioned JSONL stages |
| [DataComp Image-Text Filtering](https://github.com/backblaze-b2-samples/datacomp-image-text-filtering) | CLIP scoring, baseline filters, duplicate removal, quality metrics, and filtered WebDataset shards |
| [Supervision Sports Highlights](https://github.com/backblaze-b2-samples/supervision-sports-highlights) | Roboflow Inference, tracking, annotation, stage manifests, and presigned media delivery |
| [img2dataset WebDataset Object Storage](https://github.com/backblaze-b2-samples/img2dataset-webdataset-object-storage) | Large-batch image-text collection, validation, and reproducible WebDataset packaging |
| [WebDataset Streaming PyTorch Training](https://github.com/backblaze-b2-samples/webdataset-streaming-pytorch-training) | Manifested shards streamed directly from B2 into distributed PyTorch training |
| [DuckDB Query-in-Place](https://github.com/backblaze-b2-samples/duckdb-query-in-place) | Validation and analysis of Parquet, CSV, and JSON in B2 with materialized output slices |
| [B2 Event Broker](https://github.com/backblaze-b2-samples/b2-event-broker) | Signed event validation, prompt acknowledgement, subscriber fan-out, and retries |
| [B2 Browser Upload](https://github.com/backblaze-b2-samples/b2-browser-upload) | Direct browser ingest with presigned S3 uploads, server-held credentials, and CORS |

See the [full sample cross-reference](docs/related-b2-samples.md) for architecture mappings, AI/data notebooks, and domain-specific robotics, autonomous-vehicle, LiDAR, medical-imaging, and reinforcement-learning examples.

## B2 capability map

| Area | Capabilities | Selection notes |
|---|---|---|
| Access | S3 API, presigned URLs, CORS, multipart, scoped keys (one bucket + one prefix + capabilities) | Default to S3 API; native API only for notifications, lock, replication setup |
| Change and lifecycle | Event notifications, versions, lifecycle (hide, then delete) | Events trigger validation and refresh; webhook must ack fast, be idempotent |
| Protection | SSE-B2, SSE-C, Object Lock, replication | Lock released versions; replication is bucket-to-bucket DR |
| Delivery | Included egress, CDN, compute partners | Presigned URLs first; CDN for hot public delivery |
| Performance | Standard B2, [Overdrive](https://www.backblaze.com/cloud-storage/b2-overdrive), local cache | Standard by default; Overdrive for sustained high-throughput training/refresh reads; local cache for repeated reads of immutable versions |

## Repository layout

`catalog/` machine-readable architecture metadata, `schemas/` validated contracts, `architectures/` docs and diagrams, `applications/` runnable samples, `examples/` B2 configs, `infrastructure/` deployment helpers, `testdata/` dataset cards and synthetic data, `manifests/` sample manifests, `skill/` portable agent skill, `docs/` agent-readable pages, `.github/` CI and templates. See [CONTRIBUTING](.github/CONTRIBUTING.md).

## Documentation and machine discovery

- [Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage) is canonical for product behavior; this repository provides workflow-specific designs and runnable examples.
- [catalog/architectures.yaml](catalog/architectures.yaml) is the source of truth for architecture and integration indexes and is validated by [JSON Schema](schemas/architecture-catalog.schema.json).
- [llms.txt](llms.txt) is a curated agent index. All narrative pages are maintained as clean Markdown.
- The canonical `backblaze.com` deployment controls crawler access; [metadata/robots.txt.example](metadata/robots.txt.example) documents the intended `OAI-SearchBot` policy without pretending that a repository file changes the domain's robots configuration.
- [Dataset release contract](docs/dataset-release-contract.md) defines operational manifests, dataset cards, Croissant metadata, and expiring delivery bundles.
- Reuse and attribution are covered by the [MIT license](LICENSE) and [citation metadata](CITATION.cff); report sensitive issues through the [security policy](.github/SECURITY.md).

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-catalog.txt
python3 tools/generate_catalog.py --check
cd applications/cvat-b2-dataset-pipeline && pip install -r requirements-dev.txt -e . && python -m pytest
```
