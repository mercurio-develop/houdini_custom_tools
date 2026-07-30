# TexToMtlx_USD Examples

This folder contains practical examples demonstrating different ways to use the TexToMtlx_USD package.

## Examples Overview

### 1. simple_example.py
**Use Case**: Basic single material export

Shows the most straightforward usage:
- Export one MaterialX file from a texture folder
- Create a corresponding USD file
- Minimal configuration required

**When to use**: Quick tests, single material conversions, learning the basics

```python
from tools.material_tools.TexToMtlx_USD import (
    export_materialx_from_textures,
    create_kb3d_style_usd
)
```

---

### 2. batch_example.py
**Use Case**: Convert entire texture library at once

Demonstrates batch processing:
- Auto-detect all materials in a folder
- Convert all materials to MaterialX + USD
- Set custom kit metadata
- Get detailed results for each material

**When to use**: Converting texture libraries, bulk operations, production pipelines

```python
from tools.material_tools.TexToMtlx_USD import convert_textures_to_materialx
```

---

### 3. class_based_example.py
**Use Case**: Fine-grained control over export

Shows how to use the exporter classes directly:
- MaterialXExporter for MaterialX creation
- USDExporter for USD creation
- Custom colorspace, MaterialX version, texture variants
- Access to detailed export metadata

**When to use**: Advanced customization, integration with existing tools, debugging

```python
from tools.material_tools.TexToMtlx_USD import MaterialXExporter, USDExporter
```

---

### 4. pipeline_integration_example.py
**Use Case**: Production pipeline with versioning

Demonstrates a complete material library management system:
- Organized folder structure
- Multiple library versions
- Manifest file generation
- Proper metadata tracking

**When to use**: Production pipelines, asset management systems, library versioning

```python
class MaterialLibraryManager:
    """Custom pipeline integration"""
```

---

## Running Examples

### From Houdini Python Shell

```python
# Simple example
exec(open('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/material_tools/TexToMtlx_USD/examples/simple_example.py').read())

# Batch example
exec(open('/path/to/examples/batch_example.py').read())
```

### From Command Line (if using Houdini Python)

```bash
cd /home/tushita/houdini21.0/custom_tools/scripts/python/tools/material_tools/TexToMtlx_USD/examples
hython simple_example.py
```

### As Python Module

```python
import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python')

from tools.material_tools.TexToMtlx_USD.examples import simple_example
# Run example code...
```

---

## Customizing Examples

Before running, update these paths in each example:

```python
# Update texture folder path
texture_folder = '/your/textures/path'

# Update output folder path
output_folder = '/your/output/path'

# Update material name (if applicable)
material_name = 'YourMaterialName'
```

---

## Expected Output

Each example will create:

**MaterialX files (.mtlx)**:
- XML format
- MaterialX 1.38 standard
- Contains nodegraph and material definitions
- References texture files

**USD files (.usd)**:
- ASCII format (human-readable)
- References MaterialX file
- Includes texture variants
- KB3D-compatible metadata

**Example output structure**:
```
output_folder/
├── Material1.mtlx
├── Material1.usd
├── Material2.mtlx
├── Material2.usd
└── ...
```

---

## Troubleshooting

### Import Errors
Ensure your Python path includes the custom tools directory:
```python
import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python')
```

### Texture Detection Issues
Textures must follow naming convention:
```
MaterialName_textureType.extension

Examples:
- WoodOak_basecolor.png
- WoodOak_metallic.png
- WoodOak_roughness.png
```

Supported texture types: basecolor, metallic, roughness, normal, opacity, emission, displacement

### Path Issues
Use absolute paths or properly set relative paths:
```python
# Absolute
texture_folder = '/full/path/to/textures'

# Relative (from current working directory)
texture_folder = './textures'
```

---

## Next Steps

After running examples:

1. **Test in Houdini**: Load USD files with a Reference LOPS node
2. **Customize**: Modify kit_info, texture_variants, colorspace settings
3. **Integrate**: Adapt pipeline_integration_example for your studio
4. **Extend**: Create custom exporters based on MaterialXExporter/USDExporter

---

## Additional Resources

- **[Main README](../README.md)** - Package overview and API
- **[Quick Start](../docs/QUICK_START.md)** - Fast reference guide
- **[Complete Docs](../docs/README_STANDALONE_MTLX.md)** - Full documentation
- **[Integration Guide](../docs/INTEGRATION_GUIDE.md)** - Add to tex_to_mtlx
- **[Metadata Guide](../docs/KB3D_METADATA_GUIDE.md)** - Custom metadata

---

**Note**: Examples use KB3D reference materials by default. Update paths to your own texture libraries for testing.
