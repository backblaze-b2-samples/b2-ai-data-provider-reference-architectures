# CVAT + B2 deployment

Backblaze guide: [Connect B2 to CVAT](https://www.backblaze.com/docs/en/cloud-storage-connect-backblaze-b2-cloud-storage-to-cvat).

Run upstream CVAT and attach B2 through its cloud-storage API.

1. Deploy CVAT from a pinned release using its own `docker-compose.yml` ([CVAT install docs](https://docs.cvat.ai/docs/administration/basics/installation/)).
2. Create a CVAT Personal Access Token ([docs](https://docs.cvat.ai/docs/api_sdk/access_tokens/)).
3. Create scoped B2 keys ([examples](../../examples/README.md)). Include `listBuckets` for CVAT's bucket check. Copy `.env.example` to `source.env` and `target.env`, set each file's mode to `0600`, and configure the source-reader and export-writer credentials and bucket respectively.
4. From this directory, attach source storage for the batch uploaded by `cvat-b2 ingest`:

```bash
set -a; . ./source.env; set +a
python attach_cloud_storage.py --name b2-raw-batch1 --prefix raw/batch1/ \
  --manifest raw/batch1/manifest.jsonl
```

Manifest arguments are complete bucket-relative keys; `--prefix` filters listings and does not rebase them. Repeat `--manifest` for additional manifests. Image names inside the manifest are relative to its directory, for example `images/img_0001.png`.

5. Attach export storage without a manifest:

```bash
set -a; . ./target.env; set +a
python attach_cloud_storage.py --name b2-exports --prefix exports/
```

Choose these storages as source and target in the CVAT task and export dialogs. The environment files are gitignored; keep a separate scoped key for each storage.

Test: `python -m pytest` in this folder.
