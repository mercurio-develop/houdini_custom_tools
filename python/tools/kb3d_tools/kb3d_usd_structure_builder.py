"""
KitBash3D USD Structure Builder
Automates creation of KB3D-style USD component and assembly hierarchies in Houdini

Based on analysis of KB3D Mission to Minerva asset structure:
- Flat component hierarchy with sibling references
- Payload pattern (main → payload → [geo + mtl])
- Texture variant system (6 variants: png/jpg at 1k/2k/4k)
- MaterialX standard_surface shaders
- Proper USD composition arcs and metadata
"""

import hou
from pxr import Usd, UsdGeom, Sdf, Kind, UsdShade
import os
import json


class KB3DComponentBuilder:
    """Builds a single KB3D-style USD component with payload structure and variants"""

    def __init__(self, component_name, output_dir, texture_maps=None):
        """
        Args:
            component_name: Name like "KB3D_MTM_PropSolarPanel_A"
            output_dir: Base directory for Models folder
            texture_maps: Dict of material assignments
        """
        self.component_name = component_name
        self.output_dir = output_dir
        self.component_dir = os.path.join(output_dir, "Models", component_name)
        self.texture_maps = texture_maps or {}

        # File paths
        self.main_usd = os.path.join(self.component_dir, f"{component_name}.usd")
        self.payload_usd = os.path.join(self.component_dir, "payload.usd")
        self.geo_usd = os.path.join(self.component_dir, "geo.usd")
        self.mtl_usd = os.path.join(self.component_dir, "mtl.usd")

        # Texture variants
        self.variants = ["png1k", "png2k", "png4k", "jpg1k", "jpg2k", "jpg4k"]

    def create_directory_structure(self):
        """Create component folder"""
        os.makedirs(self.component_dir, exist_ok=True)

    def create_main_usd(self):
        """Create main USD file with payload and variants"""
        stage = Usd.Stage.CreateNew(self.main_usd)

        # Define root prim
        root_path = f"/{self.component_name}"
        root_prim = stage.DefinePrim(root_path)
        stage.SetDefaultPrim(root_prim)

        # Set kind to component
        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.component)

        # Make instanceable for performance
        root_prim.SetInstanceable(True)

        # Add asset info
        model_api = Usd.ModelAPI(root_prim)
        model_api.SetAssetName(self.component_name)
        model_api.SetAssetIdentifier(self.component_name)

        # Add payload reference (relative path)
        root_prim.GetPayloads().AddPayload(Sdf.Payload("./payload.usd"))

        # Create variant set for texture resolution
        vset = root_prim.GetVariantSets().AddVariantSet("texture_variant")

        for variant in self.variants:
            vset.AddVariant(variant)
            vset.SetVariantSelection(variant)
            # Variant-specific overrides will be in mtl.usd

        # Set default variant
        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"Created main USD: {self.main_usd}")

    def create_payload_usd(self):
        """Create payload.usd that references geo and mtl"""
        stage = Usd.Stage.CreateNew(self.payload_usd)

        # Define root prim
        root_path = f"/{self.component_name}"
        root_prim = stage.DefinePrim(root_path)
        stage.SetDefaultPrim(root_prim)

        # Set kind
        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.component)

        # Add references to geo and mtl (order matters: mtl first for material bindings)
        references = root_prim.GetReferences()
        references.AddReference("./mtl.usd")
        references.AddReference("./geo.usd")

        stage.Save()
        print(f"Created payload USD: {self.payload_usd}")

    def create_geo_usd_from_lop(self, lop_node):
        """
        Export geometry from a LOP node to geo.usd

        Args:
            lop_node: Houdini LOP node containing geometry
        """
        # Configure the LOP node to save to geo.usd
        rop = lop_node.parent().createNode("usd_rop")
        rop.parm("lopoutput").set(self.geo_usd)
        rop.parm("trange").set(0)  # Current frame only
        rop.setInput(0, lop_node)

        # Render
        rop.parm("execute").pressButton()

        print(f"Created geometry USD: {self.geo_usd}")

        # Clean up
        rop.destroy()

    def create_mtl_usd_with_variants(self, material_assignments):
        """
        Create mtl.usd with material bindings and texture variants

        Args:
            material_assignments: Dict like {"/path/to/geo": "MaterialName"}
        """
        stage = Usd.Stage.CreateNew(self.mtl_usd)

        # Define root prim
        root_path = f"/{self.component_name}"
        root_prim = stage.DefinePrim(root_path)
        stage.SetDefaultPrim(root_prim)

        # Create variant set
        vset = root_prim.GetVariantSets().AddVariantSet("texture_variant")

        for variant in self.variants:
            vset.AddVariant(variant)
            vset.SetVariantSelection(variant)

            with vset.GetVariantEditContext():
                # For each material assignment
                for geo_path, material_name in material_assignments.items():
                    # Create material reference
                    material_path = f"/{self.component_name}/Materials/{material_name}"
                    material_prim = stage.DefinePrim(material_path)

                    # Reference the material from Materials library
                    material_ref = f"@../../Materials/{material_name}.usd@"
                    material_prim.GetReferences().AddReference(material_ref)

                    # Override texture paths for this variant
                    # This would normally set parameters on the material
                    # to point to the correct texture resolution folder

        # Set default variant
        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"Created material USD: {self.mtl_usd}")

    def build_from_lop_network(self, geo_lop_node, material_assignments):
        """
        Complete build from a LOP network node

        Args:
            geo_lop_node: LOP node with geometry
            material_assignments: Material to geometry mappings
        """
        self.create_directory_structure()
        self.create_main_usd()
        self.create_payload_usd()
        self.create_geo_usd_from_lop(geo_lop_node)
        self.create_mtl_usd_with_variants(material_assignments)

        return self.main_usd


