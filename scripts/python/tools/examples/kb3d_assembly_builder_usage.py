"""
KB3DAssemblyBuilder - Complete Usage Guide

This script shows all the ways to use KB3DAssemblyBuilder to create
KB3D-style assemblies that reference multiple components.
"""

import hou
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from kb3d_usd_structure_builder import KB3DAssemblyBuilder


# =============================================================================
# BASIC USAGE
# =============================================================================

def basic_usage():
    """Most simple usage - create assembly with a few components"""

    print("\n" + "="*70)
    print("BASIC USAGE - Simple Assembly")
    print("="*70 + "\n")

    # Step 1: Create the builder
    assembly_name = "MySpaceStation"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Step 2: Add components (these must exist as sibling folders)
    builder.add_component("KB3D_MTM_PropSolarPanel_A")
    builder.add_component("KB3D_MTM_PropRaisedModules_A")
    builder.add_component("KB3D_MTM_Equip3DPrinter_A")

    # Step 3: Build the assembly
    result_path = builder.build()

    print(f"✓ Assembly created at: {result_path}")
    print(f"✓ Components added: {len(builder.components)}")

    return result_path


# =============================================================================
# WITH TRANSFORMS
# =============================================================================

def with_transforms():
    """Add components with specific positions, rotations, scales"""

    print("\n" + "="*70)
    print("WITH TRANSFORMS - Positioned Components")
    print("="*70 + "\n")

    assembly_name = "PositionedStation"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Add component with transform
    builder.add_component(
        component_name="KB3D_MTM_PropSolarPanel_A",
        transform={
            "translate": [10.5, 0, 5.2],    # X, Y, Z position
            "rotate": [0, 45, 0],            # X, Y, Z rotation in degrees
            "scale": [1, 1, 1]               # X, Y, Z scale
        },
        variant="png2k"                      # Texture resolution variant
    )

    # Add another component at different position
    builder.add_component(
        component_name="KB3D_MTM_PropRaisedModules_A",
        transform={
            "translate": [-8.3, 0, 0],
            "rotate": [0, -90, 0],
            "scale": [1.5, 1, 1.5]          # Scaled up 1.5x
        },
        variant="png2k"
    )

    # Add foreground component with higher res textures
    builder.add_component(
        component_name="KB3D_MTM_Equip3DPrinter_A",
        transform={
            "translate": [0, 0, -12.7],
            "rotate": [0, 0, 0],
            "scale": [1, 1, 1]
        },
        variant="png4k"  # Higher resolution for close-up
    )

    result_path = builder.build()

    print(f"✓ Assembly with transforms created: {result_path}")
    print(f"\nComponent positions:")
    for i, comp in enumerate(builder.components):
        print(f"  {i+1}. {comp['name']}")
        print(f"     Position: {comp['transform']['translate']}")
        print(f"     Rotation: {comp['transform']['rotate']}")
        print(f"     Variant: {comp['variant']}")

    return result_path


# =============================================================================
# FROM EXISTING KB3D ASSETS
# =============================================================================

def from_real_kb3d_assets():
    """Build assembly using actual KB3D Mission to Minerva assets"""

    print("\n" + "="*70)
    print("FROM REAL KB3D ASSETS - Mission to Minerva")
    print("="*70 + "\n")

    assembly_name = "KB3D_MTM_CustomAssembly_A"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # These component names come from the actual KB3D Mission to Minerva library
    components_to_add = [
        ("KB3D_MTM_BldgLgCommsArray_A", [0, 0, 0], [0, 0, 0]),
        ("KB3D_MTM_PropSolarPanel_A", [20, 0, 0], [0, 0, 0]),
        ("KB3D_MTM_PropSolarPanel_A", [-20, 0, 0], [0, 180, 0]),
        ("KB3D_MTM_Equip3DPrinter_A", [0, 0, 15], [0, 90, 0]),
    ]

    for comp_name, translate, rotate in components_to_add:
        builder.add_component(
            component_name=comp_name,
            transform={
                "translate": translate,
                "rotate": rotate,
                "scale": [1, 1, 1]
            },
            variant="png2k"
        )

    result_path = builder.build()

    print(f"✓ KB3D assembly created: {result_path}")
    print(f"✓ Using {len(builder.components)} real KB3D components")

    return result_path


# =============================================================================
# BATCH - MULTIPLE COMPONENTS
# =============================================================================

