# Decisions and tradeoffs

## ADR-1: Attach B2 to CVAT as Amazon S3 with a custom endpoint
Status: accepted. CVAT documents this path and its S3 client is boto3 with `endpoint_url`. Tradeoff: B2-specific features (Object Lock, notifications, replication) are configured outside CVAT.

## ADR-2: Three buckets (raw, work, releases) instead of one with prefixes
Status: accepted. Lock, lifecycle, replication, encryption and event rules are bucket-level; a key has one prefix. Tradeoff: more buckets and keys to provision. The sample collapses to one bucket for simplicity, so it cannot demonstrate bucket-level lock defaults, only per-object retention.

## ADR-3: Release manifest written last as the commit marker
Status: accepted. B2 has no multi-object transactions; a partial upload has no `manifest.json` and is ignored. Tradeoff: consumers must check for the manifest; Object Lock makes a half-written locked version undeletable until retention ends, so validate before upload.

## ADR-4: Object Lock in governance mode by default
Status: accepted. Protects against accidental deletes and compromised runtime keys (they lack `bypassGovernance`) while letting an admin correct a bad release. Compliance is irreversible for the retention period, including cost; use only under a contractual requirement. Enabling Object Lock on a bucket is one-way.

## ADR-5: Pre-signed URLs for delivery; CDN optional; replication is not delivery
Status: accepted. Presigning needs no customer accounts and inherits the signer key's narrow scope. Included egress covers direct download; add a CDN for hot or public distribution. Cloud Replication copies to another bucket you own and is used for DR, not customers. Tradeoff: URLs are bearer credentials with no per-user revocation before expiry (revoke by deleting the signer key).

## ADR-6: B2 event notifications trigger validation, not CVAT webhooks alone
Status: accepted. B2 events fire on object creation regardless of who wrote it; CVAT webhooks report job/task state. Use both: CVAT webhook = "annotation done", B2 event = "export landed". Tradeoff: at-least-once delivery and a short webhook timeout mean the receiver must ack fast and be idempotent (queue the work; releases are already idempotent).

## ADR-7: Keep CVAT state off B2
Status: accepted. Postgres, Redis, Kvrocks and ClickHouse stay on block storage; back up CVAT (per CVAT's backup guide) into B2 as objects if needed.

## ADR-8: Standard B2 first; Overdrive and local cache are triggered by measurement
Status: accepted. Annotation is human-paced. Revisit when sustained training or bulk refresh reads become the bottleneck.
