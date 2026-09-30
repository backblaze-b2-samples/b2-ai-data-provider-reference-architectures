# Related Backblaze B2 sample applications

The [`backblaze-b2-samples`](https://github.com/backblaze-b2-samples) organization contains practical applications that complement these reference architectures. The projects below demonstrate specific collection, transformation, curation, release, delivery, and event patterns; they are not evidence that a third-party platform has a native B2 integration.

The organization describes these projects as unofficial and unsupported samples. Review each repository's README, security notes, dependencies, and maintenance status before adapting it.

## Closest workflow matches

| Sample | What it demonstrates | Most relevant here |
|---|---|---|
| [SAM 2 Mask Dataset Builder](https://github.com/backblaze-b2-samples/sam2-mask-dataset-builder) | Raw images and video in B2 become versioned COCO RLE, mask PNG, cut-out, and run-metadata artifacts; reviewers and training jobs use presigned reads. | [CVAT](../architectures/cvat-annotation-pipeline/architecture.md), [Label Studio](../architectures/label-studio-annotation-pipeline/architecture.md), [Supervisely](../architectures/supervisely-annotation-pipeline/architecture.md), and [FiftyOne](../architectures/fiftyone-dataset-curation-pipeline/architecture.md) workflows |
| [MMAction2 Action Dataset Builder](https://github.com/backblaze-b2-samples/mmaction2-action-dataset-builder) | Raw video is segmented, clipped, labeled, split, and packaged into versioned training-data releases on B2. | Video annotation, automated labeling, release layout, and [dataset release contract](dataset-release-contract.md) examples |
| [NeMo Curator Training Data](https://github.com/backblaze-b2-samples/nemo-curator-training-data) | Deduplication, quality filtering, and PII redaction produce separately versioned JSONL stages with a lineage manifest. | [Dataloop](../architectures/dataloop-direct-data-pipeline/architecture.md), multimodal annotation, provenance, and governed text-corpus processing |
| [DataComp Image-Text Filtering](https://github.com/backblaze-b2-samples/datacomp-image-text-filtering) | WebDataset shards stream from B2 through CLIP scoring, baseline filters, and near-duplicate removal; filtered shards and quality metrics return to B2. | [FiftyOne](../architectures/fiftyone-dataset-curation-pipeline/architecture.md), [Dataloop](../architectures/dataloop-direct-data-pipeline/architecture.md), and dataset-quality workflows |
| [Supervision Sports Highlights](https://github.com/backblaze-b2-samples/supervision-sports-highlights) | Roboflow Inference and Supervision detect, track, clip, and annotate video while B2 stores the source, stage manifest, derived media, and presigned playback assets. | [Roboflow](../architectures/roboflow-presigned-import-pipeline/architecture.md) and computer-vision processing patterns; it is not a Roboflow Bucket Mirror example |
| [img2dataset WebDataset Object Storage](https://github.com/backblaze-b2-samples/img2dataset-webdataset-object-storage) | Image-text inputs are bulk-downloaded and written directly to reproducible WebDataset shards in B2, with download-yield validation and no local staging disk. | Collection, normalization, large-batch ingest, and training-format packaging |
| [WebDataset Streaming PyTorch Training](https://github.com/backblaze-b2-samples/webdataset-streaming-pytorch-training) | Media is packed into shards with a JSON manifest, stored in B2, and streamed directly into PyTorch with worker-aware shard allocation. | Release consumption, distributed training delivery, and throughput measurement |
| [DuckDB Query-in-Place](https://github.com/backblaze-b2-samples/duckdb-query-in-place) | DuckDB queries Parquet, CSV, and JSON in B2 with ranged reads and materializes selected results back to B2 as Parquet. | Validation, statistics, slice creation, [Dataloop](../architectures/dataloop-direct-data-pipeline/architecture.md), and [FiftyOne](../architectures/fiftyone-dataset-curation-pipeline/architecture.md) workflows |

## Operational building blocks

| Sample | Reusable pattern |
|---|---|
| [B2 Event Broker](https://github.com/backblaze-b2-samples/b2-event-broker) | Validates signed B2 Event Notifications, acknowledges promptly, and forwards events to multiple subscribers with retry handling. Useful for validation and downstream-refresh fan-out. |
| [B2 Browser Upload](https://github.com/backblaze-b2-samples/b2-browser-upload) | Direct browser upload with an S3 presigned `PutObject` URL or the B2 Native API, including CORS and the boundary that keeps application keys on the server. |
| [B2 AI and data notebooks](https://github.com/backblaze-b2-samples/notebooks) | Small downstream examples for PyTorch image classification, Ray Train/Tune checkpoints, and Whisper transcription using B2-backed data. |

## Domain-specific candidates

These samples are relevant if the catalog expands into industry-specific collection and processing architectures:

- [CARLA Sensor Data Lake](https://github.com/backblaze-b2-samples/carla-sensor-data-lake): synthetic autonomous-driving sensor capture and streaming.
- [ROS 2 rosbag2 Cloud Offload](https://github.com/backblaze-b2-samples/rosbag2-cloud-offload): robotics recording upload, Parquet cataloging, search, and presigned replay.
- [KISS-ICP LiDAR Archive](https://github.com/backblaze-b2-samples/kiss-icp-lidar-archive): LiDAR scan ingest, odometry, maps, poses, and trajectories.
- [TotalSegmentator Batch Pipeline](https://github.com/backblaze-b2-samples/totalsegmentator-batch-pipeline): medical-volume ingest, anatomical segmentation masks, and volumetric statistics.
- [MuJoCo Rollout Dataset](https://github.com/backblaze-b2-samples/mujoco-rollout-dataset): reinforcement-learning video, state, action, reward, and summary datasets.

## Selection guidance

- Use the sample that demonstrates the missing implementation pattern rather than linking every adjacent AI application.
- Keep the release contract, least-privilege key design, retention, and compliance decisions in this repository's architecture documents.
- Treat sample manifests as implementation examples, not automatically conforming release manifests. Validate or transform them before publishing a customer release.
- Do not infer production readiness or third-party connector support from a sample that only uses the B2 S3-compatible API.
