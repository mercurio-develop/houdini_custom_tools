---
name: houdini-shelf-tools
description: >-
  Adds and maintains Custom Tools shelf entries in custom_tools.shelf. Use when adding
  a shelf tool, custom_tools.shelf, shelf button, toolbar entry, or wiring Python to shelf.
---

# Houdini Shelf Tools

Shelf file: `toolbar/custom_tools.shelf`  
Audit reference: `scripts/python/SHELF_AUDIT.md`

## Rules

1. **Logic in Python modules** — never large inline Python in shelf XML
2. **Thin shelf wrapper** — import, reload, call one function
3. **Keep shelf + module in sync** when adding or renaming tools
4. Update `SHELF_AUDIT.md` inventory when adding tools

## Add a new shelf tool

### Step 1: Create module

```
scripts/python/tools/my_tool/
├── __init__.py
└── my_tool_ui.py      # def show_dialog() or def run()
```

### Step 2: Register on toolshelf

In `custom_tools.shelf`, add to `<toolshelf name="Custom Tools">`:

```xml
<memberTool name="my_tool"/>
```

### Step 3: Add tool block

```xml
<tool name="my_tool" label="My Tool" icon="hicon:/SVGIcons.index?SHELF_asset_library.svg">
  <script scriptType="python"><![CDATA[import importlib
import tools.my_tool.my_tool_ui as my_tool_ui

importlib.reload(my_tool_ui)
my_tool_ui.show_dialog()]]></script>
</tool>
```

## Shelf script template

```python
import importlib
import tools.<package>.<module> as mod

importlib.reload(mod)
mod.run()
```

Matches existing patterns: `lops_asset_builder`, `psx_tools`, `batch_asset_builder`.

## Icon IDs

Prefer Houdini SVG icons:

```
hicon:/SVGIcons.index?SHELF_asset_library.svg
hicon:/SVGIcons.index?LOP_editmaterial.svg
hicon:/SVGIcons.index?SOP_polyreduce.svg
hicon:/SVGIcons.index?LOP_stagemanager.svg
```

## Anti-patterns (from SHELF_AUDIT)

| Bad | Good |
|-----|------|
| 100+ lines inline Python in shelf | Module in `tools/` |
| Duplicate HScript of v3 logic | Import `component_material_custom.py` |
| Hardcoded H21 HIP paths | `$CUSTOM_TOOLS/templates/...` with existence check |
| Missing module (broken shelf) | Verify import before merging |

## Broken shelf tools to avoid

- `asset_builder` → use `lops_asset_builder` (v3)
- `asset_builder_v2` → archived; use v3
- `spaceship_visualizer` → module missing

## Reload after shelf/Python edits

Alt+click **Reload Packages** or HMCP `reload_custom_tools`.

## PSX example (reference)

```xml
<tool name="psx_tools" label="PSX Retro Tools" icon="hicon:/SVGIcons.index?SOP_polyreduce.svg">
  <script scriptType="python"><![CDATA[import importlib
from tools.psx_tools import psx_tools_ui

importlib.reload(psx_tools_ui)
psx_tools_ui.show_psx_tools_dialog()]]></script>
</tool>
```
