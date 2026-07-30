# Batch LOPS Asset Builder — Folder Scanner

The **Batch Asset Builder** scans geometry folders, detects variants, and writes JSON configs for headless builds via [`lops_asset_builder_cli.py`](lops_asset_builder_cli.py).

Launch from Houdini:

```python
from tools.lops_asset_builder_v3.batch_asset_builder import show_batch_asset_builder
show_batch_asset_builder()
```

Or use the **Batch Asset Builder** shelf tool.

---

## What it does

1. Scan a **Geometry Folder** (optionally recursive)
2. Detect main geometry files, LOD/geo variants, and material texture folders
3. Preview results in the UI table
4. Generate per-asset JSON configs (or run builds directly)

Generated configs match the shape used by [`examples/simple_config.json`](examples/simple_config.json) and are consumed by `build_asset_from_file()`.

---

## Supported input layouts

### ABC / FBX / OBJ / BGEO (LOD suffixes)

Classic pipeline geometry with variant suffixes:

```
MyAsset/
├── MyAsset.abc           # main
├── MyAsset_high.abc      # geo variant
├── MyAsset_low.abc
└── textures/
```

Grouping is by **filename stem** (`MyAsset`). Suffixes like `_high`, `_low`, `_lod0`, `_A`, `_v1` are detected using configurable rules (see below).

### KB3D `Models/` folders (USD)

KB3D-style component folders are treated as **one asset per subfolder**. The scanner picks a single primary USD file using this priority:

| Priority | File | Role |
|----------|------|------|
| 1 | `{FolderName}.usd` | Convenience wrapper |
| 2 | `geo.usd` | Direct geometry layer |
| 3 | `payload.usd` | Assembly entry point |

**Excluded** from standalone asset detection:

- `mtl.usd` / `mtl.usdc` / `mtl.usda` (material layer only)
- `geo.usd` and `payload.usd` when a higher-priority file was already selected

Example layout (matches [Asset Library Builder USD structure](../asset_library_builder/README.md#usd-structure)):

```
Models/SciFi_Panel_A/
├── SciFi_Panel_A.usd   # wrapper (selected as primary)
├── payload.usd
├── geo.usd
└── mtl.usd
```

Scan result: **one** asset named `SciFi_Panel_A`, with `main_asset_file_path` pointing to `SciFi_Panel_A.usd`.

If no wrapper exists:

```
Models/MyAsset/
├── geo.usd             # selected as primary
└── payload.usd
```

LOD or letter variants inside a KB3D folder (e.g. `MyAsset_high.usd`, `MyAsset_B.usd`) are still detected as **geo variants** using the same suffix logic as ABC/FBX imports.

---

## Scanning a KB3D library

For a library such as `.../secrets of the luminara/Models`:

1. Open Batch Asset Builder
2. Set **Geometry Folder** to the `Models` path
3. Enable **Recursive**
4. Click **Scan**

Each model subfolder should appear as **one row** (folder name = asset name). You should **not** see separate `geo`, `payload`, or `mtl` rows for the same folder.

---

## Configuration

Optional file: [`geo_variant_config.json`](geo_variant_config.json) (same directory as `batch_asset_builder.py`):

```json
{
  "mode": "extend",
  "suffixes": ["_high", "_low", "_lod0"],
  "patterns": ["_[A-Z]$", "_v\\d+$"],
  "usd_primary_priority": ["{folder_name}.usd", "geo.usd", "payload.usd"],
  "usd_exclude": ["mtl.usd", "mtl.usdc"]
}
```

Environment variables (override JSON contents):

| Variable | Purpose |
|----------|---------|
| `LOPS_GEO_SUFFIXES` | Comma/semicolon list of variant suffix literals |
| `LOPS_GEO_SUFFIX_PATTERNS` | Comma/semicolon list of regex patterns |
| `LOPS_GEO_SUFFIX_MODE` | `extend` (default) or `override` |

---

## Related tools

| Tool | Purpose |
|------|---------|
| [`lops_asset_builder_v3.py`](lops_asset_builder_v3.py) | Interactive single-asset LOPS builder (manual file pick) |
| [`lops_asset_builder_cli.py`](lops_asset_builder_cli.py) | Headless build from JSON |
| [Asset Library Builder](../asset_library_builder/README.md) | **Create** KB3D payload/geo/mtl structure |
| [KB3D USD Builder](../kb3d_tools/KB3D_USD_BUILDER_README.md) | KB3D USD conventions and roles |

The batch scanner **does not** create payload/geo/mtl layers — it only discovers existing folders and writes build configs.

---

## Tests

Unit tests for USD primary selection (no Houdini required):

```bash
cd scripts/python
python3 tools/lops_asset_builder_v3/tests/test_usd_primary_selection.py -v
```
