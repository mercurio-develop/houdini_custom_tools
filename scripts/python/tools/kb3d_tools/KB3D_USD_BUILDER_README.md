# KB3D USD Builder

A comprehensive Python class system for creating production-ready USD assets following **KitBash3D** conventions. This modular system makes it easy to build USD asset libraries with proper layering, materials, variants, and hierarchy management.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Examples](#examples)
- [KB3D USD Structure](#kb3d-usd-structure)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The KB3D USD Builder is based on analysis of the **KitBash3D Mission to Minerva** library structure. It replicates the production-proven patterns used by KitBash3D, including:

- Three-layer USD structure (main/payload/data)
- MaterialX-based materials with texture variants
- Assembly/Component hierarchy with proper `kind` metadata
- Variant cascading for texture resolution switching
- Relative path references for relocatable assets
- Class inheritance patterns
- Instancing for memory optimization

### Analyzed Source Structure

```
kb3d_missiontominerva/
├── Materials/           # 65 materials with MaterialX
├── Models/              # 167 components and assemblies
├── Textures/            # 6 resolution variants (jpg/png 1k/2k/4k)
└── kb3d_metadata.json   # Version tracking
```

---

## ✨ Features

### 🎨 Material System
- **MaterialX integration** with standard_surface shader
- **Texture variant management** (jpg/png, 1k/2k/4k)
- **Complete texture map support**: basecolor, metallic, roughness, normal, opacity, emissive, displacement
- **Relative path handling** for relocatable assets
- **Automatic colorspace management** (sRGB vs linear)

### 🏗️ Component Builder
- **Three-layer structure**: main USD, payload USD, mtl/geo split
- **Material reference system** with variant cascading
- **Extent hint** support for bounding boxes
- **Lazy loading** via payloads

### 🏛️ Assembly Builder
- **Multi-component referencing** with transforms
- **Group/scope organization** for complex hierarchies
- **Instancing support** for memory optimization
- **Variant propagation** to all children
- **Kind metadata** (assembly/group/component)

### 🔧 Utility Features
- **Class inheritance patterns** for centralized overrides
- **KB3D metadata** embedding (kit ID, version, display name)
- **Convenience functions** for quick workflows
- **Batch processing** support

---

## 📦 Installation

### Prerequisites

```bash
# Houdini Python environment (includes USD)
# OR standalone USD Python libraries
pip install usd-core  # If not using Houdini
```

### Setup

```python
# Add to your Python path
import sys
sys.path.append('/path/to/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_usd_builder import KB3DUSDBuilder
```

---

## 🚀 Quick Start

### 1. Create an Asset Library

```python
from kb3d_usd_builder import KB3DUSDBuilder
from pathlib import Path

# Initialize builder
builder = KB3DUSDBuilder(
    base_path=Path("/my/asset/library"),
    kit_id="my_custom_kit",
    kit_display_name="My Custom Assets",
    kit_version="1.0.0"
)

# This creates:
# /my/asset/library/
#   ├── Materials/
#   ├── Models/
#   ├── Textures/
#   └── kb3d_metadata.json

builder.save_metadata()
```

### 2. Create a Material

```python
# Create material builder
mat_builder = builder.create_material_builder("CustomMetal_A")

# Add texture maps with variants
mat_builder.add_texture_map('basecolor', {
    'png1k': '../../Textures/png1k/CustomMetal_A_basecolor.png',
    'png4k': '../../Textures/png4k/CustomMetal_A_basecolor.png',
})

mat_builder.add_texture_map('metallic', {
    'png1k': '../../Textures/png1k/CustomMetal_A_metallic.png',
    'png4k': '../../Textures/png4k/CustomMetal_A_metallic.png',
})

mat_builder.add_texture_map('roughness', {
    'png1k': '../../Textures/png1k/CustomMetal_A_roughness.png',
    'png4k': '../../Textures/png4k/CustomMetal_A_roughness.png',
})

# Build material USD + MaterialX
mat_path = mat_builder.build(builder.materials_dir, default_variant='png1k')
```

### 3. Create a Component

```python
# Create component builder
comp_builder = builder.create_component_builder("CustomProp_A")

# Set bounding box
comp_builder.set_extent_hint(
    min_point=(-5.0, 0.0, -3.0),
    max_point=(5.0, 10.0, 3.0)
)

# Reference materials
comp_builder.add_material_reference(
    "CustomMetal_A",
    "../../Materials/CustomMetal_A/CustomMetal_A.usd"
)

# Build component (creates main.usd, payload.usd, mtl.usd)
# Note: You need to provide geo.usd separately
comp_path = comp_builder.build_main_usd()
```

### 4. Create an Assembly

```python
# Create assembly builder
asm_builder = builder.create_assembly_builder("CustomBuilding_A")

# Add component references with transforms
asm_builder.add_component_reference(
    component_name="Wall_North_001",
    component_path="../CustomWall_A/CustomWall_A.usd",
    transform={'translate': (0, 5, 20)},
    group_name="Walls",
    instanceable=True
)

asm_builder.add_component_reference(
    component_name="Wall_South_001",
    component_path="../CustomWall_A/CustomWall_A.usd",
    transform={'translate': (0, 5, -20), 'rotate': (0, 180, 0)},
    group_name="Walls",
    instanceable=True
)

# Build assembly
asm_path = asm_builder.build(default_variant='png1k')
```

---

## 🏗️ Architecture

### USD Layer Structure

The system uses a three-layer composition architecture:

```
Component.usd                    # Main file (public API)
├── [inherits] /__class__/Component
├── [payload] ./payload.usd      # Composition layer
│   ├── [reference] ./mtl.usd    # Material bindings
│   └── [reference] ./geo.usd    # Geometry data
└── [variants] texture_variant   # Variant definitions
```

### Directory Structure

```
AssetLibrary/
├── Materials/
│   └── MaterialName/
│       ├── MaterialName.usd     # Material with variants
│       └── MaterialName.mtlx    # MaterialX shader
├── Models/
│   ├── ComponentName/
│   │   ├── ComponentName.usd    # Main component file
│   │   ├── payload.usd          # Payload layer
│   │   ├── mtl.usd              # Material references
│   │   └── geo.usd              # Geometry (you provide)
│   └── AssemblyName/
│       └── AssemblyName.usd     # Assembly referencing components
├── Textures/
│   ├── png1k/                   # 1K PNG textures
│   ├── png2k/                   # 2K PNG textures
│   ├── png4k/                   # 4K PNG textures
│   ├── jpg1k/                   # 1K JPG textures
│   ├── jpg2k/                   # 2K JPG textures
│   └── jpg4k/                   # 4K JPG textures
└── kb3d_metadata.json           # Library metadata
```

### Variant System

Texture variants cascade from assembly → component → material:

```
Assembly (texture_variant = "png1k")
└── Component (inherits variant = "png1k")
    └── Material (switches to png1k textures)
```

Supported variants: `jpg1k`, `jpg2k`, `jpg4k`, `png1k`, `png2k`, `png4k`

---

## 📚 API Reference

### KB3DUSDBuilder

Main orchestrator class for building asset libraries.

```python
KB3DUSDBuilder(
    base_path: Path,
    kit_id: str = "custom_assets",
    kit_display_name: str = "Custom Assets",
    kit_version: str = "1.0.0"
)
```

**Methods:**
- `create_material_builder(material_name: str) -> KB3DMaterialBuilder`
- `create_component_builder(component_name: str) -> KB3DComponentBuilder`
- `create_assembly_builder(assembly_name: str) -> KB3DAssemblyBuilder`
- `save_metadata()` - Save kb3d_metadata.json

---

### KB3DMaterialBuilder

Builds materials with MaterialX and texture variants.

```python
KB3DMaterialBuilder(
    material_name: str,
    base_path: Path,
    metadata: Optional[KB3DMetadata] = None
)
```

**Methods:**

```python
add_texture_map(map_type: str, variants: Dict[str, str])
```
Add a texture map with variant paths.

**Supported map types:**
- `basecolor` - sRGB color texture
- `metallic` - Linear grayscale (0=dielectric, 1=metal)
- `roughness` - Linear grayscale (0=smooth, 1=rough)
- `normal` - Linear tangent-space normal map
- `opacity` - Linear grayscale (for transparency)
- `emissive` - sRGB color (for glow)
- `displacement` - Linear grayscale (for height)

```python
build(output_dir: Path, default_variant: str = 'png1k') -> Path
```
Build complete material USD with variants.

**Returns:** Path to created material USD file

---

### KB3DComponentBuilder

Builds component USD files with payload structure.

```python
KB3DComponentBuilder(
    component_name: str,
    output_dir: Path,
    metadata: Optional[KB3DMetadata] = None
)
```

**Methods:**

```python
set_extent_hint(min_point: Tuple[float, float, float],
                max_point: Tuple[float, float, float])
```
Set bounding box extent hint.

```python
add_material_reference(material_name: str, material_path: str)
```
Add a material reference for this component.

```python
build_main_usd(geo_usd_path: Optional[Path] = None) -> Path
```
Create main component USD file.

**Returns:** Path to created component USD file

---

### KB3DAssemblyBuilder

Builds assembly USD files with component references.

```python
KB3DAssemblyBuilder(
    assembly_name: str,
    output_dir: Path,
    metadata: Optional[KB3DMetadata] = None
)
```

**Methods:**

```python
add_component_reference(
    component_name: str,
    component_path: str,
    transform: Optional[Dict] = None,
    group_name: Optional[str] = None,
    instanceable: bool = True
)
```
Add a component reference to the assembly.

**Transform dict keys:**
- `translate`: (x, y, z) tuple
- `rotate`: (rx, ry, rz) tuple in degrees (XYZ Euler)
- `scale`: (sx, sy, sz) tuple

```python
set_extent_hint(min_point: Tuple[float, float, float],
                max_point: Tuple[float, float, float])
```
Set bounding box extent hint.

```python
build(default_variant: str = 'png1k') -> Path
```
Build the assembly USD file.

**Returns:** Path to created assembly USD file

---

### Convenience Functions

```python
build_simple_material(
    material_name: str,
    texture_folder: Path,
    output_dir: Path,
    metadata: Optional[KB3DMetadata] = None
) -> Path
```
Quick function to build a material from a texture folder.
Assumes KB3D naming: `{material_name}_{maptype}.{ext}`

```python
build_simple_component(
    component_name: str,
    geo_usd_path: Path,
    material_bindings: List[Dict[str, str]],
    output_dir: Path,
    metadata: Optional[KB3DMetadata] = None
) -> Path
```
Quick function to build a component.

---

## 💡 Examples

See `examples/kb3d_usd_builder_examples.py` for complete working examples:

1. **Creating a Complete Asset Library**
2. **Creating a Material with Texture Variants**
3. **Creating a Component with Material References**
4. **Creating an Assembly from Components**
5. **Using Convenience Functions**
6. **Advanced Material with All Texture Maps**
7. **Houdini Integration Workflow**
8. **Batch Processing Multiple Assets**

---

## 📐 KB3D USD Structure

### Patterns Discovered from KB3D Mission to Minerva

#### 1. **Three-Layer Composition**
- **Main USD**: Public API with variants and metadata
- **Payload USD**: Composition layer (references mtl + geo)
- **Data USDs**: mtl.usd (material bindings) + geo.usd (geometry)

#### 2. **Material Structure**
- **MaterialX (.mtlx)**: Shader graph definition
- **Material USD (.usd)**: Variants that override texture paths
- **Variants**: Switch between jpg/png and 1k/2k/4k resolutions

#### 3. **Hierarchy Patterns**
```
Assembly (kind: assembly)
├── Scope (kind: group)
│   ├── Component (kind: component, instanceable: true)
│   └── Component (kind: component, instanceable: true)
```

#### 4. **Composition Arcs Order**
1. Inherits (class patterns)
2. VariantSets (texture variants)
3. References (component/material references)
4. Payloads (lazy loading)

#### 5. **Naming Conventions**
- Materials: `KB3D_{KIT}_{MaterialType}{Property}`
- Components: `KB3D_{KIT}_{Category}{Size}{Type}_{Variant}`
- Textures: `{MaterialName}_{maptype}.{ext}`

#### 6. **Relative Paths**
- Sibling folders: `../ComponentName/file.usd`
- Materials: `../../Materials/MaterialName/file.usd`
- Textures: `../../Textures/png1k/texture.png`

---

## 🎯 Best Practices

### 1. **Organize Your Textures First**

Before building materials, organize textures by resolution:
```
Textures/
├── png1k/MaterialName_basecolor.png
├── png1k/MaterialName_metallic.png
├── png1k/MaterialName_roughness.png
├── ...
├── png4k/MaterialName_basecolor.png
└── ...
```

### 2. **Create Materials Before Components**

Materials should exist before you reference them in components.

### 3. **Use Groups for Organization**

In assemblies, use groups to organize components logically:
```python
asm_builder.add_component_reference(
    ...,
    group_name="Foundation"  # Logical grouping
)
```

### 4. **Enable Instancing**

For repeated components, always use `instanceable=True` to save memory:
```python
asm_builder.add_component_reference(
    ...,
    instanceable=True  # Memory optimization
)
```

### 5. **Set Extent Hints**

Always provide extent hints for better viewport performance:
```python
comp_builder.set_extent_hint(
    min_point=(-5, 0, -3),
    max_point=(5, 10, 3)
)
```

### 6. **Use Relative Paths**

Always use relative paths for relocatable assets:
```python
# Good
material_path = "../../Materials/Mat/Mat.usd"

# Bad
material_path = "/absolute/path/Materials/Mat/Mat.usd"
```

### 7. **Default Variant Selection**

Choose appropriate default variants based on your target platform:
- **Real-time**: `jpg1k` or `png1k`
- **Offline rendering**: `png4k`
- **Web/mobile**: `jpg1k`

---

## 🔧 Troubleshooting

### Issue: "Module not found: pxr"

**Solution:** Ensure you're using Houdini Python or have USD Python installed:
```bash
# Houdini
/opt/hfs21.0/bin/hython your_script.py

# OR install USD
pip install usd-core
```

### Issue: "Material not found in component"

**Solution:** Ensure material USD exists before referencing:
1. Create material first with `mat_builder.build()`
2. Then reference it in component with correct path

### Issue: "Variant not cascading to children"

**Solution:** The system automatically handles variant cascading. Ensure:
1. Parent has variant set defined
2. Children are properly referenced (not sublayered)
3. Variant is set on parent before adding children

### Issue: "Textures not loading"

**Solution:** Check:
1. Texture paths are relative (`../../Textures/...`)
2. Textures exist at specified paths
3. Variant name matches texture folder name

### Issue: "Assembly too slow to load"

**Solution:**
1. Use payloads for lazy loading (automatically done)
2. Enable instancing for repeated components
3. Use lower resolution variant as default

---

## 📝 License

Part of Custom Houdini Tools collection.

---

## 🤝 Contributing

Improvements welcome! Areas for enhancement:
- LOD (Level of Detail) support
- Animation/rigging integration
- Procedural variant generation
- Automatic thumbnail generation
- Schema validation

---

## 📞 Support

For issues or questions:
1. Check examples in `examples/kb3d_usd_builder_examples.py`
2. Review this documentation
3. Examine KB3D source files for patterns

---

## 🔍 Advanced Topics

### Creating geo.usd from Houdini

The system expects you to provide `geo.usd` files. Here's how to create them in Houdini:

#### Method 1: USD ROP

```python
# In Houdini LOP context:
1. Build geometry in SOPs
2. Import to LOPs with SOP Import
3. Assign materials
4. Use USD ROP to export geo.usd
```

#### Method 2: Python Script

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("geo.usd")
# Add your geometry here
stage.GetRootLayer().Save()
```

### Custom Metadata

Add custom metadata beyond KB3D standard:

```python
metadata = KB3DMetadata("my_kit", "My Kit", "1.0.0")
# Extend in your code as needed
```

### Variant Inheritance Patterns

Understanding how variants cascade:

```
Assembly.texture_variant = "png4k"
    ↓ (variant edit context)
    Component.texture_variant = "png4k"
        ↓ (variant edit context)
        Material.texture_variant = "png4k"
            ↓ (overrides)
            Texture paths → png4k folder
```

---

**Version:** 1.0.0
**Last Updated:** 2025
**Based on:** KitBash3D Mission to Minerva (v6.1.1)
