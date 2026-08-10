# TexToMtlx_USD - Standalone MaterialX & USD Exporter

> Convert texture folders directly to MaterialX and USD files without Houdini nodes

## Overview

TexToMtlx_USD is a modular toolkit for creating production-ready MaterialX and USD materials from texture folders. It provides both a simple UI and programmatic API for batch processing materials with full KB3D compatibility.

### Key Features

- ✅ **No Houdini Nodes Required** - Direct file export from textures
- ✅ **KB3D Compatible** - Matches KB3D MaterialX/USD standards exactly
- ✅ **Material Name Preservation** - Keeps original casing (KB3D_MTM_Decals, not kb3d_mtm_decals)
- ✅ **UDIM Support** - Auto-detection and proper formatting
- ✅ **Texture Variants** - jpg1k, jpg2k, jpg4k, png1k, png2k, png4k
- ✅ **Custom Metadata** - Kit name, ID, and version tracking
- ✅ **ASCII USD** - Human-readable .usd files (like KB3D)
- ✅ **Modular Design** - Use components independently or together

## Quick Start

### Launch UI Tool

```python
# From Houdini Python Shell
from tools.material_tools.TexToMtlx_USD import show_standalone_converter
show_standalone_converter()
```

### 5-Step Workflow

1. **Select Texture Folder** → Browse to folder with textures
2. **Click Scan** → Auto-detect materials
3. **Select Output Folder** → Where to save .mtlx and .usd files
4. **Configure Options** → Set metadata, variants, etc.
5. **Export Materials** → Done!

## Package Structure

```
TexToMtlx_USD/
├── __init__.py                    # Package initialization
├── materialx_exporter.py          # MaterialX document creation
├── usd_exporter.py                # USD file creation with variants
├── tex_to_mtlx_standalone.py     # UI tool and batch functions
├── docs/                          # Documentation
│   ├── QUICK_START.md             # Quick reference guide
│   ├── README_STANDALONE_MTLX.md  # Complete documentation
│   ├── INTEGRATION_GUIDE.md       # Integration with tex_to_mtlx
│   └── KB3D_METADATA_GUIDE.md     # Metadata customization
└── examples/                      # Example scripts
```

## Components

### 1. MaterialX Exporter (`materialx_exporter.py`)

Creates MaterialX documents from texture folders.

```python
from tools.material_tools.TexToMtlx_USD import export_materialx_from_textures

result = export_materialx_from_textures(
    texture_folder='/path/to/textures',
    output_file='/output/Material.mtlx',
    material_name='MyMaterial',
    relative_texture_path='../../Textures/png4k/'
)
```

**Features:**
- Auto-detects texture types (basecolor, metallic, roughness, normal, etc.)
- Uses tex_to_mtlx detection logic for consistency
- UDIM support with `<UDIM>` pattern
- Proper colorspace handling (sRGB for color, linear for data)
- Normalmap node creation for normal textures

### 2. USD Exporter (`usd_exporter.py`)

Creates USD files referencing MaterialX materials.

```python
from tools.material_tools.TexToMtlx_USD import create_kb3d_style_usd

result = create_kb3d_style_usd(
    material_name='MyMaterial',
    mtlx_file='./MyMaterial.mtlx',
    output_file='./MyMaterial.usd',
    kit_info={
        'kitDisplayName': 'My Materials',
        'kitId': 'my_materials',
        'kitVersion': '1.0.0'
    }
)
```

**Features:**
- ASCII format USD (human-readable like KB3D)
- Texture variants (jpg1k, jpg2k, jpg4k, png1k, png2k, png4k)
- Class-based inheritance pattern
- Instanceable materials
- Custom metadata support

### 3. Standalone Converter (`tex_to_mtlx_standalone.py`)

UI tool and batch processing functions.

```python
from tools.material_tools.TexToMtlx_USD import convert_textures_to_materialx

results = convert_textures_to_materialx(
    texture_folder='/path/to/textures',
    output_folder='/output',
    kit_info={'kitDisplayName': 'Wood Library', ...}
)
```

## Texture Naming Convention

Materials are detected based on texture naming:

```
MaterialName_textureType.extension

Examples:
- WoodOak_basecolor.png
- WoodOak_metallic.png
- WoodOak_roughness.png
- WoodOak_normal.png
```

### Supported Texture Types

| Type | Aliases | MaterialX Output |
|------|---------|------------------|
| Base Color | basecolor, diffuse, albedo | image_base_color |
| Metalness | metalness, metallic, metal | image_metalness |
| Roughness | roughness, rough | image_specular_roughness |
| Normal | normal, nor, nrm | image_normal → normalmap |
| Opacity | opacity, alpha | image_opacity |
| Emission | emission, emissive | image_emission_color |
| Displacement | displacement, disp, height | image_displacement |

## Output Format

### MaterialX (.mtlx)

```xml
<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_MyMaterial">
    <image name="image_base_color" type="color3">
      <input name="file" type="filename"
             value="../../Textures/png4k/MyMaterial_basecolor.png"
             colorspace="srgb_texture" />
    </image>
    ...
  </nodegraph>

  <standard_surface name="SR_MyMaterial" type="surfaceshader">
    <input name="base_color" type="color3"
           output="image_base_color_output"
           nodegraph="NG_MyMaterial" />
    ...
  </standard_surface>

  <surfacematerial name="MyMaterial" type="material">
    <input name="surfaceshader" type="surfaceshader"
           nodename="SR_MyMaterial" />
  </surfacematerial>
</materialx>
```

