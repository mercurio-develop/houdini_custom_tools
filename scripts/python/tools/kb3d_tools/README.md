# KB3D USD Tools

**Complete Python toolkit for creating and managing KitBash3D-style USD asset libraries**

Based on analysis of the KitBash3D Mission to Minerva library structure, this toolkit provides production-ready tools for building, scanning, and reconstructing USD assemblies following industry-standard patterns.

---

## 🎯 What's Included

### 1. **KB3D USD Builder** (`kb3d_usd_builder.py`)
Build production-ready USD assets from scratch with materials, components, and assemblies.

**Key Features:**
- MaterialX material creation with texture variants
- Component builder with payload structure
- Assembly builder with instancing
- Full variant system support (jpg/png, 1k/2k/4k)

📖 [Read Full Documentation](KB3D_USD_BUILDER_README.md)

### 2. **KB3D Assembly Scanner** (`kb3d_assembly_scanner.py`)
Scan existing assemblies to extract structure, transforms, and rebuild from source parts.

**Key Features:**
- Extract instance and transform data from production assemblies
- Catalog source part folders
- Reconstruct production assemblies from parts
- Analyze and modify assembly structure

📖 [Read Full Documentation](KB3D_ASSEMBLY_SCANNER_README.md)

### 3. **Complete Workflow Guide**
Step-by-step guide for all workflows: build new assets, reconstruct from parts, analyze existing assets.

📖 [Read Complete Guide](COMPLETE_WORKFLOW_GUIDE.md)

---

## 🚀 Quick Start

### Answer Your Question: Yes, You Can Create Production Assemblies!

Given your source folder structure:
```
/media/tushita/TUSHITA_LINUX_DATA/assets/mission_to_minerva_clone/
└── kb3d_missiontominerva.fbxobj.native/geo/KB3D_MTM_BldgLgCommsArray_A/
    └── KB3D_MTM_BldgLgCommsArray_A/  (84 part folders)
```

You can scan these parts and create a production-ready assembly matching:
```
/media/tushita/TUSHITA_LINUX_DATA/assets/kb3d_missiontominerva/
└── Models/KB3D_MTM_BldgLgCommsArray_A/
    └── KB3D_MTM_BldgLgCommsArray_A.usd
```

**How? Run this:**

```python
from pathlib import Path
from kb3d_assembly_scanner import (
    scan_source_parts,
    scan_assembly,
    reconstruct_from_files
)

# Your paths
SOURCE_PARTS = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                   "mission_to_minerva_clone/kb3d_missiontominerva.fbxobj.native/"
                   "geo/KB3D_MTM_BldgLgCommsArray_A/KB3D_MTM_BldgLgCommsArray_A")

PRODUCTION = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                 "kb3d_missiontominerva/Models/KB3D_MTM_BldgLgCommsArray_A/"
                 "KB3D_MTM_BldgLgCommsArray_A.usd")

OUTPUT_DIR = Path("/tmp/output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Step 1: Scan source parts (catalogs all 84 folders)
parts = scan_source_parts(SOURCE_PARTS, OUTPUT_DIR / "parts_catalog.json")
print(f"✓ Found {len(parts)} source parts")

# Step 2: Scan production assembly (extracts transforms)
metadata, instances = scan_assembly(PRODUCTION, OUTPUT_DIR / "assembly_mapping.json")
print(f"✓ Found {metadata.total_instances} instances in {len(metadata.groups)} groups")

# Step 3: Reconstruct production assembly from source parts
reconstruct_from_files(
    OUTPUT_DIR / "assembly_mapping.json",
    OUTPUT_DIR / "parts_catalog.json",
    OUTPUT_DIR / "RECONSTRUCTED_ASSEMBLY.usd",
    relative_parts_path=str(SOURCE_PARTS)
)
print(f"✓ Reconstructed assembly created!")
```

**Or use the complete workflow script:**

```bash
cd /home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools/examples
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py all
```

---

## 📁 File Structure

```
kb3d_tools/
├── README.md                              # This file
├── KB3D_USD_BUILDER_README.md            # USD Builder documentation
├── KB3D_ASSEMBLY_SCANNER_README.md       # Assembly Scanner documentation
├── COMPLETE_WORKFLOW_GUIDE.md            # Complete workflow guide
│
├── kb3d_usd_builder.py                   # Main USD builder module
├── kb3d_assembly_scanner.py              # Assembly scanner module
│
├── examples/
│   ├── kb3d_usd_builder_examples.py      # 8 builder examples
│   └── kb3d_assembly_workflow.py         # Complete workflow script
│
└── [other kb3d tools...]
```

