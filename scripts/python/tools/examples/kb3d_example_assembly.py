"""
Example: Building a KB3D-style assembly in Houdini

This script demonstrates how to create an assembly USD that references multiple components:
- Assembly structure with sibling component references
- Transform placement for each component
- Texture variant management
- Payload pattern for assemblies
"""

import hou
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from kb3d_usd_structure_builder import KB3DAssemblyBuilder, create_assembly_lop_network


def example_1_python_api():
    """Example using pure Python USD API"""
    print("\n=== Example 1: Building Assembly with Python USD API ===\n")

    # Define assembly
    assembly_name = "KB3D_MTM_BldgLgCommsArray_A"
    output_dir = hou.expandString("$HIP/usd_library")

    # Create builder
    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    # Add components with transforms
    components = [
        {
            "name": "KB3D_MTM_PropSolarPanel_A",
            "transform": {
                "translate": [10.5, 0, 5.2],
                "rotate": [0, 45, 0],
                "scale": [1, 1, 1]
            },
            "variant": "png2k"
        },
        {
            "name": "KB3D_MTM_PropRaisedModules_A",
            "transform": {
                "translate": [-8.3, 0, 0],
                "rotate": [0, -90, 0],
                "scale": [1.5, 1, 1.5]
            },
            "variant": "png2k"
        },
        {
            "name": "KB3D_MTM_Equip3DPrinter_A",
            "transform": {
                "translate": [0, 0, -12.7],
                "rotate": [0, 0, 0],
                "scale": [1, 1, 1]
            },
            "variant": "png4k"  # Higher res for foreground
        }
    ]

    for comp in components:
        builder.add_component(
            comp["name"],
            comp["transform"],
            comp["variant"]
        )

    # Build assembly
    assembly_usd = builder.build()

    print(f"\nAssembly created at: {assembly_usd}")
    print(f"Referenced {len(components)} components:")
    for comp in components:
        print(f"  - {comp['name']} (variant: {comp['variant']})")


def example_2_lop_network():
    """Example creating assembly LOP network in Houdini"""
    print("\n=== Example 2: Creating Assembly LOP Network ===\n")

    # Get or create stage
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Define assembly and components
    assembly_name = "KB3D_MTM_BldgLgCommsArray_A"
    component_list = [
        {
            "name": "KB3D_MTM_PropSolarPanel_A",
            "translate": [10.5, 0, 5.2],
            "rotate": [0, 45, 0],
            "scale": [1, 1, 1],
            "variant": "png2k"
        },
        {
            "name": "KB3D_MTM_PropRaisedModules_A",
            "translate": [-8.3, 0, 0],
            "rotate": [0, -90, 0],
            "scale": [1.5, 1, 1.5],
            "variant": "png2k"
        }
    ]

    # Create assembly network
    output_node = create_assembly_lop_network(stage, assembly_name, component_list)

    # Add USD ROP to export
    usd_rop = stage.createNode("usd_rop", f"{assembly_name}_export")
    usd_rop.setInput(0, output_node)
    usd_rop.parm("lopoutput").set(f"$HIP/usd_library/Models/{assembly_name}/{assembly_name}.usd")
    usd_rop.parm("trange").set(0)

    stage.layoutChildren()

    print(f"Created assembly LOP network:")
    print(f"  Output: {output_node.path()}")
    print(f"  Export: {usd_rop.path()}")
    print(f"\nComponents added: {len(component_list)}")
    for comp in component_list:
        print(f"  - {comp['name']}")

    return usd_rop


def example_3_from_spreadsheet():
    """Example building assembly from CSV/spreadsheet data"""
    print("\n=== Example 3: Building from Spreadsheet Data ===\n")

    # Simulate spreadsheet data (could be loaded from CSV)
    import csv
    from io import StringIO

    csv_data = """component_name,tx,ty,tz,rx,ry,rz,sx,sy,sz,variant
KB3D_MTM_PropSolarPanel_A,10.5,0,5.2,0,45,0,1,1,1,png2k
KB3D_MTM_PropRaisedModules_A,-8.3,0,0,0,-90,0,1.5,1,1.5,png2k
KB3D_MTM_Equip3DPrinter_A,0,0,-12.7,0,0,0,1,1,1,png4k
KB3D_MTM_PropSolarPanel_A,15.0,0,10.0,0,90,0,1,1,1,png1k
KB3D_MTM_PropSolarPanel_A,-15.0,0,10.0,0,-45,0,1,1,1,png1k"""

    # Parse CSV
    reader = csv.DictReader(StringIO(csv_data))
    components = []

    for row in reader:
        components.append({
            "name": row["component_name"],
            "transform": {
                "translate": [float(row["tx"]), float(row["ty"]), float(row["tz"])],
                "rotate": [float(row["rx"]), float(row["ry"]), float(row["rz"])],
                "scale": [float(row["sx"]), float(row["sy"]), float(row["sz"])]
            },
            "variant": row["variant"]
        })

    # Create assembly
    assembly_name = "KB3D_MTM_BldgLgCommsArray_A"
    output_dir = hou.expandString("$HIP/usd_library")

    builder = KB3DAssemblyBuilder(assembly_name, output_dir)

    for comp in components:
        builder.add_component(comp["name"], comp["transform"], comp["variant"])

    assembly_usd = builder.build()

    print(f"Built assembly from spreadsheet data:")
    print(f"  Assembly: {assembly_usd}")
    print(f"  Components: {len(components)}")
    print(f"\nFirst 3 components:")
    for comp in components[:3]:
        print(f"  - {comp['name']} at {comp['transform']['translate']}")


