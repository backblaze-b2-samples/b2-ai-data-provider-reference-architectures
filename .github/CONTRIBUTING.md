# Contributing

The architecture catalog is the extension point. Edit `catalog/architectures.yaml`, then run `python3 tools/generate_catalog.py`; do not hand-edit generated README tables or indexes.

- New architecture: copy an existing `architectures/*/architecture.md`; name it by workflow when several tools fit. Add its audience, problem, workflow, scale, security, compliance and links to the catalog. Reuse `examples/`, `testdata/`, `manifests/` and `schemas/`.
- New integration: add it under the relevant catalog architecture with its connection method, `connection_type`, authoritative documentation `url` and, where one exists, a `setup_url` for the B2 setup guide. Connection types and their labels are shared across the B2 category repos (see `CONNECTION_LABELS` in `tools/generate_catalog.py`); a value not yet used here must be added to both the schema enum and `CONNECTION_LABELS`. Add an architecture only if the tool materially changes the data flow or security boundary.
- New sample application: build it in its own repository (for example under `backblaze-b2-samples`) and add a `samples:` entry to the catalog with `group`, `summary`, `description` and, where it fits, `architectures` and `relevance`. The generator renders the README, `docs/related-b2-samples.md`, `llms.txt` and skill tables.
- The release schema in `schemas/release-manifest.schema.json` is copied into the sample package by the generator; include that generated copy when the schema changes.
- Regenerate `README.md`, `docs/related-b2-samples.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md`, `llms.txt` and `llms-full.txt` in the same change.

Content rules: attribute to a vendor only what its docs or code show; label B2-side patterns as such; never hardcode a region or endpoint; link B2 pricing instead of quoting numbers.
Security: no real keys anywhere; secrets in gitignored `0600` `.env`; scoped keys, not master, unless provisioning requires it (say so).
Tests: `python3 tools/generate_catalog.py --check`, `python3 tools/validate_contracts.py`, `python3 tools/check_markdown_links.py`, `python3 -m pytest tests`, and `python -m pytest` in each application. Run `python3 tools/check_markdown_links.py --external` when adding outbound links. Use moto for S3 data operations and environment-gated acceptance tests for Object Lock, key scoping and lifecycle.
