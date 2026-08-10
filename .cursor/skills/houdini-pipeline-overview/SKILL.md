---
name: houdini-pipeline-overview
description: >-
  Maps the custom_tools Houdini pipeline layout, PYTHONPATH, imports, reload
  workflow, and product boundaries. Use when working on custom_tools, $CUSTOM_TOOLS,
  pipeline architecture, where to add a new tool, Solaris/LOPs scripts, or PYTHONPATH setup.
---

# Houdini Pipeline Overview

## Environment

| Variable | Role |
|----------|------|
| `$CUSTOM_TOOLS` | Repo root (`houdini22.0/custom_tools`) |
| `$CUSTOM_TOOLS/scripts/python` | Python package root — must be on `PYTHONPATH` |
| `$JOB`, `$HIP`, `$HB` | Used across tools for paths |

Houdini package: `$HOUDINI_USER_PREF_DIR/packages/custom_tools.json` loads the shelf and PYTHONPATH.

## Repo layout

```
custom_tools/
├── toolbar/custom_tools.shelf    # Shelf buttons (thin wrappers only)
├── scripts/python/
│   ├── tools/                    # Product code
│   ├── modules/                  # Shared helpers
│   ├── pipeline/                 # Project manager, save tool
│   ├── integrations/             # ftrack, Iconik (no hou)
│   └── HMCP/                     # Cursor MCP bridge + in-Houdini server
└── config/                       # integrations.json, projects_config.json
```

Full tree: [reference.md](reference.md). Architecture detail: `scripts/python/ARCHITECTURE.md`.

## Five products — do not duplicate

| Product | Module | Entry |
|---------|--------|-------|
| LOPs Asset Builder v3 | `tools/lops_asset_builder_v3/` | Shelf: `lops_asset_builder`, `batch_asset_builder` |
| PSX Retro Tools | `tools/psx_tools/` | Shelf: `psx_tools` |
| USD Library / KB3D | `tools/kb3d_tools/`, `tools/asset_library_builder/` | `build_from_parts()`, assembly UI |
| Studio pipeline | `tools/pipeline/` | Project Manager shelf |
| Production Hub | `tools/production_hub/`, `integrations/` | ftrack/Iconik + USD publish |

**Rule:** New features belong in the owning product. Do not create parallel builders.

## Import conventions

```python
from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset
from modules.misc_utils import _sanitize, MaterialNamingConfig
from custom_utils import reload_packages
```

Legacy builders live in `tools/_archive/lops_builders/` — use v3 only.

## Reload after edits

**In Houdini:** Alt+click **Reload Packages** shelf, or:

```python
from custom_utils import reload_packages
reload_packages({"altclick": True})
```

**From Cursor (HMCP):** MCP tool `reload_custom_tools`.

## Shared modules

| Module | Purpose |
|--------|---------|
| `modules/misc_utils.py` | `_sanitize`, material naming, bounds |
| `modules/houdini_node_utils.py` | `set_parm`, cook helpers |
| `modules/asset_folder_scanner.py` | Scan geo/tex folder layouts |

## Cursor integration

- **Skills:** `$CUSTOM_TOOLS/.cursor/skills/` (this repo)
- **Rules:** `$CUSTOM_TOOLS/.cursor/rules/houdini-python-tools.mdc`
- **HMCP:** `.cursor/mcp.json.example` + in-Houdini server — see `hmcp-cursor-workflow` skill

## Where to add new work

| Need | Location |
|------|----------|
| New LOPs/asset feature | `tools/lops_asset_builder_v3/` |
| Retro/PSX look | `tools/psx_tools/` |
| New shelf button | `tools/<name>/` + `toolbar/custom_tools.shelf` |
| Production tracking | `integrations/` + thin UI in `tools/production_hub/` |
| One-off stage utility | `tools/<script>.py` at tools root |
