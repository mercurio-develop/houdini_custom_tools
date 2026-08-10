---
name: hmcp-cursor-workflow
description: >-
  Guides Cursor agent interaction with live Houdini via HMCP MCP server. Use when
  testing in Houdini, HMCP, Houdini MCP, scene info, execute_code, reload modules,
  run_lops_asset_builder, or validate_asset_folder.
---

# HMCP + Cursor Workflow

## Architecture

```
Cursor IDE  →  houdini_mcp_bridge.py (stdio)  →  HMCP/server.py (TCP :9876)  →  hou.*
```

Config template: `$CUSTOM_TOOLS/.cursor/mcp.json.example` (copy to `.cursor/mcp.json`). Setup: `scripts/python/HMCP/CURSOR_SETUP.md`.

## Prerequisites

1. HMCP server running in Houdini (shelf **HMCP** toggle)
2. Cursor MCP shows `houdini` connected (green)
3. Workspace: open `$CUSTOM_TOOLS/scripts/python` in Cursor

Start server in Houdini:

```python
from HMCP import start_server, is_server_running
print(is_server_running())
start_server()
```

## Decision tree

| Task | Approach |
|------|----------|
| Edit Python tool code | Edit repo files → `reload_custom_tools` |
| Run asset build | MCP `run_lops_asset_builder` |
| PSX retro build | MCP `run_psx_asset_build` |
| Validate materials | MCP `validate_asset_folder` |
| Scan folder layout | MCP `scan_asset_folder` |
| Inspect stage | MCP `get_stage_summary` (prefer over full scene dump) |
| Node errors / cook chain | MCP `get_node_errors`, `get_cook_chain` |
| USD prim inspection | MCP `inspect_usd_prim`, `list_usd_prims` |
| Wire / layout nodes | MCP `connect_nodes`, `layout_nodes` |
| Batch asset builds | MCP `run_batch_lops_build` |
| Viewport screenshot | MCP `capture_viewport` |
| Server health | MCP `get_server_health` |
| Karma render QA | MCP `render_karma_preview` |
| Material bindings | MCP `list_material_assignments` |
| Publish paths | MCP `get_build_output_paths` |
| Scan → build config | MCP `scan_to_lops_config` |
| Asset library search | MCP `search_assets`, `import_asset` |
| SOP geo stats (PSX) | MCP `get_geo_stats` |
| USD stage metadata | MCP `get_usd_stage_info` |
| USD attributes | MCP `inspect_usd_attribute` |
| USD bounds | MCP `get_usd_bounding_box` |
| USD composition | MCP `get_usd_layer_stack` |
| USD variants | MCP `list_variant_sets`, `set_variant_selection` |
| USD reference LOP | MCP `create_usd_reference_lop` |
| Validate exported USD | MCP `validate_usd_file` |
| Cook LOP output | MCP `cook_node` |
| Organize LOP network | MCP `organize_lop_network` |
| Inspect single node | MCP `get_node_info` |
| Ad-hoc Houdini Python | MCP `execute_code` (optional `return_expr`) |
| ftrack / Iconik publish | MCP `production-hub` server (separate from HMCP) |
| Syntax-check (no hou) | Terminal: `python3 -m py_compile module.py` |
| TCP connectivity | `HMCP/smoke_test_tcp.py` via hython |

## MCP tools → pipeline modules

