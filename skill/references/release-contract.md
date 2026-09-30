# Dataset release contract

Use four complementary artifacts:

1. `manifest.json`: deterministic release identity, version, annotation format, modalities, SPDX license identifier, compact provenance, validation status, statistics, content fingerprint, and per-file size, media type, and SHA-256.
2. Dataset card: intended uses, exclusions, source or generation method, collection rights and consent, sensitive-data posture, quality evidence, limitations, bias, contact, and commercial terms.
3. Croissant JSON-LD: standardized dataset files, record sets, fields, transformations, license, lineage, and responsible-AI metadata for discovery and loading.
4. Delivery manifest: release identity, issue and expiry times, access method, and short-lived presigned GET URLs.

Write data objects first and the release manifest last. Presence of `manifest.json` is the commit marker. Reject changed content at an existing version; publish a new version instead. Exclude clocks and request-specific values from the release fingerprint so identical content is reproducible.

Treat the delivery manifest as a secret. Write it with restrictive permissions, do not log or store it beside the dataset, and use the shortest practical expiry. Revoking a signing key prevents future signatures but does not revoke an already issued URL before expiry.

Use the dataset card and Croissant RAI fields—not ad hoc object metadata—for detailed rights, consent, PII, bias, lineage, and allowed-use statements. Object metadata should remain small, especially on Object-Lock-enabled buckets.