class KB3DAssemblyBuilder:
    """Builds KB3D-style assembly USD that references multiple components"""

    def __init__(self, assembly_name, output_dir):
        """
        Args:
            assembly_name: Name like "KB3D_MTM_BldgLgCommsArray_A"
            output_dir: Base directory for Models folder
        """
        self.assembly_name = assembly_name
        self.output_dir = output_dir
        self.assembly_dir = os.path.join(output_dir, "Models", assembly_name)

        self.main_usd = os.path.join(self.assembly_dir, f"{assembly_name}.usd")
        self.payload_usd = os.path.join(self.assembly_dir, "payload.usd")
        self.mtl_usd = os.path.join(self.assembly_dir, "mtl.usd")

        self.components = []  # List of component dicts
        self.variants = ["png1k", "png2k", "png4k", "jpg1k", "jpg2k", "jpg4k"]

    def add_component(self, component_name, transform=None, variant="png2k"):
        """
        Add a component reference to the assembly

        Args:
            component_name: Name of component USD (sibling folder)
            transform: Dict with translate, rotate, scale
            variant: Texture variant to use
        """
        if transform is None:
            transform = {
                "translate": [0, 0, 0],
                "rotate": [0, 0, 0],
                "scale": [1, 1, 1]
            }

        self.components.append({
            "name": component_name,
            "transform": transform,
            "variant": variant
        })

    def create_directory_structure(self):
        """Create assembly folder"""
        os.makedirs(self.assembly_dir, exist_ok=True)

    def create_main_usd(self):
        """Create main assembly USD with payload and variants"""
        stage = Usd.Stage.CreateNew(self.main_usd)

        # Define root prim
        root_path = f"/{self.assembly_name}"
        root_prim = stage.DefinePrim(root_path)
        stage.SetDefaultPrim(root_prim)

        # Set kind to assembly
        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.assembly)

        # Add asset info
        model_api = Usd.ModelAPI(root_prim)
        model_api.SetAssetName(self.assembly_name)
        model_api.SetAssetIdentifier(self.assembly_name)

        # Add payload
        root_prim.GetPayloads().AddPayload(Sdf.Payload("./payload.usd"))

        # Create variant set for texture resolution
        vset = root_prim.GetVariantSets().AddVariantSet("texture_variant")

        for variant in self.variants:
            vset.AddVariant(variant)
            vset.SetVariantSelection(variant)
            # When this variant is active, all child components should use it

        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"Created assembly USD: {self.main_usd}")

    def create_payload_usd(self):
        """Create payload.usd with all component references"""
        stage = Usd.Stage.CreateNew(self.payload_usd)

        # Define root prim
        root_path = f"/{self.assembly_name}"
        root_prim = stage.DefinePrim(root_path, "Scope")
        stage.SetDefaultPrim(root_prim)

        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.assembly)

        # Add each component
        for i, comp in enumerate(self.components):
            comp_name = comp["name"]
            child_path = f"{root_path}/Component_{i:03d}_{comp_name}"

            # Create Xform for the component
            xform = UsdGeom.Xform.Define(stage, child_path)
            prim = xform.GetPrim()

            # Add reference to sibling component folder
            ref_path = f"@../{comp_name}/{comp_name}.usd@"
            prim.GetReferences().AddReference(ref_path)

            # Set transform
            xform.AddTranslateOp().Set(tuple(comp["transform"]["translate"]))
            xform.AddRotateXYZOp().Set(tuple(comp["transform"]["rotate"]))
            xform.AddScaleOp().Set(tuple(comp["transform"]["scale"]))

            # Set texture variant on the referenced component
            vset = prim.GetVariantSets().AddVariantSet("texture_variant")
            vset.SetVariantSelection(comp["variant"])

        stage.Save()
        print(f"Created payload USD: {self.payload_usd}")
        print(f"  Added {len(self.components)} component references")

    def create_mtl_usd(self):
        """Create assembly-level material overrides (optional)"""
        stage = Usd.Stage.CreateNew(self.mtl_usd)

        root_path = f"/{self.assembly_name}"
        root_prim = stage.DefinePrim(root_path)
        stage.SetDefaultPrim(root_prim)

        # Assembly-level material overrides would go here
        # For now, we rely on component materials

        stage.Save()
        print(f"Created material USD: {self.mtl_usd}")

    def build(self):
        """Build complete assembly structure"""
        self.create_directory_structure()
        self.create_main_usd()
        self.create_payload_usd()
        self.create_mtl_usd()

        return self.main_usd


