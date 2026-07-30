# Asset Folder Analyzer UI

## Overview

The **Asset Folder Analyzer UI** is an interactive graphical tool that combines folder scanning, asset analysis, and import capabilities into one unified interface.

## Features

### 1. Interactive Folder Scanning
- Browse and select asset folders
- Configure geometry and texture subfolder names
- Real-time scan with results preview

### 2. Detailed Results Display
- **Summary view**: Quick overview of file counts and variants
- **Geometry tree**: Organized view of all geometry files by folder
- **Texture tree**: Texture folders sorted by priority (4k > 2k > 1k)
- **Details tab**: Full scan results in structured format

### 3. One-Click Import Actions
- **Import Geometry**: Create USD references with spatial distribution
- **Expand Materials**: Convert USD materials to editable VOPs
- **Import Both**: Combined geometry + materials import

### 4. Customizable Settings
- Layout type (Grid, Line, Circular)
- Spacing between assets
- Merge materials option

## Usage

### Launching the Tool

```python
from tools.asset_folder_analyzer_ui import show_asset_folder_analyzer

# Show the UI
window = show_asset_folder_analyzer()
```

Or from Houdini's Python Shell:

```python
import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python')
from tools.asset_folder_analyzer_ui import show_asset_folder_analyzer
show_asset_folder_analyzer()
```

### Workflow

**Step 1: Select Folder**
1. Click "Browse..." or enter path manually
2. Set geometry subfolder name (default: "geo")
3. Set texture subfolder name (default: "tex")

**Step 2: Scan**
1. Click "Scan Folder" button
2. Wait for scan to complete
3. Review results in the three tabs:
   - **Geometry Files**: Tree view of all assets
   - **Texture Folders**: Available texture sets
   - **Details**: Complete scan data

**Step 3: Import**

Choose one of the import actions:

**Import Geometry Only:**
- Select layout type (Grid/Line/Circular)
- Set spacing between assets
- Click "Import Geometry as USD References"

**Expand Materials Only:**
- Choose whether to merge all materials
- Click "Expand Materials to Editable VOPs"

**Import Everything:**
- Configure both geometry and material settings
- Click "Import Both Geometry + Materials"

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│         Asset Folder Analyzer                       │
├─────────────────────────────────────────────────────┤
│ 1. Select Asset Folder                              │
│   ┌──────────────────────────────┐ [Browse...]     │
│   │ /path/to/assets              │                  │
│   └──────────────────────────────┘                  │
│   Geo Subfolder: [geo]  Tex Subfolder: [tex]       │
│   ┌──────────────────────────────┐                  │
│   │      SCAN FOLDER             │                  │
│   └──────────────────────────────┘                  │
├─────────────────────────────────────────────────────┤
│ 2. Scan Results                                     │
│   Geometry: 36  Textures: 2  Variants: 18          │
│   ┌─────────────────────────────────────────────┐  │
│   │ [Geometry Files] [Texture Folders] [Details]│  │
│   │ ┌─────────────────────────────────────────┐ │  │
│   │ │ └─ KB3D_NEC_BldgLG_A                    │ │  │
│   │ │    ├─ payload.usd (Main)                │ │  │
│   │ │    └─ KB3D_NEC_BldgLG_A.usd (Variant)   │ │  │
│   │ └─────────────────────────────────────────┘ │  │
│   └─────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│ 3. Import Actions                                   │
│   ┌──────────────────────────────────────────────┐ │
│   │ Import Geometry as USD References          │ │
│   └──────────────────────────────────────────────┘ │
│   Layout: [Grid ▼]  Spacing: [15.0 units]         │
│                                                     │
│   ┌──────────────────────────────────────────────┐ │
│   │ Expand Materials to Editable VOPs          │ │
│   └──────────────────────────────────────────────┘ │
│   ☐ Merge All                                      │
│                                                     │
│   ┌──────────────────────────────────────────────┐ │
│   │    Import Both Geometry + Materials        │ │
│   └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Examples

### Example 1: KB3D NeoCity Buildings

**Input:**
- Folder: `/media/tushita/TUSHITA_LINUX_DATA/assets/kb3d_neocity`
- Geometry Subfolder: `Models`
- Texture Subfolder: `Textures`

**Scan Results:**
- 36 geometry files found
- 9 building variants (LG_A, LG_B, LG_C, MD_A, MD_B, MD_C, SM_A, SM_B, SM_C)
- 2 texture folders (4k and 2k)