def batch_add_components():
    """Add many components in a loop"""

    print("\n" + "="*70)
    print("BATCH ADD - Multiple Components in Loop")
    print("="*70 + "\n")

    assembly_name = "SolarPanelArray"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Create a grid of solar panels
    spacing = 5.0
    grid_size = 5  # 5x5 grid = 25 panels

    for x in range(grid_size):
        for z in range(grid_size):
            # Calculate position
            pos_x = (x - grid_size/2) * spacing
            pos_z = (z - grid_size/2) * spacing

            # Vary rotation slightly
            rotation_y = (x + z) * 15  # Different angle for each

            # Use lower res for background, higher for center
            distance_from_center = abs(pos_x) + abs(pos_z)
            if distance_from_center < spacing:
                variant = "png4k"  # Center
            elif distance_from_center < spacing * 2:
                variant = "png2k"  # Middle
            else:
                variant = "png1k"  # Outer

            builder.add_component(
                component_name="KB3D_MTM_PropSolarPanel_A",
                transform={
                    "translate": [pos_x, 0, pos_z],
                    "rotate": [0, rotation_y, 0],
                    "scale": [1, 1, 1]
                },
                variant=variant
            )

    result_path = builder.build()

    print(f"✓ Solar panel array created: {result_path}")
    print(f"✓ Total panels: {len(builder.components)}")
    print(f"✓ Grid size: {grid_size}x{grid_size}")

    return result_path


# =============================================================================
# FROM CSV DATA
# =============================================================================

def from_csv_data():
    """Build assembly from CSV file or spreadsheet data"""

    print("\n" + "="*70)
    print("FROM CSV - Spreadsheet Layout Data")
    print("="*70 + "\n")

    import csv
    from io import StringIO

    # This could be loaded from a real CSV file
    # In production: with open('layout.csv', 'r') as f:
    csv_data = """component_name,tx,ty,tz,rx,ry,rz,sx,sy,sz,variant
KB3D_MTM_PropSolarPanel_A,10.5,0,5.2,0,45,0,1,1,1,png2k
KB3D_MTM_PropRaisedModules_A,-8.3,0,0,0,-90,0,1.5,1,1.5,png2k
KB3D_MTM_Equip3DPrinter_A,0,0,-12.7,0,0,0,1,1,1,png4k
KB3D_MTM_PropSolarPanel_A,15.0,0,10.0,0,90,0,1,1,1,png1k
KB3D_MTM_PropSolarPanel_A,-15.0,0,10.0,0,-45,0,1,1,1,png1k"""

    assembly_name = "CSV_LayoutAssembly"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Parse CSV and add components
    reader = csv.DictReader(StringIO(csv_data))

    for row in reader:
        builder.add_component(
            component_name=row["component_name"],
            transform={
                "translate": [float(row["tx"]), float(row["ty"]), float(row["tz"])],
                "rotate": [float(row["rx"]), float(row["ry"]), float(row["rz"])],
                "scale": [float(row["sx"]), float(row["sy"]), float(row["sz"])]
            },
            variant=row["variant"]
        )

    result_path = builder.build()

    print(f"✓ Assembly from CSV created: {result_path}")
    print(f"✓ Components loaded from spreadsheet: {len(builder.components)}")

    # Show what was loaded
    print("\nComponents loaded:")
    for i, comp in enumerate(builder.components, 1):
        print(f"  {i}. {comp['name']} at {comp['transform']['translate']}")

    return result_path


# =============================================================================
# FROM JSON CONFIG
# =============================================================================

def from_json_config():
    """Build assembly from JSON configuration file"""

    print("\n" + "="*70)
    print("FROM JSON - Configuration File")
    print("="*70 + "\n")

    import json

    # This could be loaded from a real JSON file
    # In production: with open('assembly_config.json', 'r') as f:
    config = {
        "assembly_name": "JSON_ConfiguredStation",
        "output_dir": "$HIP/usd_library",
        "components": [
            {
                "name": "KB3D_MTM_PropSolarPanel_A",
                "transform": {
                    "translate": [10, 0, 0],
                    "rotate": [0, 0, 0],
                    "scale": [1, 1, 1]
                },
                "variant": "png2k"
            },
            {
                "name": "KB3D_MTM_PropRaisedModules_A",
                "transform": {
                    "translate": [-10, 0, 0],
                    "rotate": [0, 180, 0],
                    "scale": [1, 1, 1]
                },
                "variant": "png2k"
            }
        ]
    }

    # Build from config
    assembly_name = config["assembly_name"]
    output_dir = hou.expandString(config["output_dir"])

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    for comp_config in config["components"]:
        builder.add_component(
            component_name=comp_config["name"],
            transform=comp_config["transform"],
            variant=comp_config["variant"]
        )

    result_path = builder.build()

    print(f"✓ Assembly from JSON created: {result_path}")
    print(f"✓ Configuration: {assembly_name}")

    return result_path


# =============================================================================
# PROGRAMMATIC - CALCULATED POSITIONS
# =============================================================================