class KB3DMaterialLibraryBuilder:
    """Builds MaterialX materials with texture variants"""

    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.materials_dir = os.path.join(output_dir, "Materials")
        os.makedirs(self.materials_dir, exist_ok=True)

    def create_material(self, material_name, texture_maps):
        """
        Create a MaterialX material USD with variants

        Args:
            material_name: Like "KB3D_MTM_MetalGoldenWornFillA"
            texture_maps: Dict of map types: {
                "basecolor": "path/to/base.png",
                "metallic": "path/to/metal.png",
                ...
            }
        """
        material_usd = os.path.join(self.materials_dir, f"{material_name}.usd")
        stage = Usd.Stage.CreateNew(material_usd)

        # Create material
        material_path = f"/Materials/{material_name}"
        material = UsdShade.Material.Define(stage, material_path)

        # This would normally create a MaterialX shader network
        # For now, we create a placeholder that would be filled
        # with proper MaterialX standard_surface nodes

        # Create variant set for texture resolution
        variants = ["png1k", "png2k", "png4k", "jpg1k", "jpg2k", "jpg4k"]
        vset = material.GetPrim().GetVariantSets().AddVariantSet("texture_variant")

        for variant in variants:
            vset.AddVariant(variant)
            vset.SetVariantSelection(variant)

            with vset.GetVariantEditContext():
                # Override texture paths for this variant
                # Example: ../../Textures/png2k/MaterialName_basecolor.png
                pass

        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"Created material: {material_usd}")

        return material_usd


def create_kb3d_structure_from_config(config_file):
    """
    Build complete KB3D structure from JSON config

    Config format:
    {
        "output_dir": "/path/to/output",
        "components": [
            {
                "name": "KB3D_MTM_PropSolarPanel_A",
                "lop_node": "/stage/geo1",
                "materials": {"geo_path": "MaterialName"}
            }
        ],
        "assemblies": [
            {
                "name": "KB3D_MTM_BldgLgCommsArray_A",
                "components": [
                    {
                        "name": "KB3D_MTM_PropSolarPanel_A",
                        "transform": {"translate": [10, 0, 5]},
                        "variant": "png2k"
                    }
                ]
            }
        ]
    }
    """
    with open(config_file, 'r') as f:
        config = json.load(f)

    output_dir = config["output_dir"]

    # Build components
    component_usds = {}
    for comp_config in config.get("components", []):
        builder = KB3DComponentBuilder(
            comp_config["name"],
            output_dir,
            comp_config.get("materials", {})
        )

        # Get LOP node if specified
        lop_node = None
        if "lop_node" in comp_config:
            lop_node = hou.node(comp_config["lop_node"])

        if lop_node:
            usd_path = builder.build_from_lop_network(lop_node, comp_config.get("materials", {}))
        else:
            # Manual build
            builder.create_directory_structure()
            builder.create_main_usd()
            builder.create_payload_usd()
            usd_path = builder.main_usd

        component_usds[comp_config["name"]] = usd_path

    # Build assemblies
    assembly_usds = {}
    for asm_config in config.get("assemblies", []):
        builder = KB3DAssemblyBuilder(asm_config["name"], output_dir)

        for comp in asm_config.get("components", []):
            builder.add_component(
                comp["name"],
                comp.get("transform"),
                comp.get("variant", "png2k")
            )

        usd_path = builder.build()
        assembly_usds[asm_config["name"]] = usd_path

    return {
        "components": component_usds,
        "assemblies": assembly_usds
    }


