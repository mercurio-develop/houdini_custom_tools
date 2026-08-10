# Shared modules

Reusable code with **no shelf tool** — imported by `tools/`, `HMCP/handlers/`, and `pipeline/`.

## Module map

| Module | Role |
|--------|------|
| `misc_utils.py` | Sanitize names, material naming config |
| `asset_folder_scanner.py` | KB3D/geo/tex folder layout scan |
| `usd_reference_importer.py` | Reference layout in LOPs |
| `houdini_node_utils.py` | Cook/GC helpers |
| `usd_solaris_utils.py` | USD stage discovery, materials, textures, USDZ |
| `usd_material_naming.py` | Material naming strategies for import |
| `texture_path_repair.py` | Repair/compare texture paths |
| `lop_helpers.py` | Find componentoutput and other LOP nodes |

## Guidelines

- Keep functions pure where possible; pass `hou.Node` / paths explicitly.
- No PySide6 UI here — UI lives under `tools/`.
- Headless-safe subsets belong in functions that don't import `hou` at module level when feasible.

See [`../CONVENTIONS.md`](../CONVENTIONS.md) for naming and import rules.
