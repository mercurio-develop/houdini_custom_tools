# Production Hub — Iconik · ftrack · Houdini

VFX pipeline showcase: **ftrack** (tracking/versions), **Iconik** (MAM metadata), **Houdini** (USD + PySide6 UI). Same Python layer powers **MCP** and **FastAPI + Next.js**.

**Pipeline guide:** [VFX_PIPELINE.md](VFX_PIPELINE.md) · **Backlight/ftrack study:** [BACKLIGHT_FTRACK_ARCHITECTURE.md](BACKLIGHT_FTRACK_ARCHITECTURE.md) · **Connect plugin:** [FTRACK_CONNECT.md](FTRACK_CONNECT.md) · **Demo:** [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md) · **Portfolio:** [../../PORTFOLIO.md](../../PORTFOLIO.md)

LOPS Asset Builder v3 and local KB3D USD libraries are typical publish sources; a [sample USD](samples/sample_assembly.usda) is included for sandbox tests.

## Stack

| Layer | Location |
|-------|----------|
| Integration clients (no `hou`) | [`integrations/`](../../integrations/) |
| Houdini PySide6 UI | [`tools/production_hub/`](../../tools/production_hub/) |
| MCP server | [`mcp/production_hub_server.py`](../../mcp/production_hub_server.py) |
| HTTP API | [`integrations/http_api.py`](../../integrations/http_api.py) |
| Web dashboard | [`dashboard/`](dashboard/) |

## Configuration

1. Copy [`$CUSTOM_TOOLS/config/integrations.example.json`](../../../../config/integrations.example.json) to **`$CUSTOM_TOOLS/config/integrations.json`** (gitignored).
2. Or set environment variables (override JSON):

| Variable | Purpose |
|----------|---------|
| `FTRACK_SERVER_URL` | ftrack server URL |
| `FTRACK_API_USER` | API user email |
| `FTRACK_API_KEY` | API key |
| `ICONIK_BASE_URL` | e.g. `https://app.iconik.io` |
| `ICONIK_APP_ID` | Iconik application ID |
| `ICONIK_AUTH_TOKEN` | Iconik auth token |
| `ICONIK_STORAGE_ID` | Optional FILES storage UUID (auto-resolved if empty) |
| `PRODUCTION_HUB_CONFIG` | Optional path to JSON file |

Install Python deps (venv recommended; Houdini may use `pip install --target`):

```bash
pip install -r requirements-integrations.txt
```

Add `scripts/python` to `PYTHONPATH` (or use your existing `$CUSTOM_TOOLS` package).

## Iconik TOPs bulk ingest

Recursive USD scan + upload via PDG — see [`tools/iconik_tops/README.md`](../../tools/iconik_tops/README.md).

PDG workers need the same `integrations.json` / env vars and `PYTHONPATH` as the interactive session.

## Houdini — open Production Hub

```python
from tools.production_hub import show_ui
show_ui()
```

### 5-minute demo script

1. **Connection** — Test ftrack and Iconik; confirm sandbox URLs in the log.
2. **Task** — Load projects → pick project → Load tasks → select a task (writes `$JOB/ftrack_task_id.json` when `$JOB` is set).
3. **Build** — Point at [`lops_asset_builder_v3/examples/simple_config.json`](../../tools/lops_asset_builder_v3/examples/simple_config.json) (adjust paths) → **Run LOPS Asset Builder**.
4. **Publish** — Set USD output path → **Publish USD deliverable** → **Copy last IDs** for your notes/screenshot.

## MCP (Cursor)

Add to Cursor MCP settings (adjust paths):

```json
{
  "mcpServers": {
    "production-hub": {
      "command": "python",
      "args": ["/path/to/custom_tools/scripts/python/mcp/production_hub_server.py"],
      "env": {
        "PYTHONPATH": "/path/to/custom_tools/scripts/python",
        "FTRACK_SERVER_URL": "https://YOUR.ftrackapp.com",
        "FTRACK_API_USER": "...",
        "FTRACK_API_KEY": "...",
        "ICONIK_APP_ID": "...",
        "ICONIK_AUTH_TOKEN": "..."
      }
    }
  }
}
```

Tools: `ftrack_list_projects`, `ftrack_list_tasks`, `ftrack_get_task_context`, `iconik_search_assets`, `publish_usd_deliverable_tool`.

## Web dashboard (Phase 2)

Terminal 1 — API:

```bash
cd "$CUSTOM_TOOLS/scripts/python"
export PYTHONPATH=.
uvicorn integrations.http_api:app --port 8765
```

Terminal 2 — Next.js:

```bash
cd projects/production_hub/dashboard
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The app proxies `/api/*` to the FastAPI service via `next.config.js`.

## Recruiter pitch

*Artists pick an ftrack task in Houdini, build USD via the existing LOPS CLI, publish a version to ftrack, and link metadata in Iconik—the same Python modules run in MCP and a small Next.js dashboard.*

Production would add ACLs, event plugins, transcoding, and farm dispatch; this repo demonstrates integration design and DCC-facing UX on sandbox credentials.

See also [ARCHITECTURE.md](../../ARCHITECTURE.md) (Product 5), [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md), and [FTRACK_CONNECT.md](FTRACK_CONNECT.md) (legacy Connect plugin vs Hub).
