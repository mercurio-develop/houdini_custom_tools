# How to Change Geometry Path in Houdini UI
## From /ASSET/geo to /filename/geo

This guide shows you how to modify the geometry primitive path when building USD components in Houdini's UI.

---

## Problem
By default, Houdini imports geometry as `/ASSET/geo`, but you want it to be `/filename/geo` or `/{component_name}/geo`.

---

## Solution 1: Using SOP Import Node (Easiest)

### Step-by-Step

1. **Create SOP Import Node** in `/stage`
   ```
   /stage → Tab → "sopimport" → Enter
   ```

2. **Set the SOP Path**
   - Parameter: **SOP Path**
   - Value: `/obj/geo1/OUT` (your geometry node)

3. **Change the Path Prefix** ← THIS IS KEY!
   - Parameter: **Primitives** section → **Path Prefix**
   - Default: `/ASSET`
   - Change to: `/{your_component_name}` or `/MyComponent`

   Example:
   ```
   Path Prefix: /KB3D_MTM_PropSolarPanel_A
   ```

4. **Result:**
   - Geometry will now be at: `/KB3D_MTM_PropSolarPanel_A/geo`
   - Instead of: `/ASSET/geo`

---

## Solution 2: Using Configure Primitive Node

If you already imported with `/ASSET/geo` and want to change it:

1. **Create Configure Primitive Node**
   ```
   /stage → Tab → "configureprimitive" → Enter
   ```

2. **Set Parameters:**
   - **Primitive Path**: `/ASSET` (the old path)
   - **Primitives** tab → **Name**: Type the new name (e.g., `MyComponent`)

3. **Result:**
   - Renames `/ASSET` to `/MyComponent`
   - Geometry becomes `/MyComponent/geo`

---

## Solution 3: Using Edit Primitive Node (Rename)

1. **Create Edit Node**
   ```
   /stage → Tab → "edit" → Enter
   ```

2. **Set Parameters:**
   - **Primitives**: `/ASSET`
   - **Edit** section → **New Path**: `/NewName`

3. **Result:**
   - Renames entire prim tree
   - `/ASSET/geo` becomes `/NewName/geo`

---

## Solution 4: Using Python LOP Node (Advanced)

For dynamic/automated path changes:

1. **Create Python LOP Node**
   ```
   /stage → Tab → "pythonscript" → Enter
   ```

2. **Paste this code:**
   ```python
   stage = hou.pwd().editableStage()

   # Old path
   old_prim = stage.GetPrimAtPath("/ASSET")

   # New name (can be parameter)
   component_name = "MyComponent"
   new_path = f"/{component_name}"

   # Rename
   if old_prim:
       old_prim.SetName(component_name)
   ```

3. **Make it flexible with parameter:**
   - Add parameter: `component_name` (string)
   - Update code:
     ```python
     component_name = hou.pwd().parm("component_name").eval()
     ```

---

## Complete Workflow Example

### Building Component with Custom Geo Path

**Step 1: Import Geometry**
```
[sopimport]
  ├─ SOP Path: /obj/geo1/box1
  └─ Path Prefix: /KB3D_MTM_PropSolarPanel_A  ← Set your component name here
```

**Step 2: Configure as Component**
```
[configure_prim]
  ├─ Primitive Path: /KB3D_MTM_PropSolarPanel_A
  ├─ Set Kind: component
  └─ Set Instanceable: ON
```

**Step 3: Verify Geometry Path**
- Open Scene Graph Tree (right panel)
- Should see:
  ```
  /KB3D_MTM_PropSolarPanel_A
    └─ geo
       └─ [your geometry]
  ```

---

## Using Expression for Dynamic Naming

### In SOP Import "Path Prefix" parameter:

**Option 1: From filename**
```python
"/{}".format(hou.hipFile().basename().split('.')[0])
```
Result: If file is `MyComponent.hip` → `/MyComponent`

**Option 2: From variable**
```python
"/{}".format(hou.getenv("COMPONENT_NAME", "DefaultComponent"))
```
Set environment variable first:
```python
hou.putenv("COMPONENT_NAME", "KB3D_MTM_PropSolarPanel_A")
```