**Import:**
1. Click "Import Both Geometry + Materials"
2. Result:
   - `/obj/stage/kb3d_neocity_geometry` - 9 buildings in grid layout
   - `/obj/stage/kb3d_neocity_materials` - 9 editable material libraries

### Example 2: Custom Asset Pack

**Input:**
- Folder: `/projects/my_assets/prop_cargo`
- Geometry Subfolder: `geo` (default)
- Texture Subfolder: `tex` (default)

**Scan Results:**
- 3 geometry variants
- 1 main texture folder (2k)

**Import:**
1. Set layout to "Line"
2. Set spacing to 5.0 units
3. Click "Import Geometry as USD References"
4. Assets appear in a straight line

## Integration with Other Tools

### Uses These Modules:
- `modules/asset_folder_scanner.py` - Folder scanning
- `modules/usd_reference_importer.py` - Geometry import
- `modules/usd_material_expander.py` - Material expansion

### Can Be Extended:
The UI is designed to be modular. You can add new actions by:
1. Adding buttons to the actions section
2. Implementing handler methods
3. Calling additional module functions

## Technical Details

### Window Properties
- Size: 1000x800 pixels
- Parent: Houdini main window
- Modal: No (can work alongside Houdini)

### Data Flow
```
User Input → Scan Folder → Parse Results → Display in Trees → User Action → Import/Expand
```

### Error Handling
- Invalid paths show warning dialogs
- Failed scans display error messages
- Import errors show detailed error information

### Status Updates
- Status bar shows current operation
- Blocking dialogs prevent multiple operations
- Action buttons disabled until scan completes

## API Reference

### Main Class

```python
class AssetFolderAnalyzerUI(QtWidgets.QMainWindow):
    def __init__(self)
    def _browse_folder(self)           # Open folder browser
    def _scan_folder(self)             # Scan selected folder
    def _display_results(self)         # Update UI with results
    def _import_geometry(self)         # Import geometry action
    def _expand_materials(self)        # Expand materials action
    def _import_all(self)              # Combined import action
```

### Entry Point

```python
def show_asset_folder_analyzer() -> AssetFolderAnalyzerUI:
    """
    Show the Asset Folder Analyzer UI.
    Returns the window instance.
    """
```

## Keyboard Shortcuts

- **Ctrl+O**: Browse folder (when focus is on path input)
- **Enter**: Scan folder (when focus is on path input)
- **Esc**: Close window

## Customization

### Changing Default Subfolders

Edit the default values in `_create_folder_section()`:

```python
self.geo_subfolder_input = QtWidgets.QLineEdit("Models")  # Changed from "geo"
self.tex_subfolder_input = QtWidgets.QLineEdit("Textures")  # Changed from "tex"
```

### Adding Custom Actions

Add a new button and handler:

```python
# In _create_actions_section():
self.custom_btn = QtWidgets.QPushButton("My Custom Action")
self.custom_btn.clicked.connect(self._my_custom_action)

# Add handler method:
def _my_custom_action(self):
    if not self.scan_result:
        return
    # Your custom logic here
```

### Styling

The UI uses Houdini's native styling. To customize:

```python
# In __init__():
self.setStyleSheet("""
    QPushButton {
        background-color: #4CAF50;
        color: white;
    }
""")
```

## Limitations

- Requires Houdini 19.5+ for full USD/MaterialX support
- Large asset folders (1000+ files) may take time to scan
- UI must remain open during import operations
- Single folder scan at a time

## Troubleshooting

### "No geometry files found"
- Check that the geometry subfolder name is correct
- Verify files have supported extensions (.usd, .usda, .usdc, .abc, .obj, .fbx)

### "Materials not found"
- Ensure the geometry subfolder contains `mtl.usd` files
- Check that materials are in USD format with MaterialX shaders

### Import fails
- Verify you have write permissions in the Houdini scene
- Check that file paths don't contain special characters
- Ensure USD files are not corrupted

## Future Enhancements

Potential additions:
- Multi-folder batch scanning
- Asset preview thumbnails
- Custom import presets
- Export scan results to JSON
- Material assignment to geometry
- Automatic lookdev setup

## See Also

- `asset_folder_scanner.py` - Core scanning logic
- `usd_reference_importer.py` - Geometry import module
- `usd_material_expander.py` - Material expansion module
- `README_ASSET_FOLDER_SCANNER.md` - Scanner documentation
- `README_USD_MATERIAL_EXPANDER.md` - Material expander documentation

## Author

Created as part of the custom_tools pipeline for Houdini 21.0.

## Version

v1.0 - Initial release with scanning and import capabilities
