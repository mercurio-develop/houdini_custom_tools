# LOPs Asset Builder — Examples

## Minimal JSON config

```json
{
  "main_asset_file_path": "/path/to/asset.abc",
  "folder_textures": "/path/to/textures",
  "asset_name": "MyAsset",
  "create_lookdev": true,
  "create_light_rig": true,
  "lowercase_material_names": false
}
```

Save as `my_asset.json`, then:

```python
from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset_from_file
result = build_asset_from_file("/path/to/my_asset.json")
print(result.success, result.message)
```

## MCP prompts

```
Validate materials for /path/to/asset.abc with textures in /path/to/textures
```

```
Run LOPS asset builder with config /path/to/my_asset.json
```

```
Scan asset folder /path/to/KB3D_Models/MyAsset
```

## Python dict build

```python
from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset

result = build_asset({
    "main_asset_file_path": "/data/assets/chair/chair.fbx",
    "folder_textures": "/data/assets/chair/textures",
    "asset_name": "chair",
    "asset_variants": [],
    "mtl_variants": [],
    "create_lookdev": False,
    "validate_materials": True,
})
```

## With geo + material variants

```json
{
  "main_asset_file_path": "/path/to/asset_LOD0.abc",
  "folder_textures": "/path/to/textures",
  "asset_name": "PropName",
  "asset_variants": ["/path/to/asset_LOD1.abc"],
  "asset_vset_name": "geo_variant",
  "mtl_variants": ["/path/to/textures_worn"],
  "mtl_vset_name": "mtl_variant",
  "create_lookdev": true
}
```

## Post-edit reload (in Houdini or MCP)

```python
from custom_utils import reload_packages
reload_packages({"altclick": True})
```

Or MCP: `Reload custom tools modules`
