# HMCP scope — production-focused MCP server

HMCP exposes **typed tools** for the same workflows as the Custom Tools shelf: LOPs asset building, USD inspection, scene debugging, and batch prep. It is not a generic Houdini clone.

## Design rules

1. **One tool = one pipeline action** — prefer `run_lops_asset_builder` over open-ended graph scripting.
2. **Handlers live in `HMCP/handlers/`** — shared logic in `modules/`, not duplicated in `server.py`.
3. **No studio MAM/tracking in HMCP** — Iconik, ftrack, and publish-to-Iconik were removed; add those in a separate service later if needed.
4. **`execute_code` is an escape hatch** — use typed tools first; reserve for gaps only.
5. **Grow by domain** — new tools must map to a shelf workflow or documented production step.

## Core tools (bridge, always on)

| Tool | Purpose |
|------|---------|
| `get_scene_info` / `get_stage_summary` | Scene graph overview (prefer stage summary on large HIPs) |
| `create_node` / `modify_node` / `delete_node` / `get_node_info` | Minimal graph edits |
| `cook_node` | Cook + LOP prim count |
| `scan_asset_folder` | Geo/tex folder scan → LOPs builder input |
| `validate_asset_folder` | Pre-build material/texture check |
| `run_lops_asset_builder` | Single-asset build from JSON |
| `run_psx_asset_build` | PSX preprocess + LOPs build |
| `organize_lop_network` | Layout / merge LOP outputs |
| `reload_custom_tools` | After Python edits |
| `execute_code` | Last resort |
| `set_material` | Simple /mat assign (legacy; prefer builder) |

## Extended tools (handlers)

### Scene & debug
`get_node_errors`, `get_cook_chain`, `get_parameter_schema`, `get_geo_stats`

### Pipeline
`run_batch_lops_build`, `scan_to_lops_config`, `get_build_output_paths`

### USD / Solaris
`inspect_usd_prim`, `list_usd_prims`, `export_usd_from_lop`, `list_material_assignments`, `get_usd_stage_info`, `inspect_usd_attribute`, `get_usd_bounding_box`, `get_usd_layer_stack`, `list_variant_sets`, `set_variant_selection`, `create_usd_reference_lop`, `set_default_prim`, `validate_usd_file`, `analyze_usd_materials`

### Publish prep (disk paths, variants, textures)
`list_component_variants`, `batch_export_variants`, `get_variant_manifest`, `repair_texture_paths`, `compare_material_manifests`, `extract_usd_cameras`

### Asset library (on-disk USD)
`discover_usd_assets`, `search_assets`, `get_asset_categories`, `import_asset`

### Graph
`connect_nodes`, `layout_nodes`, `set_node_flags`

### Render QA
`capture_viewport`, `cook_render_node`, `render_karma_preview`, `apply_psx_karma`, `set_frame_range`

### System
`get_server_health`, `get_asset_builder_example`

## Removed (unstable or out of scope)

| Removed | Reason |
|---------|--------|
| `handlers/general/*` (28 tools) | Ported generic MCP dump; duplicated core tools; dangerous scene I/O (`load_scene`, `new_scene`) |
| `import_url` | Arbitrary download; no production path |
| `render_single_view` | Placeholder; use `capture_viewport` / `render_karma_preview` |
| `setup_karma_usd_publish_chain`, `version_up_usd_output` | Fragile auto-graph; not shelf-tested |
| `import_usd_materials`, `extract_usdz_archive` | Experimental; high failure rate across studios |
| `build_library_from_parts`, set-dressing tools | KB3D / procedural deps removed |
| Iconik TOP + `integrations/` | Studio-specific; not in demo scope |
| `requests` / `beautifulsoup4` deps | Only used by removed help scraper |

## Shelf tool production readiness

| Tool | Status | Notes |
|------|--------|-------|
| LOPs Asset Builder v3 | **Production** | Core product; CLI + UI + HMCP |
| Batch Asset Builder | **Production** | Uses `modules/usd_discovery` |
| PSX Retro Tools | **Production** | Shelf + `run_psx_asset_build` |
| Create Project / Project Manager | **Production** | PySide + `ui/` theme |
| Scene Cache Manager | **Stable** | Self-contained UI |
| File Path Manager | **Stable** | Scan, edit, batch re-root |
| Tx To Mtlx V2 / Convert USD | **Production** | Used by builder + shelf |
| Group Importer | **Stable** | TOP workflow |
| Split Geo / Merge HIP / Node utils | **Stable** | Small focused scripts |
| HMCP | **Production** | Scoped tool surface above |
| TOP Template / Merge HIP Template | **Production** | Merges `.hiplc` from `templates/` |
| Inline HScript shelf tools | **Stable** | VOP/LOP tab menus; no Python deps |
| Place Light Highlight | **Stable** | Viewer state only |

## Candidate deletes (still in repo, low use)

- `tools/houdini_lop_utils.py` — only HMCP publish helpers; keep until publish tools return
- `tools/tex_to_mtlx.py` — legacy shim; V2 is canonical
- `Documentation/SPACESHIP_*`, `MainMenuCommon.xml` batch_importer — stale references

## Adding a new HMCP tool

1. Implement handler in the correct `handlers/<domain>/` module.
2. Register in that package's `COMMANDS`.
3. Add schema to `mcp_tool_catalog.py`.
4. Document here and in `HMCP/README.md`.
5. Tie to a shelf tool or document the production workflow it supports.
