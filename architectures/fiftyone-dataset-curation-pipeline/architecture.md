# Curate datasets and publish quality evidence with each release

## Workload

An AI data provider stores source media in B2 and uses FiftyOne to explore the collection, calculate embeddings, find duplicates, evaluate model outputs, inspect failure slices, and select a higher-quality dataset. Selected media references, labels, reports, and provenance are exported to B2, validated, and published as an immutable release.

B2 is the durable media and release system of record. FiftyOne's database, indexes, sessions, embeddings, previews, operators, and compute remain on infrastructure designed for those workloads.

## Data flow

```mermaid
flowchart LR
  RAW[(B2 raw bucket<br/>raw/collection/)] -->|cloud-backed media| FO[FiftyOne Enterprise<br/>dataset + App]
  MODEL[Predictions / embeddings] --> FO
  FO --> CURATE[Search / similarity / duplicates<br/>evaluation / selection]
  CURATE -->|labels + selections + reports| WORK[(B2 work bucket<br/>fiftyone/run/)]
  RAW -->|selected immutable inputs| VAL[Release validator]
  WORK --> VAL
  VAL -->|files, then manifest last| REL[(B2 releases bucket<br/>Object Lock)]
  REL -->|presigned GET or compute access| CONSUMER[Customer / training pipeline]
```

The release should capture the selection view or rule, dataset identity, model and embedding versions, evaluation configuration, input object versions or checksums, exclusions, and output checksums. A saved FiftyOne view alone is not a durable customer release contract.

## B2 zones

| Zone | Suggested location | FiftyOne relationship | Policy |
|---|---|---|---|
| Raw | `<org>-fiftyone-raw/raw/<collection>/` | Read-only cloud-backed media | Version and lifecycle superseded inputs according to collection policy |
| Work | `<org>-fiftyone-work/fiftyone/<run>/` | Exported selections, labels, reports, and provenance | Retain for review; expire superseded runs |
| Releases | `<org>-fiftyone-releases/releases/<dataset>/<version>/` | Downstream delivery, not FiftyOne application state | Immutable version; Object Lock governance by default |
| DR, optional | `<org>-fiftyone-releases-dr/` | No FiftyOne access | Cloud Replication target |

Use a manifest or inventory to bind each FiftyOne sample to a stable B2 object key plus a version or checksum. Avoid making a mutable object URL the only identity for a sample.

## Connect FiftyOne to B2

FiftyOne Enterprise reaches S3-compatible storage through its MinIO credential profile, which takes an `endpoint_url`, access key, secret key, optional alias, and region ([cloud credentials](https://docs.voxel51.com/enterprise/installation.html#enterprise-cloud-credentials)). Point that profile at B2:

```ini
[default]
access_key = <B2 application key ID>
secret_access_key = <B2 application key>
endpoint_url = https://s3.<region>.backblazeb2.com
alias = b2
region = <bucket region>
```

Configure it per session with `MINIO_CONFIG_FILE` (and optionally `MINIO_PROFILE`), or register it permanently with `minio_config_file` in the media cache config. Store the file in secrets management or use FiftyOne's managed cloud-credential controls rather than committing it. Scope the B2 application key to the intended bucket and the narrowest source prefix.

Configure the connection with these settings:

- Derive `endpoint_url` and `region` from the bucket region shown in the B2 console; do not hardcode a region.
- Write sample filepaths in one canonical form, either `b2://<bucket>/<key>` through the alias or `https://s3.<region>.backblazeb2.com/<bucket>/<key>`, and use the same form in the App, SDK, delegated operators, and media cache.
- Grant the media-reader key `listFiles,readFiles` on the source prefix only.

Public buckets are not needed. Do not store expiring presigned URLs as durable sample paths because they will fail after expiry and make dataset state time-dependent.

## Curation and publication

1. Create a stable source inventory containing B2 key, object version when available, size, media type, and checksum.
2. Populate a FiftyOne dataset whose filepaths resolve through the B2 cloud-media configuration.
3. Import ground truth, model predictions, and relevant sample metadata.
4. Run embeddings, similarity, uniqueness, duplicate detection, evaluations, and human review on external compute.
5. Save the selection criteria and export selected sample identities, labels, metrics, failure slices, and quality reports to the work zone.
6. Validate that every selected sample resolves to the expected immutable input and that labels and metrics conform to the release schema.
7. Publish files and metadata using the shared [dataset release contract](../../docs/dataset-release-contract.md), with `manifest.json` uploaded last.

The release may copy selected media into its own immutable prefix or reference an immutable, retained source version. Copying simplifies customer delivery and retention reasoning; referencing avoids duplication but requires the source objects to remain available for the release lifetime.

## Credential model

| Role | Scope | Capabilities |
|---|---|---|
| FiftyOne media reader | Raw bucket and collection prefix | `listFiles,readFiles` |
| Curation exporter | Work bucket and run prefix | `listFiles,readFiles,writeFiles` |
| Release validator | Raw selection plus work run | `listFiles,readFiles` |
| Release publisher | Release dataset prefix | `listFiles,readFiles,writeFiles,writeFileRetentions` |
| Delivery signer | Released dataset prefix | `listFiles,readFiles` |

FiftyOne managed credentials can be scoped by provider, bucket, user, or group according to its documentation. Use the smallest audience and bucket set that supports the curation team. Keep the release publisher separate from interactive operators and plugins.

## Performance

Cloud-backed media reduces unnecessary source copies but does not eliminate latency-sensitive reads. Plan for:

- a media or preview cache near the FiftyOne deployment;
- local or compute-adjacent storage for embeddings, indexes, and databases;
- batching and concurrency limits for large scans;
- immutable object identity so cached media cannot silently diverge from the catalog;
- measured image, video, and range-read performance with representative files.

Use Standard B2 by default. Consider compute-local caching for repeated analysis of the same immutable collection; evaluate higher-throughput storage options only after measurement shows object-store throughput is the bottleneck.

## Security and governance

- Use read-only raw credentials and separate output writers.
- Restrict managed cloud credentials to the curation team and required buckets.
- Review plugins and delegated operators before allowing them to access raw or sensitive media.
- Treat thumbnails, embeddings, similarity indexes, predictions, and failure slices as derived personal or confidential data when the source warrants it.
- Record why samples were included or excluded and which model, embedding, and evaluation versions influenced the decision.
- Delete cached and indexed derivatives when contractual deletion applies, while respecting any valid immutable-release retention.

## Keep off B2

Do not place FiftyOne's database, indexes, sessions, compute scratch data, or low-latency cache inside B2 dataset prefixes. Store durable exports and releases in B2; use application-appropriate storage for interactive state.

## Deployment requirements

1. Credential scoping and rotation behave correctly for users, groups, and services.
2. Cached content is invalidated or keyed by immutable object identity.
3. Curation exports are deterministic enough to reproduce a release from its input inventory and configuration.
4. Representative scans, embeddings, and interactive review meet performance objectives.

## References

- [FiftyOne Enterprise cloud-backed media](https://docs.voxel51.com/enterprise/cloud_media.html)
- [FiftyOne Enterprise installation and cloud credentials](https://docs.voxel51.com/enterprise/installation.html)
- [FiftyOne environment guidance](https://docs.voxel51.com/environments/index.html)
- [Backblaze B2 S3-compatible API](https://www.backblaze.com/docs/cloud-storage-s3-compatible-api)
- [Dataset release contract](../../docs/dataset-release-contract.md)
