# Asset Library Builder

A comprehensive tool for building production-ready USD asset libraries in Houdini.

**Version 1.1.0** - Now uses mesh names directly as material names (no conversion). This maintains consistency with the original FBX asset structure.

## Features

- **Proper USD Structure**: Creates payload → geo + mtl pattern for efficient asset loading
- **Texture Variants**: Supports jpg1k, jpg2k, png4k texture resolution switching
- **Automatic Instancing**: Detects and marks duplicate parts for efficient rendering
- **Material Library**: Automatically references materials from centralized library
- **Progress Reporting**: Real-time progress bar and status updates
- **Batch Processing**: Process multiple assets efficiently

## USD Structure

The builder creates a standard USD asset structure:

```
Models/AssetName/
├── payload.usd          # Main assembly (references mtl + geo)
├── geo.usd              # Geometry with instanceable parts
├── mtl.usd              # Material library with variants
└── AssetName.usd        # Convenience wrapper
```

### Benefits

- **8x smaller files**: Proper structure vs flat assembly
- **Texture switching**: Runtime resolution control
- **Efficient instancing**: Automatic duplicate detection
- **Material reuse**: Centralized material library

## Usage

### From UI

```python
from tools.asset_library_builder import show_ui
show_ui()
```

### Programmatically

```python
from tools.asset_library_builder.asset_builder import build_from_parts

payload_path = build_from_parts(
    parts_folder="/path/to/parts/MyAsset",
    asset_name="MyAsset",
    models_folder="/path/to/Models",
    materials_folder="/path/to/Materials",
    texture_variants=["jpg1k", "jpg2k", "png4k"],
    progress_callback=lambda percent, msg: print(f"{percent}%: {msg}")
)
```

## Input Structure

Your parts folder should contain subfolders, each representing a part:

```
parts/MyAsset/
├── PartA/
│   ├── geo.usd          # USD geometry
│   └── payload.usd      # (optional)
├── PartB/
│   ├── geo.usd
│   └── payload.usd
└── PartC/
    └── PartC.bgeo.sc    # Or BGEO format
```

The builder will:
1. Scan all part subfolders
2. Extract material bindings from geometry
3. Import each part into unified geo.usd
4. Create material library references
5. Set up texture variant system

## Material Library

Materials should be organized in a centralized library:

```
Materials/
├── MaterialA/
│   ├── MaterialA.usd    # Main material USD
│   └── textures/
│       ├── jpg1k/       # Low-res textures
│       ├── jpg2k/       # Mid-res textures
│       └── png4k/       # High-res textures
└── MaterialB/
    └── ...
```

The builder creates references to these materials and sets up variant switching.

## Texture Variants

The variant system allows runtime texture resolution switching:

```python
# In USD or Houdini
asset.GetVariantSet("texture_variant").SetVariantSelection("jpg2k")
```

This cascades down to all materials, switching all textures at once.

## Progress Callbacks

The builder supports progress callbacks for UI integration:

```python
def on_progress(percent: int, message: str):
    print(f"[{percent}%] {message}")

build_from_parts(..., progress_callback=on_progress)
```

Progress stages:
- 0-10%: Scanning parts
- 10-20%: Scanning materials
- 20-50%: Creating geo.usd
- 50-70%: Creating mtl.usd
- 70-85%: Creating payload.usd
- 85-100%: Creating main USD

## LOPS Network

The builder creates a temporary LOPS network:

```
primitive (root Xform) →
reference/sopimport (Part 1) →
reference/sopimport (Part 2) →
... (all parts) →
scope (material scope) →
primitive (Material 1) →
primitive (Material 2) →
... (all materials) →
configurestage (metadata) →
usd_rop (export)
```

This network is automatically cleaned up after export.

## Error Handling

The builder includes comprehensive error checking:

- Parameter validation before setting
- Clear error messages with context
- Material scanning before LOPS build (avoids stage cooking issues)
- Node name sanitization for special characters

## API Reference

### build_from_parts()

```python
def build_from_parts(
    parts_folder: str,
    asset_name: str,
    models_folder: str,
    materials_folder: str,
    texture_variants: List[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> str
```

**Parameters:**
- `parts_folder`: Folder containing part subfolders
- `asset_name`: Name for the asset
- `models_folder`: Base Models folder (will create asset subfolder)
- `materials_folder`: Materials folder for material references
- `texture_variants`: List of variants (default: ["jpg1k", "jpg2k", "png4k"])
- `progress_callback`: Optional callback(percent, message) for progress

**Returns:**
- Path to created payload.usd

**Raises:**
- `RuntimeError`: If parts folder is empty or critical parameters fail

### show_ui()

```python
def show_ui() -> AssetLibraryBuilderUI
```

Shows the interactive UI dialog.

**Returns:**
- Dialog instance

## Examples

### Basic Usage

```python
from tools.asset_library_builder import show_ui

# Launch UI
show_ui()
```

### Batch Processing

```python
from tools.asset_library_builder.asset_builder import build_from_parts
import os

assets_root = "/path/to/assets"
models_folder = "/path/to/Models"
materials_folder = "/path/to/Materials"

# Process all asset folders
for asset_name in os.listdir(assets_root):
    parts_folder = os.path.join(assets_root, asset_name)

    if os.path.isdir(parts_folder):
        print(f"Building {asset_name}...")

        build_from_parts(
            parts_folder=parts_folder,
            asset_name=asset_name,
            models_folder=models_folder,
            materials_folder=materials_folder
        )
```

### Custom Progress Tracking

```python
from PySide6 import QtWidgets

class ProgressDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.progress_bar = QtWidgets.QProgressBar()
        # ... setup UI

    def on_progress(self, percent, message):
        self.progress_bar.setValue(percent)
        self.status_label.setText(message)
        QtWidgets.QApplication.processEvents()

dialog = ProgressDialog()
dialog.show()

build_from_parts(
    ...,
    progress_callback=dialog.on_progress
)
```

## Troubleshooting

### "No parts found in folder"

- Ensure parts folder contains subfolders
- Each subfolder should have geo.usd or .bgeo file

### "Material not found"

- Check materials folder path is correct
- Verify material folders exist with {MaterialName}.usd files
- Materials must match names extracted from geometry bindings

### "NoneType has no attribute 'set'"

- This should not occur with error checking
- If it does, check Houdini version compatibility
- Verify node type names match your Houdini version

### Progress bar not updating

- Ensure you're calling from main thread
- Use `QtWidgets.QApplication.processEvents()` in callback
- Check callback is properly connected

## Version History

### 1.0.0 (Current)
- Initial release
- Progress bar support
- Generic Asset Library naming (removed KB3D references)
- Comprehensive error checking
- Material scanning optimization

## License

Custom Tools Internal Use

## Support

For issues or questions, contact the pipeline team or check the documentation at:
`/home/tushita/houdini21.0/custom_tools/scripts/python/tools/asset_library_builder/`
