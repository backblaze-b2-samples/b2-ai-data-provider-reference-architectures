# B2 configuration examples

Configuration templates for the buckets in these [reference architectures](../docs/architecture-index.md). Run command blocks from this repository's `examples/` directory using Bash and the B2 CLI v4. Authenticate the CLI with a provisioning credential before creating buckets or application keys. Configuration fields are documented in the [B2 API reference](https://www.backblaze.com/apidocs).

Set `ORG` to a globally unique bucket-name prefix. Set the additional variables used by the selected command block, and replace values shown in `<angle brackets>` before running it. Choose retention periods, lifecycle settings, and application-key capabilities for the workload; lifecycle rules permanently delete expired object versions.

| Variable | Purpose |
|---|---|
| `ORG` | Globally unique bucket-name prefix. |
| `DATASET` | Dataset identifier used to scope dataset prefixes. |

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

Connection roles include `listBuckets` for `HeadBucket`; file access remains restricted by the bucket and prefix. `listAllBucketNames` is needed only when a tool enumerates all buckets.

```bash
b2 key create --bucket "$ORG-cvat-raw"      --name-prefix raw/     ingest-writer      listBuckets,listFiles,writeFiles,readFiles
b2 key create --bucket "$ORG-cvat-raw"      --name-prefix raw/     cvat-source-reader listBuckets,listFiles,readFiles
b2 key create --bucket "$ORG-cvat-work"     --name-prefix exports/ cvat-export-writer listBuckets,listFiles,readFiles,writeFiles
b2 key create --bucket "$ORG-cvat-work"     --name-prefix exports/ validator-reader   listFiles,readFiles
b2 key create --bucket "$ORG-cvat-releases" --name-prefix releases/ publisher         listBuckets,listFiles,readFiles,writeFiles,writeFileRetentions,readFileRetentions
b2 key create --bucket "$ORG-cvat-releases" --name-prefix "releases/$DATASET/" --duration 86400 delivery-signer listFiles,readFiles
```

`b2 key create` prints the secret once; store it in a gitignored `0600` file, never in shell history or logs.
Bucket, lifecycle, retention and replication changes need an admin key (or the master key), so run them once from
provisioning and keep that key out of runtime services.

## Replication caveats

The destination bucket must have Object Lock enabled if the source does, or replication fails
([B2 docs](https://www.backblaze.com/docs/cloud-storage-cloud-replication)). Replicated data cannot be replicated again, and
deletes and hide markers are not replicated. Create the DR bucket with `--file-lock-enabled` and the same retention posture.