def programmatic_layout():
    """Generate assembly layout programmatically (circle, spiral, etc.)"""

    print("\n" + "="*70)
    print("PROGRAMMATIC - Calculated Layout (Circle)")
    print("="*70 + "\n")

    import math

    assembly_name = "CircularStation"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Arrange components in a circle
    num_components = 8
    radius = 15.0

    for i in range(num_components):
        angle = (i / num_components) * 2 * math.pi

        # Calculate position on circle
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius

        # Rotate to face center
        rotation_y = math.degrees(angle) + 90

        builder.add_component(
            component_name="KB3D_MTM_PropSolarPanel_A",
            transform={
                "translate": [x, 0, z],
                "rotate": [0, rotation_y, 0],
                "scale": [1, 1, 1]
            },
            variant="png2k"
        )

    # Add center piece
    builder.add_component(
        component_name="KB3D_MTM_Equip3DPrinter_A",
        transform={
            "translate": [0, 0, 0],
            "rotate": [0, 0, 0],
            "scale": [2, 2, 2]  # Larger center
        },
        variant="png4k"
    )

    result_path = builder.build()

    print(f"✓ Circular assembly created: {result_path}")
    print(f"✓ Solar panels arranged in circle: {num_components}")
    print(f"✓ Radius: {radius} units")

    return result_path


# =============================================================================
# INSPECT ASSEMBLY
# =============================================================================

def inspect_assembly(builder):
    """Inspect what's inside an assembly before building"""

    print("\n" + "="*70)
    print("INSPECT ASSEMBLY - Before Building")
    print("="*70 + "\n")

    print(f"Assembly Name: {builder.assembly_name}")
    print(f"Output Directory: {builder.output_dir}")
    print(f"Output Path: {builder.main_usd}")
    print(f"\nComponents ({len(builder.components)}):")

    for i, comp in enumerate(builder.components, 1):
        print(f"\n  {i}. {comp['name']}")
        print(f"     Position: {comp['transform']['translate']}")
        print(f"     Rotation: {comp['transform']['rotate']}")
        print(f"     Scale: {comp['transform']['scale']}")
        print(f"     Variant: {comp['variant']}")

    print(f"\nAvailable texture variants:")
    for variant in builder.variants:
        print(f"  - {variant}")


# =============================================================================
# HELPER FUNCTION - LOAD FROM FILE
# =============================================================================

def load_assembly_from_file(filepath):
    """Helper: Load assembly configuration from external file"""

    import json

    with open(filepath, 'r') as f:
        config = json.load(f)

    builder = KB3DAssemblyBuilder(
        config["assembly_name"],
        hou.expandString(config["output_dir"])
    )

    for comp in config["components"]:
        builder.add_component(
            comp["name"],
            comp.get("transform"),
            comp.get("variant", "png2k")
        )

    return builder


# =============================================================================
# MAIN - RUN EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("KB3D ASSEMBLY BUILDER - USAGE EXAMPLES")
    print("="*70)

    # Choose which example to run:
    # Uncomment the one you want to try

    # Example 1: Basic usage
    # basic_usage()

    # Example 2: With transforms
    # with_transforms()

    # Example 3: From real KB3D assets
    # from_real_kb3d_assets()

    # Example 4: Batch add components
    batch_add_components()

    # Example 5: From CSV data
    # from_csv_data()

    # Example 6: From JSON config
    # from_json_config()

    # Example 7: Programmatic layout
    # programmatic_layout()

    print("\n" + "="*70)
    print("DONE! Check the output in $HIP/usd_library/Models/")
    print("="*70 + "\n")


# =============================================================================
# QUICK REFERENCE
# =============================================================================

"""
QUICK REFERENCE - Copy/Paste Templates
=======================================

1. MINIMAL EXAMPLE:
-------------------
from kb3d_usd_structure_builder import KB3DAssemblyBuilder

builder = KB3DAssemblyBuilder("MyAssembly", "$HIP/usd_library")
builder.add_component("ComponentA")
builder.add_component("ComponentB")
result = builder.build()


2. WITH POSITION:
-----------------
builder.add_component(
    "ComponentName",
    transform={"translate": [10, 0, 5], "rotate": [0, 45, 0], "scale": [1, 1, 1]},
    variant="png2k"
)


3. BATCH ADD:
-------------
components = [
    ("CompA", [0, 0, 0], [0, 0, 0]),
    ("CompB", [10, 0, 0], [0, 90, 0]),
]

for name, pos, rot in components:
    builder.add_component(
        name,
        transform={"translate": pos, "rotate": rot, "scale": [1, 1, 1]},
        variant="png2k"
    )


4. INSPECT BEFORE BUILD:
------------------------
print(f"Components: {len(builder.components)}")
for comp in builder.components:
    print(comp["name"], comp["transform"]["translate"])


5. ALL TEXTURE VARIANTS:
------------------------
png1k, png2k, png4k  - PNG format at 1k, 2k, 4k resolution
jpg1k, jpg2k, jpg4k  - JPG format at 1k, 2k, 4k resolution
"""