| MCP tool | Wraps |
|----------|-------|
| `run_lops_asset_builder` | `lops_asset_builder_cli.build_asset` / `build_asset_from_file` |
| `run_psx_asset_build` | `psx_asset_builder.run_psx_asset_build` |
| `validate_asset_folder` | `material_validator` + folder scanner |
| `scan_asset_folder` | `modules/asset_folder_scanner` |
| `get_stage_summary` | Lightweight `/stage` children + component outputs |
| `cook_node` | Node cook + USD prim count |
| `organize_lop_network` | `lop_network_organizer.organize_current_stage` |
| `reload_custom_tools` | `custom_utils.reload_packages` |
| `get_scene_info` | HIP summary; use filters to list nodes |
| `execute_code` | Arbitrary `hou.*` with undo group |
| `create_node` / `modify_node` / `delete_node` | Node CRUD |
| `get_node_errors` | `HMCP/handlers/scene_inspection` |
| `get_cook_chain` | Upstream/downstream chain |
| `get_parameter_schema` | Node parm metadata |
| `inspect_usd_prim` / `list_usd_prims` | LOP USD stage inspection |
| `export_usd_from_lop` | Stage export |
| `connect_nodes` / `layout_nodes` / `set_node_flags` | Graph helpers |
| `run_batch_lops_build` | `lops_asset_builder_cli.build_assets_batch` |
| `build_library_from_parts` | `asset_library_builder.build_from_parts` |
| `capture_viewport` | Scene Viewer PNG |
| `get_server_health` | Session snapshot |
| `get_asset_builder_example` | Example JSON from repo |
| `get_geo_stats` | SOP geometry statistics |
| `list_material_assignments` | USD material bindings |
| `get_build_output_paths` | componentoutput publish paths |
| `scan_to_lops_config` | Folder scan → builder config |
| `discover_usd_assets` / `search_assets` | USD library discovery |
| `import_asset` | Reference import to /stage |
| `render_karma_preview` / `apply_psx_karma` | Karma render QA |
| `get_usd_stage_info` | USD stage metadata |
| `inspect_usd_attribute` | Prim attribute reads |
| `get_usd_bounding_box` | World bounds |
| `get_usd_layer_stack` | Layer stack / refs / payloads |
| `list_variant_sets` / `set_variant_selection` | Variant workflows |
| `create_usd_reference_lop` | Solaris reference LOP |
| `set_default_prim` | defaultPrim metadata |
| `validate_usd_file` | On-disk USD validation |
| `setup_karma_usd_publish_chain` | Karma → USD ROP → sublayer/ref publish |
| `version_up_usd_output` | `_v###` version bump on USD outputs |
| `extract_usd_cameras` | USD cameras → camera LOPs |
| `extract_usdz_archive` | USDZ unpack |
| `analyze_usd_materials` | Material/texture manifest |
| `import_usd_materials` | USD → Material Library rebuild |

## MCP resources and prompts

Bridge exposes read-only docs (`hmcp://docs/pipeline-dev`, etc.) and workflow prompts (`asset-build-workflow`, `psx-retro-workflow`, `debug-node-workflow`, `publish-prep-workflow`, `usd-solaris-workflow`) without Houdini.

## Dual MCP setup

[`$CUSTOM_TOOLS/.cursor/mcp.json.example`](.cursor/mcp.json.example) includes:

- **`houdini`** — HMCP bridge (live Houdini session)
- **`production-hub`** — ftrack/Iconik publish (no hou)

Full playbook: [`scripts/python/HMCP/PIPELINE_DEV.md`](scripts/python/HMCP/PIPELINE_DEV.md)

## Example prompts

```
Get Houdini scene info
```

```
Run LOPS asset builder with config /path/to/simple_config.json
```

```
Validate materials for asset folder /path/to/asset with textures in /path/to/textures
```

```
Reload custom tools modules after my Python edits
```

```
execute_code: print(hou.applicationVersionString())
```

## Smoke tests

**Terminal (HMCP dir, server must be running):**

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
uv run python -c "from houdini_mcp_bridge import HoudiniMCPBridge; b=HoudiniMCPBridge(); b.connect(); print(b.send_command('get_scene_info',{}))"
```

**hython:**

```bash
export PYTHONPATH="$CUSTOM_TOOLS/scripts/python:$PYTHONPATH"
/opt/hfs22.0.368/bin/hython $CUSTOM_TOOLS/scripts/python/HMCP/smoke_test_tcp.py
```

## Anti-patterns

- Do **not** duplicate builder logic in MCP handlers — call existing module APIs from `server.py`
- Do **not** run HMCP alongside another Houdini MCP on port 9876
- Do **not** skip `reload_custom_tools` after editing Python in a live session

## Adding a new MCP tool

1. Handler in `scripts/python/HMCP/handlers/`
2. Register in `handler_registry.py`
3. Schema in `mcp_tool_catalog.py`
4. Document here and in `HMCP/README.md`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP red | Start HMCP in Houdini first |
| Port 9876 stuck | `from HMCP import stop_server; stop_server()` or shelf FORCESTART |
| Code changes ignored | `reload_custom_tools` |
