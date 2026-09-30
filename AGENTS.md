# Agent guide

Use this repository to design or review storage workflows for AI data providers using Backblaze B2.

<!-- CODEGRAPH_START -->
## CodeGraph

When a `.codegraph/` directory exists at the repository root, use `codegraph explore "<question or symbols>"` before grep, find, or broad file reads when locating or understanding code. If the directory does not exist, skip CodeGraph; indexing is a maintainer decision.
<!-- CODEGRAPH_END -->

## Sources of truth

1. `catalog/architectures.yaml` is the machine-readable architecture and integration catalog.
2. `schemas/` defines the release and delivery contracts.
3. `architectures/*/architecture.md` contains the detailed design and evidence scope.
4. `applications/` contains executable demonstrations; `examples/` contains configuration templates.
5. Current Backblaze product behavior is authoritative at <https://www.backblaze.com/docs/cloud-storage>. Pricing is authoritative at <https://www.backblaze.com/cloud-storage/pricing>.

Do not describe documentation review or emulator-backed tests as a production deployment. State the evidence basis when it matters to a recommendation.

## Generated files

Run `python3 tools/generate_catalog.py` after editing the catalog. Do not hand-edit generated sections in `README.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, or `llms.txt`.

Validate generated output with:

```bash
python3 tools/generate_catalog.py --check
python3 tools/validate_contracts.py
python3 tools/check_markdown_links.py
cd applications/cvat-b2-dataset-pipeline
python3 -m pytest
```

## Operational invariants

- Derive `https://s3.<region>.backblazeb2.com` from the bucket region; do not hardcode a real region.
- Use scoped application keys. Keep master or administrative keys out of runtime services.
- Treat presigned URLs and delivery manifests as bearer credentials.
- Publish immutable dataset versions and write `manifest.json` last as the completion marker.
- Keep annotation databases, queues, caches, and compute off object storage.
- Never commit credentials, customer data, or real presigned URLs.
