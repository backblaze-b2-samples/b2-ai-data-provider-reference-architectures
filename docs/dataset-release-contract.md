# Dataset release contract

The release contract separates operational integrity from discovery and responsible-use documentation. A release is complete only when all data objects are present and `manifest.json` has been written last.

## Release bundle

| Artifact | Audience | Purpose |
|---|---|---|
| `manifest.json` | Publishers, validators, download clients | Stable release identity, per-file SHA-256, content fingerprint, format, provenance class, validation status and byte counts |
| `README.md` dataset card | Buyers, annotators, governance teams | Intended use, limitations, collection or generation method, license, sensitive-data posture and quality notes |
| `croissant.json` | Dataset catalogs and ML tooling | Standard JSON-LD description of files, record sets, fields, license and loading structure |
| On-demand delivery manifest | Authorized customer | Expiring presigned URLs, issue time, expiry time and release identity |

The operational manifest is governed by [release-manifest.schema.json](../schemas/release-manifest.schema.json). Delivery bundles are governed by [delivery-manifest.schema.json](../schemas/delivery-manifest.schema.json). The synthetic example includes a [dataset card](../testdata/synthetic-toy/README.md) and [Croissant metadata](../testdata/synthetic-toy/croissant.json); the sample publisher includes both sidecars in the released files when they are present.

## Payload layout

Use `data/` for audio, video, text, tabular, or mixed-modality payloads. Existing `images/` and `annotations/` layouts remain valid. Paths are relative to the release root and cannot contain parent-directory segments, empty segments, backslashes, or control characters. See the [multimodal release manifest](../manifests/release-manifest.multimodal.example.json) and its [text and tabular fixture](../testdata/multimodal-toy/README.md). The CVAT sample publisher handles image/COCO releases; other modalities use their own content validators with the shared manifest schema.

## Determinism and versioning

- Dataset name and version form the stable release ID: `<dataset>@<version>`.
- The content fingerprint is SHA-256 over UTF-8 `path:file-sha256` lines in the manifest's `files` array order, with a newline after each entry. The sample publisher orders image paths lexicographically, then annotation paths lexicographically, then `README.md` and `croissant.json` when present. Metadata timestamps are excluded.
- A publisher may rerun an identical release. Different content at the same version is a collision and must use a new version.
- Serialize publication per dataset/version through one publisher. The sample CLI uses a persistent OS-lock directory shared by its processes on one host; multi-host producers use the same publishing service or queue. An existence check followed by an upload does not reserve a release name.
- When retention is requested, apply and verify it on every release object version, including objects skipped on reruns, before reporting success. Preserve longer retention and stronger compliance protection.
- Schema versions use semantic versioning. Consumers must reject unsupported major versions and tolerate additive fields only when the schema permits them.

## Provenance and rights

The operational manifest records a compact provenance class and SPDX license identifier. Detailed rights, consent, source lineage, sensitive-data classes, bias, and intended-use restrictions belong in the dataset card and Croissant RAI fields. Commercial providers should replace the sample `MIT` license with their applicable SPDX identifier or `LicenseRef-*` value and link the governing terms from the dataset card.

## Quality evidence

The sample validator checks the release manifest schema, annotation structure, unique image/category/annotation IDs, referenced media, category IDs, finite bounding boxes, annotation coverage and file checksums. A successful publish changes the manifest quality status from `pending` to `passed` before upload. Provider-specific releases should add measurable checks such as label agreement, class distribution, duplicate rate, corruption rate, PII review and split leakage.

## Delivery security

Delivery manifests contain bearer credentials. Generate them on demand, write them with mode `0600`, avoid logging them, use the shortest practical TTL and do not store them in the release bucket.