---

## 🎬 Usage Examples

### Example 1: Create New Material

```python
from kb3d_usd_builder import KB3DMaterialBuilder

mat_builder = KB3DMaterialBuilder("CustomMetal_A", Path("/output/Materials"))

mat_builder.add_texture_map('basecolor', {
    'png1k': '../../Textures/png1k/CustomMetal_A_basecolor.png',
    'png4k': '../../Textures/png4k/CustomMetal_A_basecolor.png',
})

mat_path = mat_builder.build(Path("/output/Materials"))
```

### Example 2: Create New Component

```python
from kb3d_usd_builder import KB3DComponentBuilder

comp_builder = KB3DComponentBuilder("MyComponent_A", Path("/output/Models"))
comp_builder.add_material_reference("CustomMetal_A", "../../Materials/CustomMetal_A/CustomMetal_A.usd")
comp_builder.set_extent_hint((-5, 0, -3), (5, 10, 3))

comp_path = comp_builder.build_main_usd()
```

### Example 3: Create New Assembly

```python
from kb3d_usd_builder import KB3DAssemblyBuilder

asm_builder = KB3DAssemblyBuilder("MyBuilding_A", Path("/output/Models"))

asm_builder.add_component_reference(
    "Component_001",
    "../MyComponent_A/MyComponent_A.usd",
    transform={'translate': (0, 0, 0)},
    instanceable=True
)

asm_path = asm_builder.build()
```

### Example 4: Scan Existing Assembly

```python
from kb3d_assembly_scanner import scan_assembly

metadata, instances = scan_assembly(
    Path("/path/to/assembly.usd"),
    Path("mapping.json")
)

print(f"Assembly: {metadata.assembly_name}")
print(f"Instances: {metadata.total_instances}")
```

### Example 5: Reconstruct from Parts

```python
from kb3d_assembly_scanner import reconstruct_from_files

reconstruct_from_files(
    Path("mapping.json"),
    Path("catalog.json"),
    Path("reconstructed.usd"),
    relative_parts_path="../../source/parts"
)
```

---

## 🎯 Common Workflows

### Workflow A: Build New Assets
**Tools:** KB3D USD Builder
**When:** Creating new assets from scratch

1. Create materials with MaterialX
2. Build components with payload structure
3. Assemble components into buildings
4. Export from Houdini as needed

### Workflow B: Reconstruct from Parts
**Tools:** KB3D Assembly Scanner
**When:** You have source parts and want production assembly

1. Scan source parts folder (84 folders)
2. Scan reference production assembly (for transforms)
3. Reconstruct new assembly from source parts
4. Verify and adjust as needed

### Workflow C: Analyze and Modify
**Tools:** Both tools combined
**When:** Understanding or modifying existing assets

1. Scan assembly to extract structure
2. Modify transform data in JSON
3. Reconstruct with modifications
4. Or use data to build new variants

---

## 🔍 Key Concepts

### USD Structure Pattern

```
Component.usd (main file)
├── [inherits] /__class__/Component
├── [payload] ./payload.usd
│   ├── [reference] ./mtl.usd
│   └── [reference] ./geo.usd
└── [variants] texture_variant
```

### Directory Pattern

```
AssetLibrary/
├── Materials/
│   └── MaterialName/
│       ├── MaterialName.usd
│       └── MaterialName.mtlx
├── Models/
│   ├── ComponentName/
│   │   ├── ComponentName.usd
│   │   ├── payload.usd
│   │   ├── mtl.usd
│   │   └── geo.usd
│   └── AssemblyName/
│       └── AssemblyName.usd
├── Textures/
│   ├── png1k/
│   ├── png4k/
│   └── ...
└── kb3d_metadata.json
```

### Composition Hierarchy

```
Assembly (kind: assembly)
├── Group (kind: group)
│   ├── Component Instance (kind: component, instanceable)
│   └── Component Instance (kind: component, instanceable)
└── Group (kind: group)
    └── Component Instance (kind: component, instanceable)
```

---

