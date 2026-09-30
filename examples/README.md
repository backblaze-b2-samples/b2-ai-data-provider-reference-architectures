# B2 configuration examples

Templates for the buckets in [cvat-annotation-pipeline](../architectures/cvat-annotation-pipeline/architecture.md).
Placeholders are in `<angle brackets>`. Apply with the B2 CLI (`b2` v4.4.1 flags checked with `--help`; JSON shapes
checked against the [B2 API docs](https://www.backblaze.com/apidocs) on 2026-09-29). These are templates: review placeholders, capabilities, retention periods and deletion behavior before applying them to an account.

| File | Applies to | Purpose |
|---|---|---|
| `cors.json` | releases bucket | Browser presigned GET/PUT from a customer portal origin |
| `lifecycle-raw.json`, `lifecycle-work.json` | raw, work buckets | Purge non-current versions 30 days after hide/delete |
| `object-lock.json` | releases bucket | Default governance retention on released versions |
| `sse.json` | all buckets | SSE-B2 default encryption |
| `event-notifications.json` | work bucket | Webhook on new exports (validation trigger) |
| `replication.json` | releases bucket | Bucket-to-bucket copy to a DR bucket (not customer delivery) |

Retention periods are placeholders. Set them from your contracts; lifecycle deletes data.

```bash
# Buckets (names are globally unique; Object Lock is enabled at creation or later)
b2 bucket create --file-lock-enabled "$ORG-cvat-releases" allPrivate
b2 bucket create "$ORG-cvat-work" allPrivate
b2 bucket create "$ORG-cvat-raw" allPrivate

# Default encryption, lifecycle, CORS, Object Lock
b2 bucket update --default-server-side-encryption SSE-B2 "$ORG-cvat-work"
b2 bucket update --lifecycle-rules "$(cat lifecycle-work.json)" "$ORG-cvat-work"
b2 bucket update --lifecycle-rules "$(cat lifecycle-raw.json)" "$ORG-cvat-raw"
b2 bucket update --cors-rules "$(cat cors.json)" "$ORG-cvat-releases"
b2 bucket update --default-retention-mode governance --default-retention-period "90 days" "$ORG-cvat-releases"

# Replication (needs the destination bucket, and matching Object Lock settings on it)
b2 bucket update --replication "$(cat replication.json)" "$ORG-cvat-releases"

# Event notifications use the native API b2_set_bucket_notification_rules (key needs writeBucketNotifications);
# the body is event-notifications.json.
```

## Scoped application keys (one bucket + one prefix per key)

```bash
b2 key create --bucket "$ORG-cvat-raw"      --name-prefix raw/     ingest-writer      listFiles,writeFiles
b2 key create --bucket "$ORG-cvat-raw"      --name-prefix raw/     cvat-source-reader listFiles,readFiles
b2 key create --bucket "$ORG-cvat-work"     --name-prefix exports/ cvat-export-writer listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-cvat-work"     --name-prefix exports/ validator-reader   listFiles,readFiles
b2 key create --bucket "$ORG-cvat-releases" --name-prefix releases/ publisher         listFiles,readFiles,writeFiles,writeFileRetentions
b2 key create --bucket "$ORG-cvat-releases" --name-prefix "releases/$DATASET/" --duration 86400 delivery-signer listFiles,readFiles
```

`b2 key create` prints the secret once; store it in a gitignored `0600` file, never in shell history or logs.
Bucket, lifecycle, retention and replication changes need an admin key (or the master key), so run them once from
provisioning and keep that key out of runtime services.

## Replication caveats

The destination bucket must have Object Lock enabled if the source does, or replication fails
([B2 docs](https://www.backblaze.com/docs/cloud-storage-cloud-replication)). Replicated data cannot be replicated again, and
deletes and hide markers are not replicated. Create the DR bucket with `--file-lock-enabled` and the same retention posture.
