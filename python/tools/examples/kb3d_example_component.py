"""
Example: Building a single KB3D-style component in Houdini

This script demonstrates how to create a component USD with the KB3D structure:
- Main USD with payload and variants
- Payload USD referencing geo.usd and mtl.usd
- Proper metadata (kind, instanceable, asset info)
"""

import hou
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from kb3d_usd_structure_builder import KB3DComponentBuilder, create_component_lop_network


def example_1_python_api():
    """Example using pure Python USD API"""
    print("\n=== Example 1: Using Python USD API ===\n")

    # Define component
    component_name = "KB3D_MTM_PropSolarPanel_A"
    output_dir = "$HIP/usd_library"
    output_dir = hou.expandString(output_dir)

    # Create builder
    builder = KB3DComponentBuilder(component_name, output_dir)

    # Build structure (without geometry for now)
    builder.create_directory_structure()
    builder.create_main_usd()
    builder.create_payload_usd()

    # Material assignments
    material_assignments = {
        f"/{component_name}/geo": "KB3D_MTM_MetalGoldenWornFillA"
    }
    builder.create_mtl_usd_with_variants(material_assignments)

    print(f"\nComponent created at: {builder.main_usd}")
    print(f"Structure:")
    print(f"  - {builder.main_usd}")
    print(f"  - {builder.payload_usd}")
    print(f"  - {builder.mtl_usd}")
    print(f"\nNOTE: geo.usd must be created from actual geometry")


def example_2_lop_network():
    """Example creating LOP network in Houdini"""
    print("\n=== Example 2: Creating LOP Network ===\n")

    # Get or create stage node
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Create component network
    component_name = "KB3D_MTM_PropSolarPanel_A"
    output_node = create_component_lop_network(stage, component_name)

    print(f"Created LOP network for: {component_name}")
    print(f"Output node: {output_node.path()}")
    print(f"\nNext steps:")
    print(f"  1. Connect geometry to the sopimport node")
    print(f"  2. Set up materials in the materiallibrary node")
    print(f"  3. Configure save paths in the configurelayer nodes")
    print(f"  4. Create a USD ROP to export")

    # Layout nodes
    stage.layoutChildren()

    return output_node


def example_3_from_existing_geo():
    """Example building component from existing geometry node"""
    print("\n=== Example 3: From Existing Geometry ===\n")

    # This assumes you have a geometry node at /obj/geo1
    geo_node = hou.node("/obj/geo1")
    if not geo_node:
        print("Creating example geometry node...")
        obj_context = hou.node("/obj")
        geo_node = obj_context.createNode("geo", "geo1")

        # Create simple box
        box = geo_node.createNode("box")
        box.setDisplayFlag(True)
        box.setRenderFlag(True)

    # Create stage and import SOP
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Import geometry
    sopimport = stage.createNode("sopimport", "import_solar_panel")
    sopimport.parm("soppath").set(geo_node.path() + "/box")
    sopimport.parm("pathprefix").set("/KB3D_MTM_PropSolarPanel_A")

    # Configure as component
    configure = stage.createNode("configureprimitive", "set_component")
    configure.setInput(0, sopimport)
    configure.parm("primpath").set("/KB3D_MTM_PropSolarPanel_A")
    configure.parm("kind").set("component")
    configure.parm("instanceable").set(True)

    # Add variants
    add_variant = stage.createNode("addvariant", "texture_variants")
    add_variant.setInput(0, configure)
    add_variant.parm("primpath").set("/KB3D_MTM_PropSolarPanel_A")
    add_variant.parm("variantname").set("texture_variant")

    # Add variant options
    variants = ["png1k", "png2k", "png4k", "jpg1k", "jpg2k", "jpg4k"]
    for i, variant in enumerate(variants):
        add_variant.parm(f"variantname{i+1}").set(variant)

    # USD ROP for export
    usd_rop = stage.createNode("usd_rop", "export_component")
    usd_rop.setInput(0, add_variant)
    usd_rop.parm("lopoutput").set("$HIP/usd_library/Models/KB3D_MTM_PropSolarPanel_A/KB3D_MTM_PropSolarPanel_A.usd")
    usd_rop.parm("trange").set(0)  # Current frame

    stage.layoutChildren()

    print(f"Created LOP network:")
    print(f"  Import: {sopimport.path()}")
    print(f"  Configure: {configure.path()}")
    print(f"  Variants: {add_variant.path()}")
    print(f"  Export: {usd_rop.path()}")
    print(f"\nTo export: usd_rop.parm('execute').pressButton()")

    return usd_rop


def example_4_with_materials():
    """Example with MaterialX materials"""
    print("\n=== Example 4: With Materials ===\n")

    # Create stage
    stage = hou.node("/stage")
    if not stage:
        stage = hou.node("/obj").createNode("stage")

    # Import geo (reusing from example 3)
    geo_node = hou.node("/obj/geo1")
    if not geo_node:
        obj_context = hou.node("/obj")
        geo_node = obj_context.createNode("geo", "geo1")
        box = geo_node.createNode("box")
        box.setDisplayFlag(True)
        box.setRenderFlag(True)

    sopimport = stage.createNode("sopimport", "import_with_materials")
    sopimport.parm("soppath").set(geo_node.path() + "/box")
    sopimport.parm("pathprefix").set("/KB3D_MTM_PropSolarPanel_A")

    # Material library
    mtl_lib = stage.createNode("materiallibrary", "kb3d_materials")
    mtl_lib.setInput(0, sopimport)

    # Create MaterialX standard surface
    # This would normally be done through the UI or with detailed MaterialX code
    # For now, we create a placeholder

    # Assign material
    assign = stage.createNode("assignmaterial", "assign_material")
    assign.setInput(0, mtl_lib)
    assign.parm("primpattern").set("/KB3D_MTM_PropSolarPanel_A//*")
    assign.parm("matspecpath1").set("/KB3D_MTM_PropSolarPanel_A/Materials/KB3D_MTM_MetalGoldenWornFillA")

    # Configure as component
    configure = stage.createNode("configureprimitive", "set_component_with_mtl")
    configure.setInput(0, assign)
    configure.parm("primpath").set("/KB3D_MTM_PropSolarPanel_A")
    configure.parm("kind").set("component")

    stage.layoutChildren()

    print(f"Created LOP network with materials:")
    print(f"  Material Library: {mtl_lib.path()}")
    print(f"  Assign Material: {assign.path()}")
    print(f"\nNext: Add MaterialX standard_surface shader in material library")

    return configure


# Run examples
if __name__ == "__main__":
    print("KB3D Component Examples")
    print("=" * 60)

    # Uncomment the example you want to run:

    # example_1_python_api()
    # example_2_lop_network()
    example_3_from_existing_geo()
    # example_4_with_materials()

    print("\n" + "=" * 60)
    print("Example completed!")
