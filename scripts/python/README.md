# Custom Houdini Pipeline Tools

Python tools for Houdini 21.x: USD asset building in LOPS, library authoring, project management, and stage utilities. Structured for clarity when describing pipeline engineering work (PySide UIs, headless CLI, USD/asset workflows).

**Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md).  
**Conventions:** See [CONVENTIONS.md](CONVENTIONS.md) (naming, module layout, HMCP handlers).
**Shelf audit & refactor plan:** See [SHELF_AUDIT.md](SHELF_AUDIT.md).

## Setup

Add the python root to your path (or use the Houdini package for `$CUSTOM_TOOLS`):

```python
import sys, os
root = os.environ.get("CUSTOM_TOOLS", "")
if root:
    sys.path.insert(0, os.path.join(root, "scripts", "python"))
```

Environment variables used across tools: `$CUSTOM_TOOLS`, `$JOB`, `$HIP`, `$HB`.

---

## 1. LOPS Asset Builder (v3)

Component-based USD/MaterialX assembly in LOPS, with batch UI and JSON-driven CLI.

**Batch UI (PySide6):**

```python
from tools.lops_asset_builder_v3.batch_asset_builder import show_batch_asset_builder
show_batch_asset_builder()
```

**Headless / pipeline CLI:**

```python
from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset, build_asset_from_file

result = build_asset({
    "main_asset_file_path": "/path/to/asset.abc",
    "folder_textures": "/path/to/textures",
    "asset_name": "MyAsset",
})
# Or: build_asset_from_file("/path/to/config.json")
```

Example configs: `tools/lops_asset_builder_v3/examples/`.

**Batch folder scanner** (KB3D `Models/` and ABC/FBX LOD layouts): see [`tools/lops_asset_builder_v3/BATCH_SCANNER_README.md`](tools/lops_asset_builder_v3/BATCH_SCANNER_README.md).

---

## 2. USD Library Toolkit (`kb3d_tools`)

Build and maintain KB3D-style USD libraries from parts, BGEO, or existing assemblies.

**Parts folder → assembly (canonical API):**

```python
from tools.asset_library_builder.asset_builder import build_from_parts

build_from_parts(
    parts_folder="/path/to/parts/MyAsset",
    asset_name="MyAsset",
    models_folder="/path/to/Models",
    materials_folder="/path/to/Materials",
)
```

**Assembly UI (primary shelf entry):**

```python
from tools.kb3d_tools.kb3d_proper_assembly_builder_ui import show_ui
show_ui()
```

**BGEO → USD:**

```python
from tools.kb3d_tools.bgeo import analyze_bgeo_folder, convert_bgeo_to_usd
```

**Transforms before separation (FBX/BGEO):**

```python
from tools.kb3d_tools.core.transform_extractor import extract_and_save
```

Full workflows: `tools/kb3d_tools/README.md`.

---

## 3. Studio pipeline utilities

**Project manager (PySide6):**

```python
from pipeline.project_manager import ProjectManager
# Typically launched from shelf; loads projects_config.json under $CUSTOM_TOOLS/config
```

See `pipeline/` for project creation, save tool, and USD project helpers.

---

## 4. Production Hub (Iconik · ftrack · Houdini)

VFX pipeline integration: sandbox **ftrack** + **Iconik** clients, Houdini PySide6 UI, MCP server, and optional FastAPI/Next.js dashboard. See [projects/production_hub/VFX_PIPELINE.md](projects/production_hub/VFX_PIPELINE.md) and [PORTFOLIO.md](PORTFOLIO.md).

**Config:** copy `$CUSTOM_TOOLS/config/integrations.example.json` → `integrations.json` (see README for env vars).

**Houdini UI:**

```python
from tools.production_hub import show_ui
show_ui()
```

**Smoke test (integrations only, no Houdini):**

```bash
cd scripts/python && PYTHONPATH=. python -c "from integrations.settings import load_settings; print(load_settings())"
```

**Smoke test (inside Houdini):** Connection tab → test both APIs → load tasks → build from `tools/lops_asset_builder_v3/examples/simple_config.json` → publish USD path.

---

## 5. Stage and material helpers

| Tool | Import |
|------|--------|
| Organize LOP network | `from tools.lop_network_organizer import organize_current_stage` |
| Merge selected LOPs | `from tools.merge_selected_lops import merge_selected_nodes` |
| Select same node type | `from tools.select_same_type_simple import select_same_type` |
| Texture → MaterialX (Houdini) | `from tools.material_tools import MtlxMaterial, TxToMtlx` |
| Texture → MaterialX (standalone USD) | `tools/material_tools/TexToMtlx_USD/tex_to_mtlx_standalone.py` |

**Materials:** Use **TexToMtlX_V2** inside Houdini LOPs/shops; use **TexToMtlx_USD** for offline USD material libraries without running the asset builder.

---

## Directory map

```
python/
├── ARCHITECTURE.md
├── CONVENTIONS.md
├── SHELF_SCOPE.md
├── pipeline/
├── tools/
│   ├── lops_asset_builder_v3/    # Flagship asset builder
│   ├── psx_tools/                # PSX retro preprocessing
│   ├── material_tools/
│   ├── batch_import_workflow/
│   └── lop_network_organizer.py, merge_selected_lops.py, …
├── modules/
├── HMCP/                         # Cursor MCP bridge + handlers
└── custom_utils.py
```

Agent docs at repo root: `AGENTS.md`, `docs/HMCP_TOOLS.md`.

---

## For reviewers

| Theme | Where to look |
|-------|----------------|
| Asset management & batch pipelines | `lops_asset_builder_cli.py`, `batch_asset_builder.py` |
| PySide / artist tools | `batch_asset_builder.py`, `project_manager.py` |
| Agent / MCP integration | `HMCP/`, `docs/HMCP_TOOLS.md`, `AGENTS.md` |
| Extensible design | `AssetBuilderConfig`, JSON examples |
| Artist support | `material_validator.py`, `lop_network_organizer`, progress reporters |

**Stack:** Python 3.11, PySide6, USD (`pxr`) where noted, Houdini `hou`.

**Smoke test (inside Houdini):** Run `show_batch_asset_builder()`, build one asset from `examples/simple_config.json`, then `organize_current_stage()` on the result.

---

## Cursor AI setup

Agent entry: [`AGENTS.md`](../../AGENTS.md) at repo root.

| Resource | Path |
|----------|------|
| Agent mandates | `$CUSTOM_TOOLS/AGENTS.md` |
| Tool reference | `$CUSTOM_TOOLS/docs/HMCP_TOOLS.md` |
| Skills | `$CUSTOM_TOOLS/.cursor/skills/` |
| Rules | `$CUSTOM_TOOLS/.cursor/rules/` |
| HMCP setup | `scripts/python/HMCP/CURSOR_SETUP.md` |
| Edit-test playbook | `scripts/python/HMCP/PIPELINE_DEV.md` |
| MCP config template | `$CUSTOM_TOOLS/.cursor/mcp.json.example` |

Skills: `hmcp-cursor-workflow`, `hmcp-edit-test-loop`, `lops-asset-builder`, `psx-retro-tools`, `houdini-pipeline-overview`.

Open the Python workspace in Cursor: `cursor $CUSTOM_TOOLS/scripts/python`

---

## Development

```python
from custom_utils import reload_packages
reload_packages({"altclick": True})
```

Install via Houdini package: `$HOUDINI_USER_PREF_DIR/packages/custom_tools.json`.

**Version:** Houdini 21.x · **Python:** 3.11
