---
name: psx-retro-tools
description: >-
  PSX/PS1-style retro asset preprocessing for Houdini — dither, low-poly, vertex wobble,
  screen snap, Karma presets. Use for PSX, PS1, retro, vertex wobble, dither, low-poly,
  or integrating PSX look with LOPs Asset Builder.
---

# PSX Retro Tools

PSX is a **preprocessing layer** on top of LOPs Asset Builder v3 — not a replacement.

## Pipeline

```
texture_process.py  →  run_asset_build (LOPs Builder)  →  patch_geo_import_with_psx  →  karma_presets.py
```

## Module map

Location: `scripts/python/tools/psx_tools/`

| File | Role |
|------|------|
| `dither.py` | Bayer + error diffusion (NumPy + Pillow) |
| `texture_process.py` | Batch dither/downscale texture folders |
| `sop_effects.py` | Decimate, triangulate, wobble VEX, screen snap |
| `psx_sop_pipeline.py` | Wire SOP chain; patch componentgeometry imports |
| `psx_asset_builder.py` | `run_psx_asset_build()` full pipeline |
| `psx_tools_ui.py` | Shelf dialog |
| `psx_config.py` | `PSXAssetConfig`, `PSXBuildConfig` |
| `karma_presets.py` | Low-res Karma render defaults |

Shelf: **PSX Retro Tools** (`custom_tools.shelf`).

## Usage

### Full PSX asset build

```python
from tools.psx_tools.psx_asset_builder import run_psx_asset_build
from tools.psx_tools.psx_config import PSXBuildConfig, PSXAssetConfig

run_psx_asset_build(PSXBuildConfig(
    main_asset_file_path="/path/to/asset.fbx",
    folder_textures="/path/to/textures",
    asset_name="MyAsset",
    psx=PSXAssetConfig(
        decimate_ratio=0.5,
        triangulate=True,
        apply_vertex_wobble=True,
        process_textures=True,
        palette_size=16,
        dither_method="BAYER",
    ),
))
```

### SOP-only (selected node)

```python
from tools.psx_tools.psx_asset_builder import apply_psx_to_selected_geo
from tools.psx_tools.psx_config import PSXAssetConfig
apply_psx_to_selected_geo(PSXAssetConfig(decimate_ratio=0.4))
```

### Texture-only

```python
from tools.psx_tools.texture_process import process_texture_folder
process_texture_folder("/path/to/textures", palette_size=16, max_size=128)
```

Writes `{name}_psx.png` beside originals.

## SOP chain order

Inserted after `remove_points` in Asset Builder geo imports:

1. `polyreduce` (decimate ratio)
2. `divide` (triangulate)
3. `attribwrangle` (vertex wobble)
4. `attribwrangle` (screen snap — needs camera path)

Rewires `default`, `reduce_to_5`, and `convex_hull_setup` inputs.

## Asset Builder integration

Current hook: post-build `patch_geo_import_with_psx(comp_geo, cfg)` walks upstream `componentgeometry` nodes.

Future: optional `PSXAssetConfig` field on `AssetBuilderConfig`.

## Dependencies

- **Pillow** — texture dither/quantize (`pip install Pillow` in Houdini Python if missing)
- **NumPy** — dither math

Test dither without Houdini:

```bash
python .cursor/skills/psx-retro-tools/scripts/smoke_dither.py
```

## Not yet ported

- UV texture distort (MaterialX in LOPs — Blender shader group equivalent)
- Blender-style material bake (use COP pre-bake or offline texture pass instead)

## Blender feature mapping

| Blender PSX Tool | Houdini equivalent |
|------------------|-------------------|
| Low-Poly Helper | `polyreduce::2.0` + `divide` triangulate |
| Texture Dither | `dither.py` + `texture_process.py` |
| Vertex Wobble | VEX in `sop_effects.py` |
| Vertex Screen Snap | VEX + camera path parm |
| Render Presets | `karma_presets.py` |
| UV Texture Distort | Not yet — MaterialX UV quantize |
