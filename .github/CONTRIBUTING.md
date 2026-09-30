# Contributing

The architecture catalog is the extension point. Edit `catalog/architectures.yaml`, then run `python3 tools/generate_catalog.py`; do not hand-edit generated README tables or indexes.

- New architecture: copy an existing `architectures/*/architecture.md`; name it by workflow when several tools fit. Add its audience, problem, workflow, scale, validation evidence, security, compliance and links to the catalog. Reuse `examples/`, `testdata/`, `manifests/` and `schemas/`.
- New integration: add it under the relevant catalog architecture with its connection method, evidence date and authoritative documentation. Add an architecture only if the tool materially changes the data flow or security boundary.
- New application: `applications/<name>/` with README (including "B2's role"), `.env.example`, tests; add a row to the sample applications table.
- Regenerate `README.md`, `docs/architecture-index.md`, `skill/references/architecture-catalog.md` and `llms.txt` in the same change.

Evidence rules: attribute to a partner only what its docs or code show; label B2-side patterns as such; never hardcode a region or endpoint; link B2 pricing instead of quoting numbers; mark unverified claims.
Security: no real keys anywhere; secrets in gitignored `0600` `.env`; scoped keys, not master, unless provisioning requires it (say so).
Tests: `python3 tools/generate_catalog.py --check`, `python3 tools/validate_contracts.py`, `python3 tools/check_markdown_links.py`, and `python -m pytest` in each application. Use moto for S3 data operations and environment-gated acceptance tests for Object Lock, key scoping and lifecycle.
