# Houdini Custom Tools (`$CUSTOM_TOOLS`)

> Live-symlinked at `~/houdini22.0/custom_tools` via `~/houdini22.0/packages/custom_tools.json`.
> Exposed to AI agents through the unified **Houdini MCP 2.0** server (`~/dev/workstation/mcp/houdini-mcp2/`) via [`mcp_manifest.json`](mcp_manifest.json).

## Routing

| Need | Read / Use |
| :--- | :--- |
| Architecture & conventions | `scripts/python/ARCHITECTURE.md`, `scripts/python/CONVENTIONS.md`, `scripts/python/SHELF_SCOPE.md` |
| LOPs USD Asset Builder v3 | `scripts/python/tools/lops_asset_builder_v3/` (`asset_builder_engine.py`, `geo_mtl_builder.py`, `material_builder.py`) |
| PSX Retro Lookdev & Dither | `scripts/python/tools/psx_tools/` (`dither.py`, `sop_effects.py`, `karma_presets.py`, `psx_asset_builder.py`) |
| Shared Houdini 22 helpers | `scripts/python/modules/houdini_node_utils.py`, `usd_discovery.py`, `texture_path_repair.py`, `asset_folder_scanner.py` |
| Unified MCP 2.0 catalog manifest | `mcp_manifest.json` (auto-discovered & SHA-256 drift-tracked by `houdini-mcp2`) |
| Headless Houdini 22 Crucible tests | `tests/crucible_hython.py` |

## Commands

```bash
# Pure-Python unit tests
PYTHONPATH=scripts/python python3 -m unittest discover -s scripts/python/tools/lops_asset_builder_v3/tests -v

# High-severity lint gate
ruff check scripts/python --select F821,F811,B008

# Live Houdini 22 headless Crucible verification
cd /opt/hfs22.0.429 && source houdini_setup_bash >/dev/null 2>&1 && hython /home/tushita/dev/houdini_custom_tools/tests/crucible_hython.py
```

## Verified Houdini 22 Rules (Never Repeat)

1. **Karma Resolution (`karmarenderproperties` / `karmarendersettings`):** Use `modules.houdini_node_utils.set_karma_resolution(node, w, h)` — sets `res_mode="manual"`, unlocks `resolutiony`, AND calls `deleteAllKeyframes()` to strip the default `autoheight` `pythonexprf` expression.
2. **`divide` SOP Triangulation:** Set `convex=1`, `usemaxsides=1`, `numsides=3` (there is no `triangulate` parameter).
3. **VEX Functions:** Use `rint()` (not `round()`) and single-arg `chf(cam_path + "/focal")`.
4. **Headless Safety:** Guard `hou.ui.*` with `if hou.isUIAvailable():`; never eagerly import PySide6 UI modules in `__init__.py` or evaluate `hou.Vector2(...)` in function default arguments.
5. **Locked HDA Traversal:** Use `modules.houdini_node_utils.iter_author_nodes(root)` instead of raw `allSubChildren()` to skip locked SideFX library HDAs.
