# Agent guide

Use this repository to design or review storage workflows for AI data providers using Backblaze B2.

<!-- CODEGRAPH_START -->
## CodeGraph

When a `.codegraph/` directory exists at the repository root, use `codegraph explore "<question or symbols>"` before grep, find, or broad file reads when locating or understanding code. If the directory does not exist, skip CodeGraph; indexing is a maintainer decision.
<!-- CODEGRAPH_END -->

## Sources of truth

1. `catalog/architectures.yaml` is the machine-readable catalog of architectures, third-party integrations (with `connection_type`) and external sample applications.
2. `schemas/` defines the release and delivery contracts.
3. `architectures/*/architecture.md` contains the detailed design, B2 zones and security boundaries.
4. `applications/` contains executable demonstrations; `examples/` contains configuration templates.
5. Current Backblaze product behavior is authoritative at <https://www.backblaze.com/docs/cloud-storage>. Pricing is authoritative at <https://www.backblaze.com/cloud-storage/pricing>.

Describe the documented connection for each integration: a B2 backend or provider preset, a custom S3 endpoint, presigned URLs, or an application worker using an SDK. Specify the endpoint, region, addressing style, required operations, and credential scope. Attribute product capabilities to the linked vendor documentation or source code. Describe sample applications by the workflow they implement. Classify the integrations in this catalog as `s3-custom-endpoint` or `presigned-url`, according to the configured access method.

For a single-file read of the summary, every architecture and the release contract, use `llms-full.txt`.

## Generated files

Run `python3 tools/generate_catalog.py` after editing the catalog. Do not hand-edit generated sections in `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt`, or `llms-full.txt`. `llms-full.txt` concatenates narrative pages, so regenerate after editing `docs/ai-data-providers.md`, any `architecture.md`, or `docs/dataset-release-contract.md`.

Validate generated output with:

```bash
python3 tools/generate_catalog.py --check
python3 tools/validate_contracts.py
python3 tools/check_markdown_links.py            # add --external to probe outbound links
python3 -m pytest tests
cd applications/cvat-b2-dataset-pipeline
python3 -m pytest
```

The generator also copies `schemas/release-manifest.schema.json` into the sample package at `applications/cvat-b2-dataset-pipeline/src/cvat_b2_pipeline/schemas/`. Edit the root schema and regenerate; do not edit the packaged copy.

## Operational invariants

- Derive `https://s3.<region>.backblazeb2.com` from the bucket region; do not hardcode a real region.
- Use scoped application keys. Keep master or administrative keys out of runtime services.
- Treat presigned URLs and delivery manifests as bearer credentials.
- Publish immutable dataset versions and write `manifest.json` last as the completion marker. Serialize jobs per dataset/version through one publisher host with a shared persistent lock directory; multi-host producers submit work to that publisher. Verify requested retention on skipped versions as well as new uploads.
- Keep annotation databases, queues, caches, and compute off object storage.
- Never commit credentials, customer data, or real presigned URLs.
