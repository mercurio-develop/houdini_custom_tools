# Iconik USD Ingest TOPs

Recursive USD discovery and **full file upload** to Iconik via Houdini TOPs/PDG.

## Prerequisites

1. Copy [`config/integrations.example.json`](../../../config/integrations.example.json) to `config/integrations.json`
2. Set `iconik.app_id`, `iconik.auth_token`, and optionally `iconik.storage_id`
   - If `storage_id` is empty, the uploader resolves `GET files/v1/storages/matching/FILES/`
3. `pip install -r requirements-integrations.txt` (needs `httpx`)
4. `$CUSTOM_TOOLS` package loaded; PDG workers need `PYTHONPATH` including `scripts/python`

## Shelf

**Custom Tools → Iconik USD Ingest TOPs**

Creates a `topnet` named `iconik_usd_ingest`:

```text
scan_usd (Python Processor) → upload_iconik (Python Script) → manifest_csv (CSV Output)
```

### Topnet parms

| Parm | Description |
|------|-------------|
| Root Folder | Library root to scan |
| Scan Mode | `primary` (KB3D geo.usd), `all`, or `glob` |
| Recursive | Walk subfolders |
| Include/Exclude Globs | Semicolon-separated patterns (`glob` mode / filters) |
| Max Items | Safety cap (`0` = unlimited) |
| Dry Run | Log only — no Iconik API writes |
| On Exists | `skip`, `update`, or `new_version` |
| ftrack Task ID | Optional metadata link |

**Dry run is ON by default.** Disable it on the topnet before a live upload cook.

## CLI (validate before TOPs)

```bash
cd "$CUSTOM_TOOLS/scripts/python"
export PYTHONPATH=.

# Discover
python -m tools.iconik_tops.iconik_ingest_cli scan \
  --root /path/to/library --mode primary --recursive

# Dry-run ingest
python -m tools.iconik_tops.iconik_ingest_cli ingest \
  --root /path/to/library --mode primary --recursive --dry-run

# Live upload (limit 3 files)
python -m tools.iconik_tops.iconik_ingest_cli ingest \
  --root /path/to/library --limit 3 --manifest /tmp/iconik_manifest.csv
```

## Architecture

Shared headless modules (no `hou`):

| Module | Role |
|--------|------|
| [`integrations/usd_discovery.py`](../../integrations/usd_discovery.py) | Recursive USD scan |
| [`integrations/iconik/upload.py`](../../integrations/iconik/upload.py) | Iconik upload sequence |
| [`integrations/workflows/ingest_usd_to_iconik.py`](../../integrations/workflows/ingest_usd_to_iconik.py) | Per-file orchestrator |

## Farm notes

- PDG workers must read the same `integrations.json` or env vars as the interactive session
- No Qt during upload cooks (Python Script TOP only uses `httpx`)
- Throttle concurrent uploads if Iconik returns HTTP 429 (reduce PDG batch size)

## Portfolio demo

See [`projects/production_hub/DEMO_CHECKLIST.md`](../../projects/production_hub/DEMO_CHECKLIST.md) — **TOPs ingest** section.