def example_4_interactive_lop():
    """Example creating interactive assembly in LOPs"""
    print("\n=== Example 4: Interactive Assembly in LOPs ===\n")

    # Create stage
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Create assembly root
    assembly_name = "MyCustomAssembly"

    configure_root = stage.createNode("configureprimitive", f"{assembly_name}_root")
    configure_root.parm("primpath").set(f"/{assembly_name}")
    configure_root.parm("kind").set("assembly")
    configure_root.parm("defineonly").set(True)

    last_node = configure_root

    # Component 1: Solar Panel
    ref1 = stage.createNode("reference", "ref_solar_panel")
    ref1.setInput(0, last_node)
    ref1.parm("primpath").set(f"/{assembly_name}/SolarPanel_001")
    ref1.parm("filepath").set("$HIP/usd_library/Models/KB3D_MTM_PropSolarPanel_A/KB3D_MTM_PropSolarPanel_A.usd")

    xform1 = stage.createNode("xform", "place_solar_panel")
    xform1.setInput(0, ref1)
    xform1.parm("primpath").set(f"/{assembly_name}/SolarPanel_001")
    xform1.parmTuple("t").set([10, 0, 5])
    xform1.parmTuple("r").set([0, 45, 0])

    # Component 2: Another Solar Panel (instance)
    ref2 = stage.createNode("reference", "ref_solar_panel_2")
    ref2.setInput(0, xform1)
    ref2.parm("primpath").set(f"/{assembly_name}/SolarPanel_002")
    ref2.parm("filepath").set("$HIP/usd_library/Models/KB3D_MTM_PropSolarPanel_A/KB3D_MTM_PropSolarPanel_A.usd")

    xform2 = stage.createNode("xform", "place_solar_panel_2")
    xform2.setInput(0, ref2)
    xform2.parm("primpath").set(f"/{assembly_name}/SolarPanel_002")
    xform2.parmTuple("t").set([-10, 0, 5])
    xform2.parmTuple("r").set([0, -45, 0])

    # Add assembly-level variant control
    add_variant = stage.createNode("addvariant", "assembly_texture_variant")
    add_variant.setInput(0, xform2)
    add_variant.parm("primpath").set(f"/{assembly_name}")
    add_variant.parm("variantname").set("texture_variant")

    # Export ROP
    usd_rop = stage.createNode("usd_rop", "export_assembly")
    usd_rop.setInput(0, add_variant)
    usd_rop.parm("lopoutput").set(f"$HIP/usd_library/Models/{assembly_name}/{assembly_name}.usd")

    stage.layoutChildren()

    print(f"Created interactive assembly network:")
    print(f"  Assembly: /{assembly_name}")
    print(f"  Components:")
    print(f"    - SolarPanel_001 at [10, 0, 5]")
    print(f"    - SolarPanel_002 at [-10, 0, 5]")
    print(f"  Export ROP: {usd_rop.path()}")
    print(f"\nYou can now:")
    print(f"  - Add more reference nodes for additional components")
    print(f"  - Adjust transforms interactively")
    print(f"  - Set variants per component")

    return usd_rop


def example_5_batch_from_json():
    """Example building multiple assemblies from JSON config"""
    print("\n=== Example 5: Batch Assembly from JSON ===\n")

    import json

    # Sample JSON config
    config = {
        "output_dir": hou.expandString("$HIP/usd_library"),
        "assemblies": [
            {
                "name": "KB3D_MTM_Section_A",
                "components": [
                    {
                        "name": "KB3D_MTM_PropSolarPanel_A",
                        "transform": {
                            "translate": [0, 0, 0],
                            "rotate": [0, 0, 0],
                            "scale": [1, 1, 1]
                        },
                        "variant": "png2k"
                    },
                    {
                        "name": "KB3D_MTM_PropRaisedModules_A",
                        "transform": {
                            "translate": [10, 0, 0],
                            "rotate": [0, 0, 0],
                            "scale": [1, 1, 1]
                        },
                        "variant": "png2k"
                    }
                ]
            },
            {
                "name": "KB3D_MTM_Section_B",
                "components": [
                    {
                        "name": "KB3D_MTM_Equip3DPrinter_A",
                        "transform": {
                            "translate": [0, 0, 0],
                            "rotate": [0, 0, 0],
                            "scale": [1, 1, 1]
                        },
                        "variant": "png4k"
                    }
                ]
            }
        ]
    }

    # Build all assemblies
    output_dir = config["output_dir"]
    results = []

    for asm_config in config["assemblies"]:
        builder = KB3DAssemblyBuilder(asm_config["name"], output_dir)

        for comp in asm_config["components"]:
            builder.add_component(
                comp["name"],
                comp["transform"],
                comp["variant"]
            )

        assembly_usd = builder.build()
        results.append({
            "name": asm_config["name"],
            "path": assembly_usd,
            "component_count": len(asm_config["components"])
        })

    print(f"Built {len(results)} assemblies:")
    for result in results:
        print(f"  - {result['name']}: {result['component_count']} components")
        print(f"    Path: {result['path']}")

    return results


# Run examples
if __name__ == "__main__":
    print("KB3D Assembly Examples")
    print("=" * 60)

    # Uncomment the example you want to run:

    # example_1_python_api()
    example_2_lop_network()
    # example_3_from_spreadsheet()
    # example_4_interactive_lop()
    # example_5_batch_from_json()

    print("\n" + "=" * 60)
    print("Example completed!")
