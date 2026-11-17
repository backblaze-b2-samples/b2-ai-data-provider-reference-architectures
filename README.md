# B2 reference architectures for AI data providers

How AI data providers use Backblaze B2 across collection, normalization, dataset versioning, quality validation, publishing, customer delivery and continuous downstream refresh. Each architecture documents the data flow, B2 zones and security boundaries, and links out to the third-party integrations and B2 sample applications that implement it.

Learn more about [Backblaze B2 for AI and machine learning](https://www.backblaze.com/cloud-storage/industries/ai-ml).

Start with the [architecture index](docs/architecture-index.md) or the [agent-readable summary](docs/ai-data-providers.md). Current B2 product behavior is documented at [backblaze.com/docs](https://www.backblaze.com/docs/cloud-storage).

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
| Tool | Role | Connection type | How it connects to B2 | Architecture |
|---|---|---|---|---|
| [CVAT](https://docs.cvat.ai/docs/workspace/attach-cloud-storage/) | Image and video annotation, review, and dataset export | S3 custom endpoint | Add cloud storage with provider Amazon S3, the bucket name, a bucket-scoped B2 application key, and Endpoint URL https://s3.<region>.backblazeb2.com ([setup guide](https://docs.cvat.ai/docs/workspace/attach-cloud-storage/#backblaze-b2)) | [Annotate images and video, then publish versioned datasets](architectures/cvat-annotation-pipeline/architecture.md) |
| [Label Studio](https://labelstud.io/guide/storage_s3) | Multimodal task import, annotation, review, and annotation export | S3 custom endpoint | Amazon S3 source and target storage with S3 Endpoint https://s3.<region>.backblazeb2.com and Region Name set to the bucket region; enable presigned URLs with CORS for direct browser reads, or proxy media through Label Studio | [Annotate multimodal data with separate source and target storage](architectures/label-studio-annotation-pipeline/architecture.md) |
| [Dataloop DDOE](https://docs.dataloop.ai/docs/s3-api) | Dataset synchronization, preprocessing, annotation, applications, pipelines, and AI workloads | S3 custom endpoint | Storage integration with provider On-Prem and type S3 API, Endpoint URL https://s3.<region>.backblazeb2.com, Region set to the bucket region, and a prefix-scoped B2 application key | [Process datasets in place and publish governed releases](architectures/dataloop-direct-data-pipeline/architecture.md) |
| [Supervisely](https://docs.supervisely.com/enterprise-edition/advanced-tuning/s3) | Image and video annotation, review, transformation, application execution, and dataset import or export | S3 custom endpoint | STORAGE_PROVIDER=minio with STORAGE_ENDPOINT=s3.<region>.backblazeb2.com and STORAGE_PORT=443 for instance storage, or a minio provider entry with the same endpoint and bucket region for remote links and team cloud storage | [Transform and annotate remote media, then release immutable datasets](architectures/supervisely-annotation-pipeline/architecture.md) |
| [FiftyOne Enterprise](https://docs.voxel51.com/enterprise/installation.html) | Dataset visualization, search, curation, embeddings, duplicate analysis, model evaluation, and selection | S3 custom endpoint | MinIO cloud credential profile with endpoint_url https://s3.<region>.backblazeb2.com, the bucket region, and a read-only B2 application key; reference media as <alias>://<bucket>/<key> ([setup guide](https://docs.voxel51.com/enterprise/installation.html#enterprise-cloud-credentials)) | [Curate datasets and publish quality evidence with each release](architectures/fiftyone-dataset-curation-pipeline/architecture.md) |
| [Roboflow](https://docs.roboflow.com/datasets/create-and-upload/adding-data/upload-data-from-aws-gcp-and-azure/aws-s3-bucket) | Computer-vision upload, annotation, preprocessing, augmentation, dataset versioning, training, and export | Presigned URLs | Submit short-lived B2 presigned GET URLs to the Roboflow upload API for bounded batches; for continuous sync, Roboflow Datasources list Backblaze B2 as an S3-compatible provider (endpoint s3.<region>.backblazeb2.com, path-style off) ([setup guide](https://docs.roboflow.com/datasets/create-and-upload/adding-data/datasources)) | [Import to a training platform via presigned URLs and return approved exports](architectures/roboflow-presigned-import-pipeline/architecture.md) |
<!-- catalog:integrations:end -->

## Sample applications

Sample applications from [`backblaze-b2-samples`](https://github.com/backblaze-b2-samples) demonstrating these storage workflows. Follow the linked repositories for source code, setup, and operating instructions.

<!-- catalog:samples:start -->
| Sample | Demonstrates | Related architectures |
|---|---|---|
| [SAM 2 Mask Dataset Builder](https://github.com/backblaze-b2-samples/sam2-mask-dataset-builder) | Versioned COCO segmentation masks and derived artifacts from B2-backed images and video | [CVAT](architectures/cvat-annotation-pipeline/architecture.md), [Label Studio](architectures/label-studio-annotation-pipeline/architecture.md), [Supervisely](architectures/supervisely-annotation-pipeline/architecture.md), [FiftyOne Enterprise](architectures/fiftyone-dataset-curation-pipeline/architecture.md) |
| [MMAction2 Action Dataset Builder](https://github.com/backblaze-b2-samples/mmaction2-action-dataset-builder) | Video segmentation, automated labeling, train/validation/test splits, and versioned releases | — |
| [NeMo Curator Training Data](https://github.com/backblaze-b2-samples/nemo-curator-training-data) | Deduplication, quality filtering, PII redaction, lineage, and versioned JSONL stages | [Dataloop DDOE](architectures/dataloop-direct-data-pipeline/architecture.md) |
| [DataComp Image-Text Filtering](https://github.com/backblaze-b2-samples/datacomp-image-text-filtering) | CLIP scoring, baseline filters, duplicate removal, quality metrics, and filtered WebDataset shards | [FiftyOne Enterprise](architectures/fiftyone-dataset-curation-pipeline/architecture.md), [Dataloop DDOE](architectures/dataloop-direct-data-pipeline/architecture.md) |
| [Supervision Sports Highlights](https://github.com/backblaze-b2-samples/supervision-sports-highlights) | Roboflow Inference, tracking, annotation, stage manifests, and presigned media delivery | [Roboflow](architectures/roboflow-presigned-import-pipeline/architecture.md) |
| [img2dataset WebDataset Object Storage](https://github.com/backblaze-b2-samples/img2dataset-webdataset-object-storage) | Large-batch image-text collection, validation, and reproducible WebDataset packaging | — |
| [WebDataset Streaming PyTorch Training](https://github.com/backblaze-b2-samples/webdataset-streaming-pytorch-training) | Manifested shards streamed directly from B2 into distributed PyTorch training | — |
| [DuckDB Query-in-Place](https://github.com/backblaze-b2-samples/duckdb-query-in-place) | Validation and analysis of Parquet, CSV, and JSON in B2 with materialized output slices | [Dataloop DDOE](architectures/dataloop-direct-data-pipeline/architecture.md), [FiftyOne Enterprise](architectures/fiftyone-dataset-curation-pipeline/architecture.md) |
| [B2 Event Broker](https://github.com/backblaze-b2-samples/b2-event-broker) | Signed event validation, prompt acknowledgement, subscriber fan-out, and retries | — |
| [B2 Browser Upload](https://github.com/backblaze-b2-samples/b2-browser-upload) | Direct browser ingest with presigned S3 uploads, server-held credentials, and CORS | — |
| [B2 AI and data notebooks](https://github.com/backblaze-b2-samples/notebooks) | PyTorch, Ray Train/Tune, and Whisper notebooks reading B2-backed data | — |
<!-- catalog:samples:end -->

See the [full sample cross-reference](docs/related-b2-samples.md) for domain-specific robotics, autonomous-vehicle, LiDAR, medical-imaging and reinforcement-learning samples, and for selection guidance.

## B2 capability map

| Area | Capabilities | Selection notes |
|---|---|---|
| Access | S3 API, presigned URLs, CORS, multipart, scoped keys (one bucket + one prefix + capabilities) | Default to S3 API; native API only for notifications, lock, replication setup |
| Change and lifecycle | Event notifications, versions, lifecycle (hide, then delete) | Events trigger validation and refresh; webhook must ack fast, be idempotent |
| Protection | SSE-B2, SSE-C, Object Lock, replication | Lock released versions; replication is bucket-to-bucket DR |
| Delivery | Included egress, CDN, compute partners | Presigned URLs first; CDN for hot public delivery |
| Performance | Standard B2, [Overdrive](https://www.backblaze.com/cloud-storage/b2-overdrive), local cache | Standard by default; Overdrive for sustained high-throughput training/refresh reads; local cache for repeated reads of immutable versions |

<!-- catalog:related:start -->
Other B2 reference architecture categories: [Generative Video](https://github.com/backblaze-b2-samples/b2-gen-video-reference-architectures), [Image Generation](https://github.com/backblaze-b2-samples/b2-image-generation-reference-architectures), [Robotics](https://github.com/backblaze-b2-samples/b2-robotics-reference-architectures), [Autonomous Vehicles](https://github.com/backblaze-b2-samples/b2-autonomous-vehicle-reference-architectures), [Commercial Drones](https://github.com/backblaze-b2-samples/b2-commercial-drone-reference-architectures).
<!-- catalog:related:end -->

[Backblaze B2 documentation](https://www.backblaze.com/docs/cloud-storage) is canonical for product behavior; this repository provides workflow-specific designs.

## Repository layout

`catalog/` architecture, integration and sample metadata, `schemas/` validated contracts, `architectures/` docs and diagrams, `docs/` agent-readable pages, `examples/` B2 configs, `manifests/` sample manifests, `skill/` portable agent skill, `applications/` and `infrastructure/` the CVAT reference implementation, `testdata/` dataset cards and synthetic data, `tools/` generators and checks, `tests/` tool tests, `.github/` CI and templates.

## Validate locally

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-catalog.txt pytest
python3 tools/generate_catalog.py --check
python3 tools/validate_contracts.py
python3 tools/check_markdown_links.py
python3 -m pytest tests
```

The CVAT sample application has its own tests: see [applications/cvat-b2-dataset-pipeline](applications/cvat-b2-dataset-pipeline/README.md).

## Contributing, security and license

See [CONTRIBUTING](.github/CONTRIBUTING.md); the catalog is the extension point. Report sensitive issues through the [security policy](.github/SECURITY.md). Released under the [MIT license](LICENSE); cite with [CITATION.cff](CITATION.cff).
