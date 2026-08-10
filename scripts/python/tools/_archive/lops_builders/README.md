# Archived LOPS asset builders

Superseded by **`tools/lops_asset_builder_v3/`**. Kept for reference only; do not use in new shelves or pipelines.

| Path | Notes |
|------|--------|
| `lops_asset_builder.py` | Original monolithic builder |
| `lops_asset_builder_v2/` | Component builder + TOPs helper |
| `lops_asset_builder_workflow_LEGACY/` | Multi-asset step UI (depended on v2) |

Active lookdev helpers (`create_camera_lookdev`, `create_karma_nodes`) are imported from v3 in production code (e.g. `lops_light_rig_pipeline.py`).
