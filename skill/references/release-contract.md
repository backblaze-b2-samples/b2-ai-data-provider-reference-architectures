# Dataset release contract

Use four complementary artifacts:

1. `manifest.json`: deterministic release identity, version, annotation format, modalities, SPDX license identifier, compact provenance, validation status, statistics, content fingerprint, and per-file size, media type, and SHA-256.
2. Dataset card: intended uses, exclusions, source or generation method, collection rights and consent, sensitive-data posture, quality evidence, limitations, bias, contact, and commercial terms.
3. Croissant JSON-LD: standardized dataset files, record sets, fields, transformations, license, lineage, and responsible-AI metadata for discovery and loading.
4. Delivery manifest: release identity, issue and expiry times, access method, and short-lived presigned GET URLs.

Use `data/` for payloads of any modality; `images/` and `annotations/` remain valid. Keep paths relative to the release root and reject traversal, empty segments, and backslashes.

Serialize publication for each dataset/version through one publisher; multi-host producers submit jobs to that publishing service. Apply and verify requested retention on skipped object versions as well as new uploads, preserving longer or stronger existing protection.

Write data objects first and the release manifest last. Presence of `manifest.json` is the commit marker. Reject changed content at an existing version; publish a new version instead. Compute the fingerprint from UTF-8 `path:file-sha256` lines in `files` array order, with a newline after each entry. Exclude clocks and request-specific values so identical content is reproducible.

Treat the delivery manifest as a secret. Write it with restrictive permissions, do not log or store it beside the dataset, and use the shortest practical expiry.

Use the dataset card and Croissant RAI fields—not ad hoc object metadata—for detailed rights, consent, PII, bias, lineage, and allowed-use statements. Object metadata should remain small, especially on Object-Lock-enabled buckets.
