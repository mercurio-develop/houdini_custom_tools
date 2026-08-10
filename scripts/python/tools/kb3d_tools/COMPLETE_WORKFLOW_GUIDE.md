# Complete KB3D USD Workflow Guide

**From Source Parts to Production-Ready USD Assemblies**

This guide walks you through the complete workflow for creating and managing KitBash3D-style USD asset libraries, from scanning decomposed parts to building production assemblies.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [The Complete System](#the-complete-system)
3. [Workflow A: Build New Assets from Scratch](#workflow-a-build-new-assets-from-scratch)
4. [Workflow B: Reconstruct from Existing Parts](#workflow-b-reconstruct-from-existing-parts)
5. [Workflow C: Analyze and Modify Existing Assets](#workflow-c-analyze-and-modify-existing-assets)
6. [Real-World Example: KB3D Mission to Minerva](#real-world-example-kb3d-mission-to-minerva)
7. [Integration with Houdini](#integration-with-houdini)
8. [Tips and Best Practices](#tips-and-best-practices)

---

## 🎯 Overview

### What We Have

Two complementary Python systems for USD asset management:

**1. KB3D USD Builder** (`kb3d_usd_builder.py`)
- Creates new USD assets from scratch
- Builds materials with MaterialX
- Creates components with payload structure
- Assembles components into assemblies
- **Use when**: Building new assets

**2. KB3D Assembly Scanner** (`kb3d_assembly_scanner.py`)
- Scans existing assemblies
- Extracts transform and instance data
- Reconstructs assemblies from source parts
- Analyzes asset structure
- **Use when**: Working with existing assets

### Your Source Data

```
/media/tushita/TUSHITA_LINUX_DATA/assets/
├── mission_to_minerva_clone/
│   └── kb3d_missiontominerva.fbxobj.native/
│       └── geo/KB3D_MTM_BldgLgCommsArray_A/
│           └── KB3D_MTM_BldgLgCommsArray_A/
│               ├── KB3D_MTM_BldgLgCommsArray_A_1LPlatform/
│               ├── KB3D_MTM_BldgLgCommsArray_A_2LPlatform/
│               ├── KB3D_MTM_BldgLgCommsArray_A_SolarPanelA/
│               └── ... (84 parts total)
│
└── kb3d_missiontominerva/
    └── Models/KB3D_MTM_BldgLgCommsArray_A/
        ├── KB3D_MTM_BldgLgCommsArray_A.usd
        ├── payload.usd
        ├── mtl.usd
        └── geo.usd
```

---

## 🔧 The Complete System

### Component Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUR WORKFLOW                             │
└─────────────────────────────────────────────────────────────┘

SOURCE PARTS                    PRODUCTION ASSEMBLY
(84 folders)                    (Single USD file)
     │                                  │
     │                                  │
     ▼                                  ▼
┌──────────────┐              ┌──────────────────┐
│   Scanner    │◄─────────────┤ Assembly Scanner │
│              │   Extract     │                  │
│ Catalogs     │   Transform   │ Scans structure  │
│ Parts        │   Data        │ Extracts data    │
└──────┬───────┘              └────────┬─────────┘
       │                               │
       │  parts_catalog.json           │  assembly_mapping.json
       │                               │
       ▼                               ▼
┌─────────────────────────────────────────────┐
│         RECONSTRUCTOR                       │
│  Matches parts + Applies transforms         │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
         RECONSTRUCTED ASSEMBLY
         (Production-ready USD)

                  │
                  │  OR use as input for:
                  ▼
┌─────────────────────────────────────────────┐
│           USD BUILDER                       │
│  Create new variations/assemblies           │
└─────────────────────────────────────────────┘
```

---

## 🚀 Workflow A: Build New Assets from Scratch

**Use case**: Creating brand new USD assets with materials, components, and assemblies

### Step 1: Set Up Asset Library

```python
from pathlib import Path
from kb3d_usd_builder import KB3DUSDBuilder

# Initialize builder
builder = KB3DUSDBuilder(
    base_path=Path("/my/asset/library"),
    kit_id="my_scifi_kit",
    kit_display_name="My SciFi Assets",
    kit_version="1.0.0"
)

builder.save_metadata()
```

**Created structure:**
```
/my/asset/library/
├── Materials/
├── Models/
├── Textures/
└── kb3d_metadata.json
```

### Step 2: Create Materials

```python
# Create material builder
mat_builder = builder.create_material_builder("Metal_Panel_A")

# Add texture maps
mat_builder.add_texture_map('basecolor', {
    'png1k': '../../Textures/png1k/Metal_Panel_A_basecolor.png',
    'png4k': '../../Textures/png4k/Metal_Panel_A_basecolor.png',
})

mat_builder.add_texture_map('metallic', {
    'png1k': '../../Textures/png1k/Metal_Panel_A_metallic.png',
    'png4k': '../../Textures/png4k/Metal_Panel_A_metallic.png',
})

mat_builder.add_texture_map('roughness', {
    'png1k': '../../Textures/png1k/Metal_Panel_A_roughness.png',
    'png4k': '../../Textures/png4k/Metal_Panel_A_roughness.png',
})

mat_builder.add_texture_map('normal', {
    'png1k': '../../Textures/png1k/Metal_Panel_A_normal.png',
    'png4k': '../../Textures/png4k/Metal_Panel_A_normal.png',
})

# Build material
mat_path = mat_builder.build(builder.materials_dir)
```

### Step 3: Create Components

```python
# Create component (assuming you have geo.usd from Houdini)
comp_builder = builder.create_component_builder("SciFi_Panel_A")

comp_builder.set_extent_hint(
    min_point=(-5.0, 0.0, -3.0),
    max_point=(5.0, 10.0, 3.0)
)

comp_builder.add_material_reference(
    "Metal_Panel_A",
    "../../Materials/Metal_Panel_A/Metal_Panel_A.usd"
)

# Build component structure
comp_path = comp_builder.build_main_usd()

# Copy your geo.usd to the component folder
# cp /path/to/houdini_export/geo.usd /my/asset/library/Models/SciFi_Panel_A/
```

### Step 4: Create Assembly

```python
# Create assembly
asm_builder = builder.create_assembly_builder("SciFi_Building_A")

asm_builder.set_extent_hint(
    min_point=(-50.0, 0.0, -30.0),
    max_point=(50.0, 40.0, 30.0)
)

# Add components with transforms
asm_builder.add_component_reference(
    component_name="Panel_Wall_North",
    component_path="../SciFi_Panel_A/SciFi_Panel_A.usd",
    transform={'translate': (0, 5, 20)},
    group_name="Walls",
    instanceable=True
)

asm_builder.add_component_reference(
    component_name="Panel_Wall_South",
    component_path="../SciFi_Panel_A/SciFi_Panel_A.usd",
    transform={'translate': (0, 5, -20), 'rotate': (0, 180, 0)},
    group_name="Walls",
    instanceable=True
)

# Build assembly
asm_path = asm_builder.build()
```

### Result

```
/my/asset/library/
├── Materials/
│   └── Metal_Panel_A/
│       ├── Metal_Panel_A.usd
│       └── Metal_Panel_A.mtlx
├── Models/
│   ├── SciFi_Panel_A/
│   │   ├── SciFi_Panel_A.usd
│   │   ├── payload.usd
│   │   ├── mtl.usd
│   │   └── geo.usd
│   └── SciFi_Building_A/
│       └── SciFi_Building_A.usd
├── Textures/
│   ├── png1k/
│   └── png4k/
└── kb3d_metadata.json
```

---

## 🔄 Workflow B: Reconstruct from Existing Parts

**Use case**: You have 84 source part folders and want to create production assembly

### Step 1: Scan Source Parts

```python
from pathlib import Path
from kb3d_assembly_scanner import scan_source_parts

source_dir = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                 "mission_to_minerva_clone/kb3d_missiontominerva.fbxobj.native/"
                 "geo/KB3D_MTM_BldgLgCommsArray_A/KB3D_MTM_BldgLgCommsArray_A")

# Scan and save catalog
parts = scan_source_parts(source_dir, Path("parts_catalog.json"))

print(f"Found {len(parts)} source parts")
```

**Output:**
```
✓ Found 84 source parts
✓ Saved parts catalog to: parts_catalog.json
```

### Step 2: Scan Production Assembly (Reference)

```python
from kb3d_assembly_scanner import scan_assembly

production_usd = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                     "kb3d_missiontominerva/Models/KB3D_MTM_BldgLgCommsArray_A/"
                     "KB3D_MTM_BldgLgCommsArray_A.usd")

# Scan production assembly to extract transform data
metadata, instances = scan_assembly(production_usd, Path("assembly_mapping.json"))

print(f"Assembly: {metadata.assembly_name}")
print(f"Instances: {metadata.total_instances}")
print(f"Groups: {len(metadata.groups)}")
```

**Output:**
```
✓ Saved mapping to: assembly_mapping.json
  - Assembly: KB3D_MTM_BldgLgCommsArray_A
  - Instances: 47
  - Groups: 3
```

### Step 3: Reconstruct Assembly

```python
from kb3d_assembly_scanner import reconstruct_from_files

reconstruct_from_files(
    mapping_json=Path("assembly_mapping.json"),
    catalog_json=Path("parts_catalog.json"),
    output_usd=Path("KB3D_MTM_BldgLgCommsArray_A_reconstructed.usd"),
    relative_parts_path=str(source_dir)
)
```

**Output:**
```
Reconstructing assembly: KB3D_MTM_BldgLgCommsArray_A
✓ Reconstructed assembly saved to: KB3D_MTM_BldgLgCommsArray_A_reconstructed.usd
  - Instances: 47
  - Groups: 3
```

### Step 4: Verify Reconstruction

```bash
# View in usdview
usdview KB3D_MTM_BldgLgCommsArray_A_reconstructed.usd

# Or in Houdini
# File > Import > USD
```

---

## 🔍 Workflow C: Analyze and Modify Existing Assets

**Use case**: Understand and modify existing production assemblies

### Step 1: Analyze Assembly Structure

```python
from kb3d_assembly_scanner import KB3DAssemblyScanner

scanner = KB3DAssemblyScanner(Path("existing_assembly.usd"))
metadata, instances = scanner.scan()

# Analyze groups
for group_name in metadata.groups:
    group_instances = [i for i in instances if i.group_name == group_name]
    print(f"Group: {group_name}")
    print(f"  Instances: {len(group_instances)}")

    # Analyze transforms
    with_translate = [i for i in group_instances if i.transform and i.transform.translate]
    with_rotate = [i for i in group_instances if i.transform and i.transform.rotate]

    print(f"  With translation: {len(with_translate)}")
    print(f"  With rotation: {len(with_rotate)}")
```

### Step 2: Extract and Modify Transforms

```python
import json

# Save original mapping
scanner.save_mapping(Path("original_mapping.json"))

# Load and modify
with open("original_mapping.json") as f:
    mapping = json.load(f)

# Example: Offset all positions by +10 on Y axis
for inst in mapping['instances']:
    if inst.get('transform') and inst['transform'].get('translate'):
        t = inst['transform']['translate']
        inst['transform']['translate'] = [t[0], t[1] + 10, t[2]]

# Save modified mapping
with open("modified_mapping.json", 'w') as f:
    json.dump(mapping, f, indent=2)

# Reconstruct with modifications
reconstruct_from_files(
    Path("modified_mapping.json"),
    Path("parts_catalog.json"),
    Path("modified_assembly.usd")
)
```

### Step 3: Create Assembly Variants

```python
# Create "compact" variant - scale everything down
with open("original_mapping.json") as f:
    mapping = json.load(f)

for inst in mapping['instances']:
    if not inst.get('transform'):
        inst['transform'] = {}
    inst['transform']['scale'] = [0.5, 0.5, 0.5]

with open("compact_mapping.json", 'w') as f:
    json.dump(mapping, f, indent=2)

reconstruct_from_files(
    Path("compact_mapping.json"),
    Path("parts_catalog.json"),
    Path("assembly_compact.usd")
)
```

---

## 🎬 Real-World Example: KB3D Mission to Minerva

### Complete Workflow Script

```python
#!/opt/hfs21.0/bin/hython
"""
Reconstruct KB3D Mission to Minerva Building Assembly
"""

from pathlib import Path
from kb3d_assembly_scanner import (
    scan_source_parts,
    scan_assembly,
    reconstruct_from_files
)

# Define paths
BASE = Path("/media/tushita/TUSHITA_LINUX_DATA/assets")

SOURCE_PARTS = BASE / "mission_to_minerva_clone" / \
               "kb3d_missiontominerva.fbxobj.native/geo" / \
               "KB3D_MTM_BldgLgCommsArray_A" / \
               "KB3D_MTM_BldgLgCommsArray_A"

PRODUCTION = BASE / "kb3d_missiontominerva/Models" / \
             "KB3D_MTM_BldgLgCommsArray_A" / \
             "KB3D_MTM_BldgLgCommsArray_A.usd"

OUTPUT_DIR = Path("/tmp/kb3d_reconstruction")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Step 1: Scan source parts
print("Step 1: Scanning source parts...")
parts = scan_source_parts(
    SOURCE_PARTS,
    OUTPUT_DIR / "parts_catalog.json"
)

# Step 2: Scan production assembly
print("\nStep 2: Scanning production assembly...")
metadata, instances = scan_assembly(
    PRODUCTION,
    OUTPUT_DIR / "assembly_mapping.json"
)

# Step 3: Reconstruct
print("\nStep 3: Reconstructing assembly...")
reconstruct_from_files(
    OUTPUT_DIR / "assembly_mapping.json",
    OUTPUT_DIR / "parts_catalog.json",
    OUTPUT_DIR / "KB3D_MTM_BldgLgCommsArray_A_RECONSTRUCTED.usd",
    relative_parts_path=str(SOURCE_PARTS)
)

print("\n✓ Complete!")
print(f"Output: {OUTPUT_DIR / 'KB3D_MTM_BldgLgCommsArray_A_RECONSTRUCTED.usd'}")
print("\nView with:")
print(f"  usdview {OUTPUT_DIR / 'KB3D_MTM_BldgLgCommsArray_A_RECONSTRUCTED.usd'}")
```

### Run the Script

```bash
chmod +x reconstruct_mtm_building.py
/opt/hfs21.0/bin/hython reconstruct_mtm_building.py
```

---

## 🎨 Integration with Houdini

### Method 1: Export Geometry from Houdini

```python
# In Houdini Python shell or LOP network

import hou
from pathlib import Path

# Get LOP node with your geometry
lop_node = hou.node("/stage/lopnet/your_geo_node")

# Export geo.usd
output_path = Path("/path/to/component/folder/geo.usd")
lop_node.stage().Export(str(output_path))

print(f"Exported: {output_path}")
```

### Method 2: Use KB3D Builder in Houdini

```python
# In Houdini Python shell

import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_usd_builder import KB3DUSDBuilder
from pathlib import Path

# Initialize builder
builder = KB3DUSDBuilder(
    Path("/path/to/output"),
    "my_kit",
    "My Assets",
    "1.0.0"
)

# Create component
comp_builder = builder.create_component_builder("HoudiniAsset_A")
comp_builder.add_material_reference("Material_A", "../../Materials/Material_A/Material_A.usd")

# Build structure (then manually copy geo.usd from Houdini export)
comp_builder.build_main_usd()
```

### Method 3: HDA Tool (Shelf Tool)

Create a shelf tool that wraps the workflow:

```python
# HDA Python code
import hou
import sys
from pathlib import Path

sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_assembly_scanner import scan_source_parts, scan_assembly

# Get user input
source_dir = hou.ui.selectFile(title="Select Source Parts Directory")
production_usd = hou.ui.selectFile(title="Select Production Assembly USD")

# Run workflow
if source_dir and production_usd:
    parts = scan_source_parts(Path(source_dir))
    metadata, instances = scan_assembly(Path(production_usd))

    hou.ui.displayMessage(
        f"Scanned:\n"
        f"  Parts: {len(parts)}\n"
        f"  Instances: {len(instances)}\n"
        f"  Groups: {len(metadata.groups)}"
    )
```

---

## 💡 Tips and Best Practices

### 1. **Directory Organization**

```
/my/assets/
├── source/              # Source parts (never modified)
├── production/          # Production assemblies
├── work/               # Work-in-progress
├── mappings/           # JSON mapping files
└── exports/            # Final exports
```

### 2. **Naming Conventions**

Follow KB3D patterns:
- Materials: `KB3D_{KIT}_{MaterialType}`
- Components: `KB3D_{KIT}_{Category}{Type}_{Variant}`
- Assemblies: `KB3D_{KIT}_{Category}{Size}{Type}_{Variant}`

### 3. **Version Control**

Track JSON files in git:
```bash
git add parts_catalog.json
git add assembly_mapping.json
git commit -m "Add assembly mapping for Building_A"
```

### 4. **Validation Checklist**

Before finalizing assemblies:
- ✅ All source parts found
- ✅ Transforms applied correctly
- ✅ Materials load properly
- ✅ Extents calculated
- ✅ Variants work
- ✅ Instancing enabled
- ✅ File paths are relative

### 5. **Performance Optimization**

```python
# Enable instancing
asm_builder.add_component_reference(
    ...,
    instanceable=True  # Critical for repeated components!
)

# Use payloads for lazy loading (automatic in KB3D Builder)

# Use lower-res variants as default
asm_builder.build(default_variant='png1k')  # Not png4k!
```

### 6. **Troubleshooting Workflow**

```python
# If reconstruction fails, analyze the mapping
import json

with open("assembly_mapping.json") as f:
    mapping = json.load(f)

# Check for issues
for inst in mapping['instances']:
    part_name = inst['source_part_name']
    if part_name not in parts_catalog:
        print(f"Missing: {part_name}")

    if not inst.get('transform'):
        print(f"No transform: {inst['instance_name']}")
```

### 7. **Create Assembly Variations**

```python
# Base assembly
base_mapping = "assembly_mapping.json"

# Create "light" version (fewer instances)
with open(base_mapping) as f:
    mapping = json.load(f)

# Keep only "Foundation" group
mapping['instances'] = [
    i for i in mapping['instances']
    if i.get('group_name') == 'Foundation'
]

with open("assembly_light_mapping.json", 'w') as f:
    json.dump(mapping, f, indent=2)

# Reconstruct light version
reconstruct_from_files(
    Path("assembly_light_mapping.json"),
    Path("parts_catalog.json"),
    Path("assembly_light.usd")
)
```

---

## 🎯 Summary

### Quick Reference

| Task | Tool | Command |
|------|------|---------|
| Build new materials | `KB3DUSDBuilder` | `mat_builder.build()` |
| Build new components | `KB3DUSDBuilder` | `comp_builder.build_main_usd()` |
| Build new assemblies | `KB3DUSDBuilder` | `asm_builder.build()` |
| Scan source parts | `KB3DSourcePartScanner` | `scan_source_parts()` |
| Scan assemblies | `KB3DAssemblyScanner` | `scan_assembly()` |
| Reconstruct assemblies | `KB3DAssemblyReconstructor` | `reconstruct_from_files()` |
| Analyze structure | `KB3DAssemblyScanner` | `scanner.scan()` |

### When to Use Which Tool

**Use KB3D USD Builder when:**
- Creating new assets from scratch
- Building material libraries
- Assembling new combinations
- Need fine control over USD structure

**Use KB3D Assembly Scanner when:**
- Working with existing assemblies
- Need to extract transform data
- Want to recreate assemblies from parts
- Analyzing asset structure
- Modifying existing layouts

**Use Both Together when:**
- Migrating assets to new structure
- Creating variants from templates
- Building pipeline tools
- Learning USD patterns

---

## 📚 Further Reading

- `KB3D_USD_BUILDER_README.md` - Detailed USD Builder documentation
- `KB3D_ASSEMBLY_SCANNER_README.md` - Detailed Scanner documentation
- `examples/kb3d_usd_builder_examples.py` - Builder examples
- `examples/kb3d_assembly_workflow.py` - Scanner workflow examples

---

**Ready to start? Run the workflow script!**

```bash
cd /home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools/examples
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py all
```

**Version:** 1.0.0
**Last Updated:** 2025
**Part of:** KB3D Custom Tools Collection
