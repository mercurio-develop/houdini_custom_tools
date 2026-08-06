# Custom Houdini Pipeline Tools

Python tools for Houdini 21.x: USD asset building in LOPS, library authoring, project management, and stage utilities. Structured for clarity when describing pipeline engineering work (PySide UIs, headless CLI, USD/asset workflows).

**Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md).  
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
| Texture → MaterialX (Houdini) | `from tools.tex_to_mtlx import TxToMtlx` |
| Texture → MaterialX (standalone USD) | `tools/material_tools/TexToMtlx_USD/tex_to_mtlx_standalone.py` |

**Materials:** Use **TexToMtlX_V2** inside Houdini LOPs/shops; use **TexToMtlx_USD** for offline USD material libraries without running the asset builder.

---

## Directory map

```
python/
├── ARCHITECTURE.md
├── integrations/
├── mcp/
├── pipeline/
├── projects/production_hub/
├── tools/
│   ├── production_hub/
│   ├── lops_asset_builder_v3/    # Flagship asset builder
│   ├── kb3d_tools/               # USD library + bgeo/ + core/
│   ├── asset_library_builder/    # Canonical build_from_parts
│   ├── material_tools/
│   ├── batch_import_workflow/
│   ├── _archive/                 # Superseded LOPS builders
│   └── lop_network_organizer.py, merge_selected_lops.py, …
├── modules/
└── utils/
```

Legacy LOPS builders (v1, v2, workflow UI) live under `tools/_archive/lops_builders/`.

---

## For reviewers

| Theme | Where to look |
|-------|----------------|
| Asset management & batch pipelines | `lops_asset_builder_cli.py`, `asset_library_builder`, `kb3d_tools/bgeo` |
| PySide / artist tools | `batch_asset_builder.py`, `project_manager.py`, `production_hub`, `kb3d_proper_assembly_builder_ui.py` |
| Tracking / MAM bridge | `integrations/`, `tools/production_hub/` |
| Extensible design | `AssetBuilderConfig`, JSON examples, modular `kb3d_usd_builder` classes |
| Artist support | `material_validator.py`, `lop_network_organizer`, progress reporters in UIs |

**Stack:** Python 3.11, PySide6, USD (`pxr`) where noted, Houdini `hou`; optional `httpx` + `ftrack-python-api` for Production Hub.

**Smoke test (inside Houdini):** Run `show_batch_asset_builder()`, build one asset from `examples/simple_config.json`, then `organize_current_stage()` on the result.

---

## Development

```python
from custom_utils import reload_packages
reload_packages({"altclick": True})
```

Install via Houdini package: `$HOUDINI_USER_PREF_DIR/packages/custom_tools.json`.

**Version:** Houdini 21.x · **Python:** 3.11
