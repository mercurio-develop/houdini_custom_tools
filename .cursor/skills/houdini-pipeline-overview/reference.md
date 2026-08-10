# Directory reference

From `scripts/python/README.md` and `ARCHITECTURE.md`.

```
python/
├── ARCHITECTURE.md
├── SHELF_AUDIT.md
├── integrations/             # ftrack + Iconik (no hou)
├── mcp/                      # Production Hub MCP
├── pipeline/                 # Project folders, save tool
├── projects/production_hub/
├── HMCP/                     # Houdini ↔ Cursor MCP
├── tools/
│   ├── lops_asset_builder_v3/   # Flagship LOPS USD/MaterialX builder
│   │   ├── asset_builder_config.py
│   │   ├── asset_builder_engine.py
│   │   ├── geo_mtl_builder.py
│   │   ├── material_builder.py
│   │   ├── asset_builder_graph.py
│   │   ├── batch_asset_builder.py
│   │   ├── lops_asset_builder_cli.py
│   │   └── examples/            # JSON configs
│   ├── psx_tools/               # PSX retro preprocessing
│   ├── kb3d_tools/              # USD library toolkit
│   ├── asset_library_builder/   # build_from_parts()
│   ├── production_hub/
│   ├── material_tools/
│   │   ├── TexToMtlX_V2/        # In-Houdini MaterialX
│   │   └── TexToMtlx_USD/       # Standalone USD export
│   ├── batch_import_workflow/
│   ├── _archive/                # Superseded LOPS builders
│   └── *.py                     # Stage utilities
├── modules/
└── custom_utils.py              # reload_packages()
```

## Stack

- Houdini 22.x (`hou`), Python 3.11+, PySide6
- USD (`pxr`) for library tools
- Optional: `httpx`, `ftrack-python-api`, Pillow (PSX dither)

## Key docs

| Doc | Path |
|-----|------|
| Main README | `scripts/python/README.md` |
| Architecture | `scripts/python/ARCHITECTURE.md` |
| Shelf audit | `scripts/python/SHELF_AUDIT.md` |
| HMCP setup | `scripts/python/HMCP/CURSOR_SETUP.md` |
| Batch scanner | `tools/lops_asset_builder_v3/BATCH_SCANNER_README.md` |
