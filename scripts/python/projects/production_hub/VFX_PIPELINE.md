# VFX Pipeline — Iconik · ftrack · Houdini

Production Hub connects three systems the way VFX/post shops typically operate:

| System | Responsibility |
|--------|----------------|
| **Houdini** | DCC: artists pick work, build or reference **USD** (LOPS Asset Builder and/or local KB3D library), publish from PySide6 UI |
| **ftrack** | Production tracking: projects, shots/tasks, **Asset** / **AssetVersion**, file components |
| **Iconik** | MAM: searchable metadata linked to ftrack IDs and USD paths |

Shared Python in [`integrations/`](../../integrations/) powers Houdini, MCP, and FastAPI—no duplicated publish logic in TypeScript.

## Data flow

1. Artist opens **Production Hub** in Houdini (`from tools.production_hub import show_ui; show_ui()`).
2. **Connection** — verify sandbox ftrack + Iconik credentials.
3. **Task** — load ftrack project/tasks; select task, or auto-bind from **`FTRACK_TASKID`** (Connect launch) / **`$JOB/ftrack_task_id.json`**
4. **Build** — optional LOPS CLI build from JSON, or point **USD output** at an existing library file.
5. **Publish** — [`publish_usd_deliverable`](../../integrations/workflows/publish_usd_deliverable.py):
   - Registers USD on the ftrack task (AssetVersion).
   - Upserts Iconik metadata (`ftrack_task_id`, `ftrack_asset_version_id`, `usd_path`, optional `kb3d_asset_code`, `vfx_shot_code` from parent context).

## Sandbox sample USD

Without a full KB3D library on disk, use:

[`samples/sample_assembly.usda`](samples/sample_assembly.usda)

Set that path in **Build → USD output**, then publish.

## Configuration

Copy [`$CUSTOM_TOOLS/config/integrations.example.json`](../../../../config/integrations.example.json) to `integrations.json` or set env vars — see [README.md](README.md).

## Sidecar access (no Houdini)

| Tool | Purpose |
|------|---------|
| **MCP** [`mcp/production_hub_server.py`](../../mcp/production_hub_server.py) | List tasks, publish, Iconik search |
| **FastAPI** [`integrations/http_api.py`](../../integrations/http_api.py) | Same operations over HTTP |
| **Next.js** [`dashboard/`](dashboard/) | Task browser + task detail |

## 5-minute demo script

See [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md).

## Compared to ftrack Connect Houdini

The legacy **[ftrack-connect-houdini](https://ftrack-connect-houdini.readthedocs.io/)** integration (Python 2.7, `ftrack-connector-legacy`) publishes **Scene / Geometry / Camera** by exporting Alembic, `.hip`, etc. from the DCC. It does not cover **USD library deliverables** or **Iconik**.

**Production Hub** is the modern path for your portfolio pipeline:

| | Connect Houdini (reference) | Production Hub |
|--|------------------------------|----------------|
| API | Legacy connector | **`ftrack-python-api`** |
| Python | 2.7 | **3.11** (Houdini 21) |
| Launch context | `FTRACK_TASKID`, `FS`, `FE` | Same env vars + auto-bind on open |
| Publish | Export selection → components | **Register USD path** + Iconik metadata |
| MAM | — | **Iconik** |

Recommended workflow: launch Houdini from **ftrack Connect** (env vars set) → open Production Hub (task auto-bound) → build/publish USD → verify ftrack + Iconik. Legacy Connect menus can stay installed for Alembic/`.hip` reference; details in [FTRACK_CONNECT.md](FTRACK_CONNECT.md).

For **Backlight / ftrack conventions**, entity model, Connect plugins, recipes, and how Production Hub maps to them, see [BACKLIGHT_FTRACK_ARCHITECTURE.md](BACKLIGHT_FTRACK_ARCHITECTURE.md).

## Production extensions (not in sandbox)

ftrack location plugins, farm dispatch, transcoding, ACLs, automated thumbnail upload to Iconik, and full KB3D library deployment on studio storage.