## 📊 Feature Comparison

| Feature | USD Builder | Assembly Scanner |
|---------|-------------|------------------|
| Create materials | ✅ | ❌ |
| Create components | ✅ | ❌ |
| Create assemblies | ✅ | ❌ |
| Scan source parts | ❌ | ✅ |
| Extract transforms | ❌ | ✅ |
| Reconstruct assemblies | ❌ | ✅ |
| Analyze structure | ❌ | ✅ |
| MaterialX generation | ✅ | ❌ |
| Texture variants | ✅ | ✅ (extracts) |
| Instancing support | ✅ | ✅ |

---

## 🛠️ Installation

### Prerequisites

```bash
# Using Houdini Python (recommended)
/opt/hfs21.0/bin/hython

# OR standalone USD
pip install usd-core
```

### Add to Python Path

```python
import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_usd_builder import KB3DUSDBuilder
from kb3d_assembly_scanner import KB3DAssemblyScanner
```

---

## 📖 Documentation

- **[KB3D USD Builder Documentation](KB3D_USD_BUILDER_README.md)** - Complete API reference for building USD assets
- **[KB3D Assembly Scanner Documentation](KB3D_ASSEMBLY_SCANNER_README.md)** - Complete API reference for scanning assemblies
- **[Complete Workflow Guide](COMPLETE_WORKFLOW_GUIDE.md)** - Step-by-step workflows for all use cases
- **[Builder Examples](examples/kb3d_usd_builder_examples.py)** - 8 working examples for USD Builder
- **[Scanner Workflow](examples/kb3d_assembly_workflow.py)** - Complete workflow script with command-line interface

---

## 🎓 Learning Resources

### For Beginners
1. Start with [COMPLETE_WORKFLOW_GUIDE.md](COMPLETE_WORKFLOW_GUIDE.md)
2. Run `kb3d_assembly_workflow.py` on your data
3. Examine generated JSON files
4. Try modifying transforms in JSON

### For Advanced Users
1. Read both API documentations
2. Study the example scripts
3. Examine KB3D source files for patterns
4. Build custom pipeline tools

---

## 🤝 Integration

### With Houdini

```python
# In Houdini Python shell
import hou
import sys
sys.path.append('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_usd_builder import KB3DUSDBuilder

# Use builder to create assets
# Export geo.usd from Houdini LOP network
# Build component structure around it
```

### With USD Tools

```bash
# View reconstructed assemblies
usdview reconstructed_assembly.usd

# Check structure
usdcat reconstructed_assembly.usd

# Convert to binary
usdcat -o output.usdc input.usd
```

### With Python Scripts

All tools are pure Python modules - import and use in your pipelines!

---

## ⚡ Performance Tips

1. **Use instancing** - Always set `instanceable=True` for repeated components
2. **Use payloads** - Automatically handled by builder for lazy loading
3. **Choose appropriate variants** - Use `png1k` as default, not `png4k`
4. **Binary formats** - Convert final USD to `.usdc` for smaller files
5. **Relative paths** - Always use relative paths for relocatable assets

---

## 🐛 Troubleshooting

### "Source parts not found"
- Check `SOURCE_PARTS` path points to folder with 84 part folders
- Each part folder should contain `.usd` file

### "Unmatched instances"
- Production assemblies reference prop models, not individual parts
- This is expected - unmatched instances use original reference paths
- See Scanner documentation for mapping strategies

### "Transform data missing"
- Instances at origin may not have explicit transforms
- This is normal USD behavior

### "Assembly looks different"
- Check material assignments
- Verify variant selections
- Ensure geo.usd files are present
- Check relative path references

---

## 📝 License

Part of Custom Houdini Tools collection.

---

## 🎉 Quick Start Command

**To answer your original question directly:**

```bash
# Navigate to examples
cd /home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools/examples

# Run complete workflow on your data
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py all

# This will:
# 1. Scan your 84 source parts
# 2. Extract transforms from production assembly
# 3. Reconstruct production assembly from source parts
# 4. Compare original vs reconstructed
```

**Result:** Production-ready USD assembly built from your source parts! 🎉

---

**Version:** 1.0.0
**Last Updated:** 2025
**Based on:** KitBash3D Mission to Minerva (v6.1.1)
**Tools:** KB3D USD Builder + KB3D Assembly Scanner
