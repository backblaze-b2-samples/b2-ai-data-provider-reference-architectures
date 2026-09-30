# Object layout and data-flow spec

Key builders live in [`layout.py`](../../applications/cvat-b2-dataset-pipeline/src/cvat_b2_pipeline/layout.py).

```
<org>-cvat-raw/
  raw/<batch>/manifest.jsonl              CVAT image manifest (cloud-storage source)
  raw/<batch>/images/<name>.<ext>
<org>-cvat-work/
  exports/<batch>/annotations/instances.json    CVAT export (COCO 1.0 in the sample)
<org>-cvat-releases/
  releases/<dataset>/<version>/images/<name>.<ext>
  releases/<dataset>/<version>/annotations/instances.json
  releases/<dataset>/<version>/manifest.json    written last: presence == release complete
```

Rules:

- No leading `/` and no `//` in keys (CVAT cannot use them). Batch IDs, dataset names and versions use `[a-z0-9._-]`.
- `<version>` is immutable. A rerun with identical content is skipped; different content at an existing version is refused (`Collision`). Publish a new version instead.
- Consumers discover versions by listing `releases/<dataset>/` common prefixes and trust only versions that have `manifest.json`.
- Every object stores `sha256` in user metadata; keep metadata minimal (Object Lock buckets have a small per-version metadata limit).
- Delivery manifests (pre-signed URLs) are generated on demand and are not stored in B2.

## Stages

| Stage | Input | Output | Gate |
|---|---|---|---|
| Ingest | collector data | `raw/<batch>/` + CVAT manifest | Key/prefix policy, checksums |
| Annotate | `raw/<batch>/` via CVAT source storage | CVAT tasks | CVAT review / QA |
| Export | CVAT job/task | `exports/<batch>/` via CVAT target storage | Event notification fires |
| Validate | export + raw | pass/fail report | schema, bbox bounds, category ids, image/annotation coverage, checksums |
| Publish | validated set | `releases/<dataset>/<version>/` | remote size + checksum verify, manifest last, retention set |
| Deliver | release | pre-signed URLs | TTL, read-only prefix-scoped key |
| Refresh | new batch / new version | next version | `manifest.json` created event |

Manifests: [release](../../manifests/release-manifest.example.json), [delivery](../../manifests/delivery-manifest.example.json).
