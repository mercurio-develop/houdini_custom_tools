# Custom Tools — shelf scope

Active tools on the **Custom Tools** shelf tab (`toolbar/custom_tools.shelf`).

## Shelf tools (28)

| Tool | Code |
|------|------|
| Reload Packages | `custom_utils.reload_packages` |
| Create Project | `pipeline/create_project.py` |
| Clean Logs | `custom_utils.clean_log` |
| Project Manager | `pipeline/project_manager.py`, `save_tool.py` |
| Scene Cache Manager | `tools/scene_cache_manager.py` |
| Batch Asset Builder | `tools/lops_asset_builder_v3/batch_asset_builder.py` |
| Lops Asset Builder | `tools/lops_asset_builder_v3/` |
| PSX Retro Tools | `tools/psx_tools/` |
| LOPS Light Rig | `tools/lops_light_rig.py` |
| Place Light Highlight | `viewer_states/_place_light.py` |
| Split Geo | `tools/split_geo.py` |
| Group Importer | `tools/batch_import_workflow/` |
| TOP Template | `tools/hip_templates.py` → `TEMPLATE_TOPS.hiplc` |
| Merge HIP Template | `tools/hip_templates.py` (menu of all templates) |
| File Path Manager | `tools/file_path_manager.py` |
| Shader Nodes Script | inline HScript (VOP) |
| Customize Variant Name | inline HScript (LOP) |
| Component Material Custom | inline HScript / `component_material_custom.py` |
| Asset Builder Template | `templates/Asset_Builder_Template.hiplc` |
| Merge Nodes From HIP | `tools/merge_nodes_from_hipfile.py` |
| Tx To Mtlx V2 | `tools/material_tools/TexToMtlX_V2/` |
| Show Node Inputs | `tools/reveal_node_inputs_and_names.py` |
| Node Batch Setter | `tools/node_batch_setter.py` |
| Texture From Disk | `tools/texture_from_disk.py` |
| Get Node Code | `tools/get_node_code.py` |
| HMCP | `HMCP/` |
| Convert To MTLX & USD | `tools/material_tools/TexToMtlx_USD/` |
| Select Same Type | `tools/select_same_type_simple.py` |

## Shared dependencies

- `modules/` — parms, USD helpers, `asset_folder_scanner`, `usd_discovery`
- `ui/` — Qt theme for pipeline dialogs
- `tools/lops_lookdev_camera.py` — LOPs builder lookdev subnet
- `tools/lop_network_organizer.py` — HMCP `organize_lop_network`

## Removed from repo

KB3D tools, production hub, Iconik ingest, `_archive`, orphan importers, integrations package.

See [`HMCP/HMCP_SCOPE.md`](HMCP/HMCP_SCOPE.md) for MCP tool tiers and stability notes.
