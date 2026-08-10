# HMCP handlers

TCP command handlers invoked from `HMCP/server.py` via `handler_registry.py`.

## Layout

Handlers are grouped by domain in subpackages. Each subpackage exports a `COMMANDS` dict merged in `handler_registry.py`.

```
handlers/
  scene/       inspection.py, geo.py
  usd/         inspection.py, solaris.py, materials.py, bindings.py
  publish/     solaris.py, variants.py, prep.py, textures.py
  pipeline/    build.py
  assets/      library.py
  graph/       nodes.py
  render/      karma.py, viewport.py
  system/      health.py
```

| Subpackage | Module | Commands |
|------------|--------|----------|
| `scene/` | `inspection.py` | `get_node_errors`, `get_cook_chain`, `get_parameter_schema` |
| `scene/` | `geo.py` | `get_geo_stats` |
| `usd/` | `inspection.py` | `inspect_usd_prim`, `list_usd_prims`, `export_usd_from_lop` |
| `usd/` | `solaris.py` | Stage info, attributes, bounds, layers, variants, validate |
| `usd/` | `bindings.py` | `list_material_assignments` |
| `usd/` | `materials.py` | USDZ, analyze/import materials |
| `publish/` | `solaris.py` | Karma publish chain, version-up, cameras |
| `publish/` | `variants.py` | Component variant list/export/manifest |
| `publish/` | `textures.py` | Repair paths, compare manifests |
| `publish/` | `prep.py` | Output paths, scan→config |
| `pipeline/` | `build.py` | Batch builder, library from parts |
| `assets/` | `library.py` | Discover/search/import assets |
| `graph/` | `nodes.py` | Connect, layout, flags |
| `render/` | `karma.py` | Karma preview, PSX karma |
| `render/` | `viewport.py` | Viewport, cook ROP, frame range |
| `system/` | `health.py` | Health, example configs |

## Adding a handler

1. Implement `def my_tool(params: dict) -> dict` in the appropriate subpackage module.
2. Register in that subpackage's `__init__.py` `COMMANDS` dict (picked up by `handler_registry.py`).
3. Add schema to `mcp_tool_catalog.py`.
4. Document in `HMCP/README.md` and smoke test if safe without assets.

Shared logic goes in `modules/`, not copied across handlers. Prefer `modules/` over handler-to-handler imports; when one handler must call another, import from the subpackage (e.g. `HMCP.handlers.usd.materials`).
