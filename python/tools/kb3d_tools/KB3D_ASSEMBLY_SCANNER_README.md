# KB3D Assembly Scanner & Reconstructor

A comprehensive Python system for **scanning**, **analyzing**, and **reconstructing** KitBash3D-style USD assemblies from decomposed source parts.

## 🎯 Problem Statement

When working with KitBash3D assets or similar USD assemblies, you often have:
- **Source parts**: 84+ individual component folders (from FBX/BGEO decomposition)
- **Production assembly**: Optimized USD file that references and positions these parts

**The Challenge**: How do you reconstruct the production assembly from source parts while preserving:
- ✅ Transform data (position, rotation, scale)
- ✅ Instance relationships
- ✅ Group organization
- ✅ Material assignments
- ✅ Variant systems

**This tool solves that problem!**

---

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Workflow Overview](#workflow-overview)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Use Cases](#use-cases)
- [Troubleshooting](#troubleshooting)

---

## ✨ Features

### 🔍 Source Parts Scanner
- Catalogs all source part folders
- Extracts metadata (extents, materials, thumbnails)
- Identifies available components
- Generates JSON catalog for reference

### 📊 Production Assembly Scanner
- Extracts complete instance hierarchy
- Captures transform data (translate/rotate/scale)
- Identifies group organization
- Extracts variant configurations
- Preserves instanceable flags
- Saves mapping as JSON

### 🏗️ Assembly Reconstructor
- Rebuilds assemblies from source parts
- Applies extracted transforms
- Recreates group hierarchy
- Maintains instancing optimization
- Supports relative path references

### 📈 Analysis Tools
- Compares source parts vs production instances
- Identifies missing mappings
- Analyzes transform coverage
- Validates reconstruction accuracy

---

## 📦 Installation

### Prerequisites

```bash
# Using Houdini Python (recommended)
/opt/hfs21.0/bin/hython

# OR standalone USD Python
pip install usd-core
```

### Setup

```python
import sys
sys.path.append('/path/to/custom_tools/scripts/python/tools/kb3d_tools')

from kb3d_assembly_scanner import (
    KB3DAssemblyScanner,
    KB3DSourcePartScanner,
    KB3DAssemblyReconstructor
)
```

---

## 🚀 Quick Start

### Step 1: Scan Source Parts

```python
from pathlib import Path
from kb3d_assembly_scanner import KB3DSourcePartScanner

# Define source parts directory
source_dir = Path("/path/to/source/parts/KB3D_MTM_BldgLgCommsArray_A")

# Create scanner
scanner = KB3DSourcePartScanner(source_dir)

# Scan and save catalog
parts = scanner.scan()
scanner.save_catalog(Path("parts_catalog.json"))

# Output:
# ✓ Found 84 source parts
# ✓ Saved parts catalog to: parts_catalog.json
```

### Step 2: Scan Production Assembly

```python
from kb3d_assembly_scanner import KB3DAssemblyScanner

# Define production assembly
assembly_path = Path("/path/to/production/KB3D_MTM_BldgLgCommsArray_A.usd")

# Create scanner
scanner = KB3DAssemblyScanner(assembly_path)

# Scan and save mapping
metadata, instances = scanner.scan()
scanner.save_mapping(Path("assembly_mapping.json"))

# Output:
# ✓ Saved mapping to: assembly_mapping.json
#   - Assembly: KB3D_MTM_BldgLgCommsArray_A
#   - Instances: 47
#   - Groups: 3
```

### Step 3: Reconstruct Assembly

```python
from kb3d_assembly_scanner import reconstruct_from_files

# Reconstruct from JSON files
reconstruct_from_files(
    mapping_json=Path("assembly_mapping.json"),
    catalog_json=Path("parts_catalog.json"),
    output_usd=Path("reconstructed_assembly.usd"),
    relative_parts_path="../../source/parts"
)

# Output:
# Reconstructing assembly: KB3D_MTM_BldgLgCommsArray_A
# ✓ Reconstructed assembly saved to: reconstructed_assembly.usd
#   - Instances: 47
#   - Groups: 3
```

---

## 🔄 Workflow Overview

### Complete Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE PARTS                              │
│   84 folders with individual components                     │
│   (from FBX/BGEO decomposition)                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  SOURCE PART SCANNER  │
         │  - Catalogs parts     │
         │  - Extracts metadata  │
         └───────────┬───────────┘
                     │
                     ▼
            ┌────────────────┐
            │ parts_catalog  │
            │     .json      │
            └────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              PRODUCTION ASSEMBLY                             │
│   Single optimized USD with references                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  ASSEMBLY SCANNER     │
         │  - Extracts instances │
         │  - Captures transforms│
         └───────────┬───────────┘
                     │
                     ▼
            ┌────────────────────┐
            │ assembly_mapping   │
            │       .json        │
            └────────────────────┘

         ┌───────────────────────┐
         │    RECONSTRUCTOR      │
         │  - Matches parts      │
         │  - Applies transforms │
         │  - Rebuilds hierarchy │
         └───────────┬───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           RECONSTRUCTED ASSEMBLY                             │
│   New USD built from source parts                           │
│   with production transforms                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 API Reference

### KB3DSourcePartScanner

Scans directories containing source part folders.

```python
class KB3DSourcePartScanner:
    def __init__(self, source_parts_dir: Path)

    def scan(self) -> Dict[str, Dict]
        """
        Scan directory for part folders

        Returns:
            Dict mapping part name to part info:
            {
                'part_name': {
                    'usd_path': str,
                    'folder': str,
                    'has_payload': bool,
                    'has_geo': bool,
                    'has_mtl': bool,
                    'has_thumbnail': bool,
                    'extent': {'min': tuple, 'max': tuple}
                }
            }
        """

    def save_catalog(self, output_path: Path)
        """Save parts catalog to JSON"""
```

**Example Output (JSON)**:
```json
{
  "1LPlatform": {
    "usd_path": "/path/to/KB3D_MTM_BldgLgCommsArray_A_1LPlatform.usd",
    "folder": "/path/to/KB3D_MTM_BldgLgCommsArray_A_1LPlatform",
    "has_payload": true,
    "has_geo": true,
    "has_mtl": true,
    "has_thumbnail": true,
    "extent": {
      "min": [-23.16, 0.001, 40.20],
      "max": [23.16, 5.50, 45.30]
    }
  }
}
```

---

### KB3DAssemblyScanner

Scans production assemblies to extract instance data.

```python
class KB3DAssemblyScanner:
    def __init__(self, production_assembly_path: Path)

    def scan(self) -> Tuple[AssemblyMetadata, List[InstanceData]]
        """
        Scan assembly and extract all data

        Returns:
            Tuple of (AssemblyMetadata, List[InstanceData])
        """

    def save_mapping(self, output_path: Path)
        """Save extracted data to JSON mapping file"""
```

**AssemblyMetadata**:
```python
@dataclass
class AssemblyMetadata:
    assembly_name: str
    extent_hint: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]
    default_variant: str
    total_instances: int
    groups: List[str]
```

**InstanceData**:
```python
@dataclass
class InstanceData:
    instance_name: str
    source_part_name: str
    referenced_model_path: Optional[str]
    transform: Optional[TransformData]
    instanceable: bool
    group_name: Optional[str]
    kind: str
```

**TransformData**:
```python
@dataclass
class TransformData:
    translate: Optional[Tuple[float, float, float]]
    rotate: Optional[Tuple[float, float, float]]
    scale: Optional[Tuple[float, float, float]]
    rotate_order: str  # "XYZ", "XZY", etc.
```

**Example Output (JSON)**:
```json
{
  "metadata": {
    "assembly_name": "KB3D_MTM_BldgLgCommsArray_A",
    "extent_hint": [[-79.93, 0.001, -31.27], [167.51, 55.90, 48.94]],
    "default_variant": "png4k",
    "total_instances": 47,
    "groups": ["Foundation", "Walls", "Props"]
  },
  "instances": [
    {
      "instance_name": "KB3D_MTM_BldgLgCommsArray_A_1LPlatform_001",
      "source_part_name": "1LPlatform",
      "referenced_model_path": "../KB3D_MTM_PropRaisedModules_A_1LPlatform/KB3D_MTM_PropRaisedModules_A_1LPlatform.usd",
      "transform": {
        "translate": [-23.16, 0.001, 40.21],
        "rotate": [0, 0, 0],
        "scale": [1, 1, 1]
      },
      "instanceable": true,
      "group_name": "Foundation",
      "kind": "component"
    }
  ]
}
```

---

### KB3DAssemblyReconstructor

Reconstructs assemblies from source parts using mapping data.

```python
class KB3DAssemblyReconstructor:
    def __init__(self, mapping_data: Dict, source_parts_catalog: Dict)

    def reconstruct(self, output_path: Path, relative_parts_path: str = "../../parts")
        """
        Reconstruct assembly USD from mapping data

        Args:
            output_path: Where to save the reconstructed assembly USD
            relative_parts_path: Relative path from assembly to source parts directory
        """
```

---

### Convenience Functions

```python
def scan_assembly(production_assembly_path: Path,
                 output_mapping_path: Optional[Path] = None) -> Tuple[AssemblyMetadata, List[InstanceData]]
    """Quick function to scan assembly and optionally save mapping"""

def scan_source_parts(source_parts_dir: Path,
                     output_catalog_path: Optional[Path] = None) -> Dict
    """Quick function to scan source parts and optionally save catalog"""

def reconstruct_from_files(mapping_json: Path,
                          catalog_json: Path,
                          output_usd: Path,
                          relative_parts_path: str = "../../parts")
    """Quick function to reconstruct assembly from JSON files"""
```

---

## 💡 Examples

### Example 1: Complete Workflow

```python
from pathlib import Path
from kb3d_assembly_scanner import (
    scan_source_parts,
    scan_assembly,
    reconstruct_from_files
)

# Paths
source_dir = Path("/path/to/source/parts")
production_usd = Path("/path/to/production/assembly.usd")
output_dir = Path("/tmp/output")

# Step 1: Scan source parts
parts = scan_source_parts(
    source_dir,
    output_dir / "catalog.json"
)

# Step 2: Scan production assembly
metadata, instances = scan_assembly(
    production_usd,
    output_dir / "mapping.json"
)

# Step 3: Reconstruct
reconstruct_from_files(
    output_dir / "mapping.json",
    output_dir / "catalog.json",
    output_dir / "reconstructed.usd",
    relative_parts_path=str(source_dir)
)
```

### Example 2: Detailed Analysis

```python
from kb3d_assembly_scanner import KB3DAssemblyScanner

scanner = KB3DAssemblyScanner(Path("assembly.usd"))
metadata, instances = scanner.scan()

# Analyze transform coverage
with_translate = [i for i in instances if i.transform and i.transform.translate]
with_rotate = [i for i in instances if i.transform and i.transform.rotate]
with_scale = [i for i in instances if i.transform and i.transform.scale]

print(f"Translation: {len(with_translate)}/{len(instances)}")
print(f"Rotation: {len(with_rotate)}/{len(instances)}")
print(f"Scale: {len(with_scale)}/{len(instances)}")

# Analyze by group
for group_name in metadata.groups:
    group_instances = [i for i in instances if i.group_name == group_name]
    print(f"Group '{group_name}': {len(group_instances)} instances")
```

### Example 3: Custom Reconstruction

```python
import json
from pathlib import Path
from kb3d_assembly_scanner import KB3DAssemblyReconstructor

# Load mapping and catalog
with open("mapping.json") as f:
    mapping = json.load(f)

with open("catalog.json") as f:
    catalog = json.load(f)

# Modify mapping (e.g., filter instances)
filtered_instances = [
    inst for inst in mapping['instances']
    if inst.get('group_name') == 'Foundation'
]
mapping['instances'] = filtered_instances

# Reconstruct with modified data
reconstructor = KB3DAssemblyReconstructor(mapping, catalog)
reconstructor.reconstruct(
    Path("foundation_only.usd"),
    relative_parts_path="/absolute/path/to/parts"
)
```

### Example 4: Command Line Usage

```bash
# Run complete workflow
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py all

# Run individual steps
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py scan-parts
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py scan-assembly
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py reconstruct

# Quick scan
/opt/hfs21.0/bin/hython kb3d_assembly_workflow.py quick
```

---

## 🎯 Use Cases

### 1. **Asset Pipeline Integration**
Automate conversion from FBX/OBJ decomposition to production USD assemblies.

### 2. **Asset Variants**
Create multiple assembly variants from the same source parts with different layouts.

### 3. **Asset Analysis**
Understand how production assemblies are structured before modification.

### 4. **Version Migration**
Update assemblies to new part versions while preserving transforms.

### 5. **Custom Assembly Tools**
Build your own assembly tools using extracted instance data.

### 6. **Educational**
Learn USD composition patterns by analyzing real production assets.

---

## 🔧 Troubleshooting

### Issue: "Source parts not found"

**Solution:**
Check that the source directory contains folders with USD files:
```
source_parts_dir/
├── PartName_001/
│   ├── PartName_001.usd
│   ├── geo.usdc
│   └── mtl.usd
├── PartName_002/
...
```

### Issue: "Unmatched instances"

**Problem:** Production assembly references props not in source parts.

**Solution:**
This is expected! Production assemblies often reference **prop models** (higher-level assemblies) rather than individual source parts. Options:

1. **Accept unmatched instances**: They'll use original reference paths
2. **Scan prop models too**: Include prop model directories in your catalog
3. **Create mapping file**: Manually map prop names to source parts

### Issue: "Transform data missing"

**Problem:** Some instances have no transform data.

**Reason:** Instances at origin (0,0,0) with no rotation/scale may not have explicit transforms.

**Solution:** This is normal. Instances without transforms stay at origin.

### Issue: "Reconstructed assembly looks different"

**Solution:** Check:
1. Material assignments (may need separate material layer)
2. Variant selections (ensure correct texture variant)
3. Payload loading (some data may be in payloads)
4. Path references (verify relative paths are correct)

### Issue: "Large file sizes"

**Problem:** Reconstructed USD is much larger than production.

**Reason:** Production may use binary USDC files; reconstructed uses text USDA.

**Solution:**
```python
# Convert to binary after reconstruction
from pxr import Usd
stage = Usd.Stage.Open("reconstructed.usd")
stage.Export("reconstructed.usdc")  # Binary format
```

---

## 📊 Data Format Reference

### Parts Catalog JSON Structure

```json
{
  "part_name": {
    "usd_path": "string - absolute path to USD file",
    "folder": "string - absolute path to part folder",
    "has_payload": "bool - has payload.usd",
    "has_geo": "bool - has geo.usd/usdc",
    "has_mtl": "bool - has mtl.usd",
    "has_thumbnail": "bool - has .png thumbnail",
    "extent": {
      "min": [float, float, float],
      "max": [float, float, float]
    }
  }
}
```

### Assembly Mapping JSON Structure

```json
{
  "metadata": {
    "assembly_name": "string",
    "extent_hint": [[min_x, min_y, min_z], [max_x, max_y, max_z]],
    "default_variant": "string",
    "total_instances": "int",
    "groups": ["string array of group names"]
  },
  "instances": [
    {
      "instance_name": "string - unique instance identifier",
      "source_part_name": "string - matches catalog key",
      "referenced_model_path": "string - original reference path",
      "transform": {
        "translate": [x, y, z],
        "rotate": [rx, ry, rz],
        "scale": [sx, sy, sz],
        "rotate_order": "XYZ"
      },
      "instanceable": "bool - GPU instancing flag",
      "group_name": "string or null",
      "kind": "string - USD kind (component/assembly/group)"
    }
  ]
}
```

---

## 🚀 Advanced Topics

### Custom Transform Processing

```python
from kb3d_assembly_scanner import KB3DAssemblyScanner

scanner = KB3DAssemblyScanner(Path("assembly.usd"))
metadata, instances = scanner.scan()

# Apply custom transform modifications
for inst in instances:
    if inst.transform and inst.transform.translate:
        # Offset all positions
        t = inst.transform.translate
        inst.transform.translate = (t[0] + 10, t[1], t[2])

# Save modified mapping
scanner.save_mapping(Path("modified_mapping.json"))
```

### Filtering Instances

```python
import json

with open("mapping.json") as f:
    mapping = json.load(f)

# Keep only instances in specific group
mapping['instances'] = [
    inst for inst in mapping['instances']
    if inst.get('group_name') in ['Foundation', 'Walls']
]

with open("filtered_mapping.json", 'w') as f:
    json.dump(mapping, f, indent=2)
```

### Batch Processing

```python
from pathlib import Path
from kb3d_assembly_scanner import scan_assembly, scan_source_parts

# Process multiple assemblies
assemblies = [
    "KB3D_MTM_BldgLgCommsArray_A",
    "KB3D_MTM_BldgMdGreenHouse_A",
    "KB3D_MTM_PropSolarPanel_A"
]

for asm_name in assemblies:
    print(f"Processing {asm_name}...")

    source_dir = Path(f"/source/parts/{asm_name}")
    prod_usd = Path(f"/production/{asm_name}/{asm_name}.usd")

    parts = scan_source_parts(source_dir, Path(f"{asm_name}_catalog.json"))
    metadata, instances = scan_assembly(prod_usd, Path(f"{asm_name}_mapping.json"))

    print(f"  ✓ {len(parts)} parts, {len(instances)} instances")
```

---

## 📝 Best Practices

1. **Always save JSON outputs** - They're your source of truth for reconstruction

2. **Use version control** - Track mapping/catalog JSON files in git

3. **Verify paths** - Check source part paths are accessible before reconstruction

4. **Test small first** - Reconstruct single groups before full assemblies

5. **Document mappings** - Add comments to JSON for complex part relationships

6. **Backup originals** - Keep original production assemblies for reference

7. **Use relative paths** - Makes assemblies relocatable

---

## 🤝 Integration with KB3D USD Builder

This tool works seamlessly with the KB3D USD Builder:

```python
from kb3d_usd_builder import KB3DAssemblyBuilder
from kb3d_assembly_scanner import scan_assembly

# Scan existing assembly
metadata, instances = scan_assembly(Path("existing.usd"))

# Use data to build new assembly with KB3D USD Builder
builder = KB3DAssemblyBuilder("NewAssembly", Path("/output"))

for inst in instances:
    if inst.transform:
        builder.add_component_reference(
            inst.instance_name,
            inst.referenced_model_path,
            transform={
                'translate': inst.transform.translate,
                'rotate': inst.transform.rotate,
                'scale': inst.transform.scale
            },
            group_name=inst.group_name
        )

builder.build()
```

---

**Version:** 1.0.0
**Last Updated:** 2025
**Part of:** KB3D Custom Tools Collection
