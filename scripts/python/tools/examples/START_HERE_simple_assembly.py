"""
START HERE - Simple Assembly Builder

This is the simplest possible example to get started.
Just run this script in Houdini and it will create an assembly.
"""

import hou
import sys
import os

# Add the tools directory to Python path
tools_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, tools_dir)

from kb3d_usd_structure_builder import KB3DAssemblyBuilder


def simple_example():
    """
    Simplest possible example - create assembly from KB3D components
    """

    print("\n" + "="*70)
    print("SIMPLE ASSEMBLY BUILDER - Getting Started")
    print("="*70 + "\n")

    # STEP 1: Define where to save
    # This will create: $HIP/usd_library/Models/MyFirstAssembly/
    output_directory = hou.expandString("$HIP/usd_library")

    # STEP 2: Create the builder
    assembly_name = "MyFirstAssembly"
    builder = KB3DAssemblyBuilder(assembly_name, output_directory)

    print(f"Creating assembly: {assembly_name}")
    print(f"Output location: {output_directory}\n")

    # STEP 3: Add components
    # These are actual KB3D Mission to Minerva components
    # Replace with your own component names if needed

    print("Adding components...")

    # Component 1: Center building
    builder.add_component(
        component_name="KB3D_MTM_BldgLgCommsArray_A",
        transform={
            "translate": [0, 0, 0],      # Center position
            "rotate": [0, 0, 0],          # No rotation
            "scale": [1, 1, 1]            # Normal size
        },
        variant="png2k"                   # Medium resolution
    )
    print("  ✓ Added: KB3D_MTM_BldgLgCommsArray_A (center)")

    # Component 2: Solar panel on right
    builder.add_component(
        component_name="KB3D_MTM_PropSolarPanel_A",
        transform={
            "translate": [25, 0, 0],      # 25 units to the right
            "rotate": [0, 0, 0],
            "scale": [1, 1, 1]
        },
        variant="png2k"
    )
    print("  ✓ Added: KB3D_MTM_PropSolarPanel_A (right)")

    # Component 3: Solar panel on left (mirrored)
    builder.add_component(
        component_name="KB3D_MTM_PropSolarPanel_A",
        transform={
            "translate": [-25, 0, 0],     # 25 units to the left
            "rotate": [0, 180, 0],         # Flipped 180 degrees
            "scale": [1, 1, 1]
        },
        variant="png2k"
    )
    print("  ✓ Added: KB3D_MTM_PropSolarPanel_A (left, flipped)")

    # Component 4: Equipment in front
    builder.add_component(
        component_name="KB3D_MTM_Equip3DPrinter_A",
        transform={
            "translate": [0, 0, 20],      # 20 units forward
            "rotate": [0, 45, 0],          # Rotated 45 degrees
            "scale": [1, 1, 1]
        },
        variant="png4k"                    # High resolution (foreground)
    )
    print("  ✓ Added: KB3D_MTM_Equip3DPrinter_A (front, high-res)")

    # STEP 4: Build the assembly
    print("\nBuilding USD files...")
    result_path = builder.build()

    # STEP 5: Done!
    print("\n" + "="*70)
    print("SUCCESS!")
    print("="*70)
    print(f"\nAssembly created at:")
    print(f"  {result_path}")
    print(f"\nTotal components: {len(builder.components)}")
    print(f"\nFiles created:")
    print(f"  - {assembly_name}.usd (main file)")
    print(f"  - payload.usd (component references)")
    print(f"  - mtl.usd (materials)")

    print("\n" + "="*70)
    print("NEXT STEPS:")
    print("="*70)
    print("\n1. Open the Scene View")
    print("2. Create a Reference LOP node")
    print("3. Point it to the USD file above")
    print("4. View your assembly!\n")

    print("OR in LOPs:")
    print(f'  reference_node.parm("filepath").set("{result_path}")\n')

    return result_path


def load_in_lops():
    """
    Bonus: Automatically load the created assembly into LOPs
    """

    # First create the assembly
    assembly_path = simple_example()

    print("\n" + "="*70)
    print("BONUS: Loading into LOPs")
    print("="*70 + "\n")

    # Get or create stage
    stage = hou.node("/stage")
    if not stage:
        obj = hou.node("/obj")
        stage = obj.createNode("stage", "stage")
        print("Created /stage context")

    # Create reference node
    ref_node = stage.createNode("reference", "MyFirstAssembly_ref")
    ref_node.parm("filepath").set(assembly_path)

    print(f"✓ Created Reference LOP: {ref_node.path()}")
    print(f"✓ Loaded assembly into scene")

    # Layout nodes nicely
    stage.layoutChildren()

    # Set display flag
    ref_node.setDisplayFlag(True)

    print("\n✓ Assembly is now visible in Scene Viewer!")

    return ref_node


# =============================================================================
# RUN IT!
# =============================================================================

if __name__ == "__main__":
    # Choose one:

    # Option 1: Just build the USD files
    simple_example()

    # Option 2: Build AND load into LOPs automatically
    # load_in_lops()


# =============================================================================
# CUSTOMIZE IT
# =============================================================================

"""
Want to customize? Change these values above:

1. ASSEMBLY NAME:
   assembly_name = "MySpaceStation"

2. OUTPUT LOCATION:
   output_directory = "/path/to/my/library"

3. COMPONENTS:
   Replace component names with your own:
   builder.add_component("MyComponent", ...)

4. POSITIONS:
   Change translate values:
   "translate": [X, Y, Z]  # X=left/right, Y=up/down, Z=forward/back

5. ROTATIONS:
   Change rotate values:
   "rotate": [X, Y, Z]  # Degrees

6. TEXTURE QUALITY:
   variant="png1k"  # Low-res (background)
   variant="png2k"  # Medium-res (default)
   variant="png4k"  # High-res (foreground)
"""
