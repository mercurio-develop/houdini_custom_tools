---
name: lops-asset-builder
description: >-
  Builds component-based USD/MaterialX assets in Houdini LOPs via Asset Builder v3.
  Use for LOPs asset builder, component output, material variants, lookdev, batch build,
  AssetBuilderConfig, Solaris USD publish, or geo/mtl variant workflows.
---

# LOPs Asset Builder v3

## Entry points

| Mode | Code |
|------|------|
| Interactive UI | `tools.lops_asset_builder_v3.lops_asset_builder_v3.create_component_builder()` |
| Batch UI | `tools.lops_asset_builder_v3.batch_asset_builder.show_batch_asset_builder()` |
| Headless CLI | `tools.lops_asset_builder_v3.lops_asset_builder_cli.build_asset(config_dict)` |
| JSON file | `build_asset_from_file("/path/to/config.json")` |
| MCP | `run_lops_asset_builder` with config path or inline dict |

Shelf: **Lops Asset Builder**, **Batch Asset Builder**.

## Config

Use `AssetBuilderConfig` dataclass (`asset_builder_config.py`):

```python
from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from tools.lops_asset_builder_v3.asset_builder_engine import run_asset_build

cfg = AssetBuilderConfig(
    main_asset_file_path="/path/to/asset.abc",
    folder_textures="/path/to/textures",
    asset_name="MyAsset",
    create_lookdev=True,
    create_light_rig=True,
)
result = run_asset_build(cfg)
```

Example JSON: `tools/lops_asset_builder_v3/examples/simple_config.json`, `full_config.json`.

Validate config fields:

```bash
python .cursor/skills/lops-asset-builder/scripts/validate_config.py examples/simple_config.json
```

## Pipeline layers — do not bypass

```
AssetBuilderConfig
  → asset_builder_engine.run_asset_build()
      → geo_mtl_builder.build_geo_and_mtl_variants()   # geo import + variants
      → material_builder.create_materials()            # TexToMtlX_V2
      → asset_builder_graph.build_lookdev_setup()      # turntable, Karma, light rig
```

## Geo import chain (inside componentgeometry)

`prepare_imported_asset()` in `geo_mtl_builder.py`:

```
file/alembic → matchsize → attribwrangle (material→name) → attribdelete → remove_points
  → default output
  → polyreduce (proxy) → simproxy branch
```

PSX hooks insert after `remove_points` — see `psx-retro-tools` skill.

## Safe extension points

| Change | Where |
|--------|-------|
| New builder option | `AssetBuilderConfig` + `from_dialog`/`from_dict` + engine step |
| Geo preprocessing | After `remove_points` in `geo_mtl_builder.py` or post-build patch |
| Material validation | `material_validator.validate_and_warn_user` |
| Lookdev/Karma | `asset_builder_graph.py`, `subnet_lookdev_setup.py` |
| Network layout | `network_layout.create_organized_net_note` |

## Testing checklist

- [ ] MCP `validate_asset_folder` or material_validator passes
- [ ] Build from `examples/simple_config.json`
- [ ] `reload_custom_tools` after Python edits
- [ ] Cook component output; confirm `/ASSET` prims exist
- [ ] Material variants assigned; lookdev camera at `/turntable/lookdev/ldevCam0`

## Key files

| File | Role |
|------|------|
| `lops_asset_builder_v3.py` | Interactive dialog entry |
| `asset_builder_engine.py` | Orchestration |
| `geo_mtl_builder.py` | Geo import + variant graph |
| `material_builder.py` | Texture → MaterialX |
| `asset_builder_graph.py` | Lookdev, Karma, light rig |
| `material_validator.py` | Pre-build validation |
| `lops_asset_builder_cli.py` | Headless/batch CLI |

More examples: [examples.md](examples.md).
