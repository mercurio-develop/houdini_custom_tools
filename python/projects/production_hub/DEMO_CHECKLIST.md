# Production Hub — demo checklist (Iconik · ftrack · Houdini)

## Before the call

- [ ] `integrations.json` or env vars set for **ftrack** and **Iconik** sandboxes
- [ ] `pip install -r requirements-integrations.txt` in venv used by MCP / API
- [ ] Houdini `$CUSTOM_TOOLS` package loads `scripts/python`
- [ ] USD path ready: LOPS build output, KB3D library `.usd`, or [`samples/sample_assembly.usda`](samples/sample_assembly.usda)

## Live demo in Houdini (≈5 min)

- [ ] Optional: launch from **ftrack Connect** so `FTRACK_TASKID` / `FS` / `FE` are set (see [FTRACK_CONNECT.md](FTRACK_CONNECT.md))
- [ ] `from tools.production_hub import show_ui; show_ui()`
- [ ] **Connection:** ftrack + Iconik tests green
- [ ] **Task:** confirm auto-bind from Connect or `$JOB/ftrack_task_id.json`, or load project → tasks manually
- [ ] **Build:** LOPS CLI **or** set USD path to sample/library file
- [ ] **Publish:** publish → **Copy last IDs**
- [ ] **Publish:** **Search Iconik for task** — confirm metadata hit
- [ ] **ftrack UI:** new asset version on task
- [ ] **Iconik UI:** record with `ftrack_task_id` (and optional `kb3d_asset_code`)

## Without Houdini (≈3 min)

- [ ] `uvicorn integrations.http_api:app --port 8765`
- [ ] Next dashboard: [http://localhost:3000](http://localhost:3000) — pick project, open task detail
- [ ] `POST /publish` with sandbox task id + absolute path to `sample_assembly.usda`
- [ ] MCP: `ftrack_list_tasks` → `publish_usd_deliverable_tool` → `iconik_search_assets`

## Talking points

- ftrack owns **task + version**; Iconik owns **searchable MAM metadata**; Houdini owns **USD creation**
- Same [`publish_usd_deliverable`](../../integrations/workflows/publish_usd_deliverable.py) for UI, API, MCP
- [`integrations/identifiers/`](../../integrations/identifiers/) maps shot/parent + KB3D-style names into Iconik fields

See [VFX_PIPELINE.md](VFX_PIPELINE.md).
