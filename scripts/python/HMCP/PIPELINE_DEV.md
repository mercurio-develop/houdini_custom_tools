# HMCP Pipeline Development Playbook

Guide for humans and Cursor agents developing Houdini custom_tools with HMCP.

## Prerequisites

1. Houdini 22 with `$CUSTOM_TOOLS` package loaded
2. HMCP server running (shelf **HMCP** toggle)
3. Cursor MCP green for `houdini`
4. Workspace: `$CUSTOM_TOOLS/scripts/python`

## Standard edit-test loop

```
1. Edit Python in tools/ or modules/
2. MCP: reload_custom_tools
3. MCP: validate_asset_folder (or scan_asset_folder)
4. MCP: run_lops_asset_builder OR run_psx_asset_build
5. MCP: get_stage_summary → cook_node on output
6. MCP: organize_lop_network (optional)
```

Target: under 60 seconds from save to verified build.

## MCP tools by task

| Task | Tool | Notes |
|------|------|-------|
| Reload after edits | `reload_custom_tools` | Alt+click Reload Packages equivalent |
| Scan folder layout | `scan_asset_folder` | KB3D-style geo/tex detection |
| Validate materials | `validate_asset_folder` | Before every build |
| Build USD asset | `run_lops_asset_builder` | JSON file or inline config |
| PSX retro build | `run_psx_asset_build` | Textures + SOP FX + builder |
| Inspect stage | `get_stage_summary` | Prefer over full `get_scene_info` |
| Cook LOP output | `cook_node` | Returns prim count |
| Tidy network | `organize_lop_network` | Grid layout + merge outputs |
| Ad-hoc Python | `execute_code` | Use `return_expr` for values |

### Extended inspection and graph tools

| Task | Tool | Notes |
|------|------|-------|
| Node cook errors | `get_node_errors` | Optional cook_first |
| Trace dependencies | `get_cook_chain` | upstream / downstream / both |
| Parm discovery | `get_parameter_schema` | For AI-safe param edits |
| USD prim detail | `inspect_usd_prim` | From cooked LOP stage |
| USD prim listing | `list_usd_prims` | Optional type_filter |
| Export stage | `export_usd_from_lop` | Writes USD to disk |
| Wire nodes | `connect_nodes` | output_node → input_node |
| Layout network | `layout_nodes` | parent_path or node_paths |
| Node flags | `set_node_flags` | display/render/template/bypass |
| Batch builds | `run_batch_lops_build` | JSON file or inline array |
| Viewport QA | `capture_viewport` | Returns PNG image |
| Render cook | `cook_render_node` | ROP output path |
| Frame range | `set_frame_range` | Playbar start/end |
| Health check | `get_server_health` | Version, HIP, port |
| Example config | `get_asset_builder_example` | From repo examples/ |
| SOP geo stats | `get_geo_stats` | PSX / decimation QA |
| Material bindings | `list_material_assignments` | Post-build lookdev check |
| Publish paths | `get_build_output_paths` | componentoutput disk layout |
| Scan → config | `scan_to_lops_config` | One-step build prep |
| Library search | `search_assets`, `discover_usd_assets` | Find USD on disk |
| Reference import | `import_asset` | Grid layout in /stage |
| Karma QA | `render_karma_preview`, `apply_psx_karma` | Still render after build |

### USD / Solaris depth

| Task | Tool | Notes |
|------|------|-------|
| Stage metadata | `get_usd_stage_info` | defaultPrim, upAxis, prim counts |
| Attribute read | `inspect_usd_attribute` | Single attr or list all |
| Bounds check | `get_usd_bounding_box` | World-space AABB |
| Composition | `get_usd_layer_stack` | refs, payloads, prim stack |
| Variants | `list_variant_sets`, `set_variant_selection` | geo/mtl variant workflows |
| Reference in LOPs | `create_usd_reference_lop` | Wire USD file into /stage |
| Export metadata | `set_default_prim` | Before publish |
| File validation | `validate_usd_file` | pxr + optional usdchecker |
| Karma preview | `render_karma_preview` | Still render after build |
| USD cameras | `extract_usd_cameras` | Stage cameras → LOP nodes |
| Material manifest | `analyze_usd_materials` | Bindings + texture map |
| Variant export | `batch_export_variants` | geo × mtl USD matrix |

### MCP resources and prompts

Resources (`hmcp://docs/...`) and workflow prompts are served by the bridge without Houdini — useful for agent context before connecting.

## get_scene_info vs get_stage_summary

**Default `get_scene_info`** returns HIP metadata + selection only (no full node dump).

To list nodes:

```json
{ "context_path": "/stage", "max_nodes": 100 }
```

Or:

```json
{ "include_all_nodes": true, "max_nodes": 200 }
```

Use **`get_stage_summary`** for LOPs work — lists `/stage` children and `componentoutput` nodes.

## execute_code tips

```python
# Reload and print version
from custom_utils import reload_packages
reload_packages({"altclick": True})
print(hou.applicationVersionString())
```

With `return_expr`:

```json
{
  "code": "node = hou.node('/stage/comp_out')",
  "return_expr": "node.path() if node else None"
}
```

Runs inside `hou.undos.group("MCP execute_code")`. Namespace includes `hou`, `custom_utils`, `Usd` (if available).

## Full asset build example

```
Scan asset folder at $JOB/assets/props/chair
Validate materials for that folder
Run LOPS asset builder with config $JOB/assets/props/chair/build.json
Get stage summary
Cook node /stage/chair_comp_out
Organize lop network
```

## PSX build example

```json
{
  "main_asset_file_path": "/path/to/asset.fbx",
  "folder_textures": "/path/to/textures",
  "asset_name": "MyProp",
  "psx": {
    "decimate_ratio": 0.5,
    "triangulate": true,
    "process_textures": true,
    "palette_size": 16,
    "apply_vertex_wobble": true
  }
}
```

## Smoke tests

**TCP (inside Houdini via hython):**

```bash
export PYTHONPATH="$CUSTOM_TOOLS/scripts/python:$PYTHONPATH"
hython $CUSTOM_TOOLS/scripts/python/HMCP/smoke_test_tcp.py
```

**Bridge (HMCP server must be running):**

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
uv run python -c "from houdini_mcp_bridge import HoudiniMCPBridge; b=HoudiniMCPBridge(); b.connect(); print(b.send_command('get_stage_summary',{}))"
```

## Adding a new MCP tool

1. Handler in `HMCP/handlers/<area>.py` — call existing module API, never duplicate logic
2. Register in `HMCP/handler_registry.py`
3. Schema in `HMCP/mcp_tool_catalog.py` (bridge auto-exposes)
4. Document here and in `README.md`
5. Add to `smoke_test_tcp.py` if testable without assets

Legacy one-offs can still live in `server.py` `self.commands` directly.

All handlers run on Houdini's main thread via `hou.ui.executeDeferred`.

## Anti-patterns

- Do not use `get_scene_info` without filters on large HIPs
- Do not use `execute_code` for routine builds — use typed tools
- Do not skip `reload_custom_tools` after Python edits
- Do not add studio MAM/tracking tools to HMCP — keep integrations as separate services