**Option 3: From upstream parameter**
- Add string parameter to parent node: `component_name`
- In Path Prefix:
  ```python
  "/{}`".format(hou.pwd().parent().parm("component_name").eval())
  ```

---

## Template Setup (Reusable)

### Create a Reusable HDA with Flexible Geo Path

1. **Create LOP Network:**
   ```
   /stage/
     ├─ [sopimport] path_prefix: `chs("../component_name")`
     ├─ [configure]
     └─ [output]
   ```

2. **Add Parameter Interface:**
   - String parameter: `component_name`
   - Default: `MyComponent`

3. **Save as Digital Asset:**
   - Right-click network box
   - "Create Digital Asset"
   - Name: `kb3d_component_builder`

4. **Use it:**
   - Create instance
   - Set `component_name` parameter
   - Geo path automatically becomes `/{component_name}/geo`

---

## Quick Reference Table

| Method | When to Use | Difficulty |
|--------|-------------|------------|
| **SOP Import Path Prefix** | Starting fresh | ⭐ Easy |
| **Configure Primitive** | Already imported | ⭐⭐ Medium |
| **Edit Node** | Need to rename | ⭐⭐ Medium |
| **Python LOP** | Automation | ⭐⭐⭐ Advanced |

---

## Common Path Patterns

```
Houdini Default:    /ASSET/geo
KB3D Style:         /ComponentName/geo
Custom:             /geometry/main
Nested:             /assets/ComponentName/geo
Simple:             /geo
```

---

## Troubleshooting

### Problem: Geometry still at /ASSET/geo

**Check:**
1. Did you set **Path Prefix** BEFORE importing?
2. If already imported, add Configure/Edit node AFTER import

### Problem: Path has spaces or special characters

**Solution:**
Use only alphanumeric and underscores:
- ✅ `/My_Component/geo`
- ✅ `/KB3D_MTM_Prop_A/geo`
- ❌ `/My Component/geo` (space)
- ❌ `/My-Component/geo` (hyphen can be problematic)

### Problem: Want to batch change multiple components

**Solution:**
Use Python LOP to loop through:
```python
stage = hou.pwd().editableStage()

# Mapping of old to new names
rename_map = {
    "/ASSET": "/Component_A",
    "/ASSET1": "/Component_B"
}

for old_path, new_name in rename_map.items():
    prim = stage.GetPrimAtPath(old_path)
    if prim:
        prim.SetName(new_name.split('/')[-1])
```

---

## Visual UI Guide

### SOP Import Node Interface

```
┌─────────────────────────────────────────┐
│ SOP Import                              │
├─────────────────────────────────────────┤
│ SOP Path: /obj/geo1/OUT                 │
│                                         │
│ ┌─ Primitives ────────────────────────┐│
│ │                                     ││
│ │ Path Prefix: /MyComponent  ← HERE! ││
│ │                                     ││
│ │ Hierarchy: Subdirectory Path       ││
│ └─────────────────────────────────────┘│
│                                         │
│ Import as Reference: OFF                │
└─────────────────────────────────────────┘
```

Result in Scene Graph:
```
Scene Graph Tree:
  /MyComponent          ← Your component name
    └─ geo              ← Geometry group
       ├─ mesh_0
       ├─ mesh_1
       └─ ...
```

---

## Automated Script (Python)

Save this as a shelf tool for quick setup:

```python
import hou

def setup_component_with_custom_geo():
    # Get component name from user
    component_name = hou.ui.readInput(
        "Enter component name:",
        initial_contents="MyComponent"
    )[1]

    if not component_name:
        return

    # Get stage
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Create SOP import with custom path
    sopimport = stage.createNode("sopimport")
    sopimport.parm("pathprefix").set(f"/{component_name}")

    # Configure as component
    configure = stage.createNode("configureprimitive")
    configure.setInput(0, sopimport)
    configure.parm("primpath").set(f"/{component_name}")
    configure.parm("kind").set("component")

    print(f"✓ Created component: {component_name}")
    print(f"✓ Geo path: /{component_name}/geo")

    stage.layoutChildren()

# Run it
setup_component_with_custom_geo()
```

---

## Next Steps

1. ✅ Set **Path Prefix** in SOP Import to your component name
2. ✅ Verify in Scene Graph Tree that path is correct
3. ✅ Continue with material assignment
4. ✅ Export to USD

The geometry will now be at the correct path throughout your pipeline!