### USD (.usd with ASCII content)

```usda
#usda 1.0
(
    defaultPrim = "MyMaterial"
    metersPerUnit = 1
    upAxis = "Y"
)

def Material "MyMaterial" (
    assetInfo = {
        dictionary kb3d = {
            string kitDisplayName = "My Materials"
            string kitId = "my_materials"
            string kitVersion = "1.0.0"
        }
    }
    prepend inherits = </__class__/MyMaterial>
    instanceable = true
    prepend references = @./MyMaterial.mtlx@</MaterialX/Materials/MyMaterial>
    variants = {
        string texture_variant = "png4k"
    }
)
{
    variantSet "texture_variant" = {
        "png4k" { ... }
        "jpg2k" { ... }
        ...
    }
}

class "__class__"
{
    class "MyMaterial" { }
}
```

## Documentation

### Quick References
- **[QUICK_START.md](docs/QUICK_START.md)** - TL;DR guide, 5-minute setup
- **[README_STANDALONE_MTLX.md](docs/README_STANDALONE_MTLX.md)** - Complete documentation

### Integration & Advanced
- **[INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md)** - Add to existing tex_to_mtlx tool
- **[KB3D_METADATA_GUIDE.md](docs/KB3D_METADATA_GUIDE.md)** - Custom metadata setup

## Use Cases

### 1. Batch Material Export
Convert entire texture library to MaterialX/USD:

```python
from tools.material_tools.TexToMtlx_USD import convert_textures_to_materialx

convert_textures_to_materialx(
    texture_folder='/project/textures/wood',
    output_folder='/project/materials/wood'
)
```

### 2. Material Library Versioning
Track different versions:

```python
kit_v1 = {'kitDisplayName': 'Metal Library', 'kitVersion': '1.0.0'}
kit_v2 = {'kitDisplayName': 'Metal Library', 'kitVersion': '2.0.0'}
```

### 3. Pipeline Integration
Integrate with asset management systems:

```python
def export_material_kit(kit_name, version):
    kit_info = {
        'kitDisplayName': kit_name,
        'kitId': kit_name.lower().replace(' ', '_'),
        'kitVersion': version
    }

    convert_textures_to_materialx(
        texture_folder=f'/assets/{kit_name}/textures',
        output_folder=f'/assets/{kit_name}/materials',
        kit_info=kit_info
    )
```

## KB3D Compatibility

This tool creates materials that **exactly match KB3D standards**:

| Feature | KB3D Original | Our Export | Status |
|---------|---------------|------------|--------|
| MaterialX version | 1.38 | 1.38 | ✅ Match |
| Colorspace | lin_rec709 | lin_rec709 | ✅ Match |
| Material name casing | Original | Original | ✅ Match |
| USD format | ASCII (.usd) | ASCII (.usd) | ✅ Match |
| Variant order | jpg1k...png4k | jpg1k...png4k | ✅ Match |
| Class inheritance | Yes | Yes | ✅ Match |
| Metadata structure | kb3d dict | kb3d dict | ✅ Match |

## Requirements

- **Houdini**: 21.0+ (for MaterialX 1.38 and USD support)
- **Python**: 3.11+ (Houdini's Python)
- **Libraries**: MaterialX, USD/pxr, PySide6 (all included with Houdini)

## API Reference

### Functions

```python
# MaterialX Export
export_materialx_from_textures(texture_folder, output_file, material_name, **kwargs)

# USD Export
export_usd_material(material_name, mtlx_file, output_file, **kwargs)
create_kb3d_style_usd(material_name, mtlx_file, output_file, kit_info=None)

# Batch Conversion
convert_textures_to_materialx(texture_folder, output_folder, kit_info=None, **kwargs)

# UI Tool
show_standalone_converter()
```

### Classes

```python
# MaterialX Exporter
MaterialXExporter()
  .export_from_folder(texture_folder, output_file, material_name, ...)

# USD Exporter
USDExporter()
  .export_material_usd(material_name, mtlx_file, output_file, ...)
  .create_simple_usd_reference(material_name, mtlx_file, output_file)

# UI Converter
StandaloneMaterialXConverter()  # PySide6 QMainWindow
```

## Testing

Run the test suite:

```python
from tools.material_tools.TexToMtlx_USD.examples import test_example
test_example.run_all_tests()
```

## Changelog

### Version 1.0.0 (2025-10-28)
- Initial release
- MaterialX exporter with tex_to_mtlx detection logic
- USD exporter with KB3D compatibility
- Standalone UI tool
- KB3D metadata support
- ASCII USD format
- Material name casing preservation
- Complete documentation

## Support

For issues or questions:
- Check documentation in `docs/` folder
- See `CLAUDE.md` in repository root
- Review KB3D reference materials

## License

Part of Custom Houdini Tools collection.

---

**Version**: 1.0.0
**Created**: 2025-10-28
**Compatible with**: Houdini 21.0+, KB3D Standards
