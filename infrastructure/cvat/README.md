# CVAT + B2 deployment

Backblaze guide: [Connect B2 to CVAT](https://www.backblaze.com/docs/en/cloud-storage-connect-backblaze-b2-cloud-storage-to-cvat).

No compose fork is kept here: run upstream CVAT and attach B2 through its API, so the repo does not drift from CVAT releases.

1. Deploy CVAT from a released tag using its own `docker-compose.yml` ([CVAT install docs](https://docs.cvat.ai/docs/administration/basics/installation/)). Pin and acceptance-test the version used by your environment.
2. Create a CVAT Personal Access Token ([docs](https://docs.cvat.ai/docs/api_sdk/access_tokens/)).
3. Create scoped B2 keys ([examples](../../examples/README.md)) and copy `.env.example` to `.env` (`chmod 600`).
4. Attach the storage. Source storage, prefix limited to one batch:

```bash
set -a; . ./.env; set +a
python attach_cloud_storage.py --name b2-raw-batch1 --prefix raw/batch1/
python attach_cloud_storage.py --name b2-exports --prefix exports/   # run with the export-writer key
```

Use a different `.env` (different key) per storage: source uses the read-only key, target the export-writer key.
Then choose these storages as source/target in the CVAT task and export dialogs.

Test: `python -m pytest` in this folder.