# Houdini LOP network builder functions
def create_component_lop_network(parent_node, component_name):
    """
    Create a LOP network that mimics KB3D component structure

    Returns the output node that can be saved to USD
    """
    # Create network box for organization
    netbox = parent_node.createNetworkBox(f"netbox_{component_name}")

    # Import geometry (placeholder - user provides this)
    sopimport = parent_node.createNode("sopimport", f"{component_name}_import")

    # Configure as component
    configure_prim = parent_node.createNode("configureprimitive", f"{component_name}_configure")
    configure_prim.setInput(0, sopimport)
    configure_prim.parm("primpath").set(f"/{component_name}")
    configure_prim.parm("kind").set("component")
    configure_prim.parm("instanceable").set(True)

    # Split for geo and mtl branches
    split = parent_node.createNode("split", f"{component_name}_split")
    split.setInput(0, configure_prim)

    # Geo branch - configure layer to save geo.usd
    configure_geo = parent_node.createNode("configurelayer", f"{component_name}_geo_layer")
    configure_geo.setInput(0, split)
    # User would set save path here

    # Mtl branch - material library
    mtl_lib = parent_node.createNode("materiallibrary", f"{component_name}_mtl")
    mtl_lib.setInput(0, split)

    assign_mtl = parent_node.createNode("assignmaterial", f"{component_name}_assign")
    assign_mtl.setInput(0, mtl_lib)

    configure_mtl = parent_node.createNode("configurelayer", f"{component_name}_mtl_layer")
    configure_mtl.setInput(0, assign_mtl)

    # Merge geo and mtl
    merge = parent_node.createNode("merge", f"{component_name}_merge")
    merge.setInput(0, configure_geo)
    merge.setInput(1, configure_mtl)

    # Add variants
    add_variant = parent_node.createNode("addvariant", f"{component_name}_variant")
    add_variant.setInput(0, merge)
    add_variant.parm("primpath").set(f"/{component_name}")
    add_variant.parm("variantname").set("texture_variant")
    add_variant.parm("variantsets").set("png1k png2k png4k jpg1k jpg2k jpg4k")

    # Configure layer for payload
    configure_payload = parent_node.createNode("configurelayer", f"{component_name}_payload")
    configure_payload.setInput(0, add_variant)

    # Add all to netbox
    netbox.addNode(sopimport)
    netbox.addNode(configure_prim)
    netbox.addNode(split)
    netbox.addNode(configure_geo)
    netbox.addNode(mtl_lib)
    netbox.addNode(assign_mtl)
    netbox.addNode(configure_mtl)
    netbox.addNode(merge)
    netbox.addNode(add_variant)
    netbox.addNode(configure_payload)

    netbox.fitAroundContents()

    return configure_payload


def create_assembly_lop_network(parent_node, assembly_name, component_list):
    """
    Create a LOP network for assembly with component references

    Args:
        parent_node: Parent LOP network
        assembly_name: Name of assembly
        component_list: List of dicts with component info
    """
    # Create assembly root
    configure_asm = parent_node.createNode("configureprimitive", f"{assembly_name}_root")
    configure_asm.parm("primpath").set(f"/{assembly_name}")
    configure_asm.parm("kind").set("assembly")
    configure_asm.parm("defineonly").set(True)

    last_node = configure_asm

    # Add each component reference
    for i, comp in enumerate(component_list):
        # Reference node
        ref_node = parent_node.createNode("reference", f"{assembly_name}_ref_{i}")
        ref_node.setInput(0, last_node)
        ref_node.parm("primpath").set(f"/{assembly_name}/Component_{i:03d}")
        ref_node.parm("filepath").set(f"@../{comp['name']}/{comp['name']}.usd@")

        # Transform
        xform_node = parent_node.createNode("xform", f"{assembly_name}_xform_{i}")
        xform_node.setInput(0, ref_node)
        xform_node.parm("primpath").set(f"/{assembly_name}/Component_{i:03d}")

        if "translate" in comp:
            xform_node.parmTuple("t").set(comp["translate"])
        if "rotate" in comp:
            xform_node.parmTuple("r").set(comp["rotate"])
        if "scale" in comp:
            xform_node.parmTuple("s").set(comp["scale"])

        # Set variant
        set_variant = parent_node.createNode("setvariant", f"{assembly_name}_variant_{i}")
        set_variant.setInput(0, xform_node)
        set_variant.parm("primpath").set(f"/{assembly_name}/Component_{i:03d}")
        set_variant.parm("variantname").set("texture_variant")
        set_variant.parm("variantchoice").set(comp.get("variant", "png2k"))

        last_node = set_variant

    # Add assembly-level variant
    add_variant = parent_node.createNode("addvariant", f"{assembly_name}_variant")
    add_variant.setInput(0, last_node)
    add_variant.parm("primpath").set(f"/{assembly_name}")
    add_variant.parm("variantname").set("texture_variant")

    return add_variant


if __name__ == "__main__":
    print("KB3D USD Structure Builder")
    print("Import this module and use the builder classes or LOP network functions")
    print("\nExample usage:")
    print("  from kb3d_usd_structure_builder import KB3DComponentBuilder")
    print("  builder = KB3DComponentBuilder('MyComponent', '/path/to/output')")
    print("  builder.create_main_usd()")
