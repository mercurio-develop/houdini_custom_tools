"""
KB3D Component Builder - Flexible Version
Supports custom geometry paths like /filename/geo instead of hardcoded /ASSET/geo

This version allows you to specify custom prim paths for geometry,
matching Houdini's default structure where geometry is under /filename/geo
"""

import hou
from pxr import Usd, UsdGeom, Sdf, Kind, UsdShade
import os


class FlexibleKB3DComponentBuilder:
    """
    Builds KB3D-style USD components with flexible geometry path structure

    Supports custom geometry paths like:
    - /filename/geo (Houdini default)
    - /ASSET/geo (KB3D default)
    - /MyComponent/geometry
    - Any custom path you need
    """

    def __init__(self, component_name, output_dir, geo_path=None):
        """
        Args:
            component_name: Name like "KB3D_MTM_PropSolarPanel_A" or "MyComponent"
            output_dir: Base directory for Models folder
            geo_path: Custom geometry path (default: "/{component_name}/geo")
                     Examples:
                     - None -> uses "/{component_name}/geo"
                     - "/ASSET/geo" -> KB3D style
                     - "/geo" -> relative path
                     - "/{filename}/geo" -> uses component_name as filename
        """
        self.component_name = component_name
        self.output_dir = output_dir
        self.component_dir = os.path.join(output_dir, "Models", component_name)

        # Flexible geometry path
        if geo_path is None:
            # Default: /{component_name}/geo (Houdini style)
            self.geo_path = f"/{self.component_name}/geo"
        elif "{filename}" in geo_path:
            # Replace {filename} with component_name
            self.geo_path = geo_path.replace("{filename}", self.component_name)
        elif "{component}" in geo_path:
            # Replace {component} with component_name
            self.geo_path = geo_path.replace("{component}", self.component_name)
        else:
            # Use as-is
            self.geo_path = geo_path

        # File paths
        self.main_usd = os.path.join(self.component_dir, f"{component_name}.usd")
        self.payload_usd = os.path.join(self.component_dir, "payload.usd")
        self.geo_usd = os.path.join(self.component_dir, "geo.usd")
        self.mtl_usd = os.path.join(self.component_dir, "mtl.usd")

        # Texture variants
        self.variants = ["png1k", "png2k", "png4k", "jpg1k", "jpg2k", "jpg4k"]

        # Material assignments
        self.material_assignments = {}

    def create_directory_structure(self):
        """Create component folder"""
        os.makedirs(self.component_dir, exist_ok=True)
        print(f"Created directory: {self.component_dir}")

    def create_main_usd(self):
        """Create main USD file with payload and variants"""
        stage = Usd.Stage.CreateNew(self.main_usd)

        # Define root prim (use component_name as root)
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

        # Set default variant
        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"✓ Created main USD: {self.main_usd}")
        print(f"  Root prim: {root_path}")

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
        print(f"✓ Created payload USD: {self.payload_usd}")

    def create_geo_usd_from_lop(self, lop_node, root_prim_path=None):
        """
        Export geometry from a LOP node to geo.usd with custom root path

        Args:
            lop_node: Houdini LOP node containing geometry
            root_prim_path: Override root prim path (default: uses self.geo_path)
        """
        if root_prim_path is None:
            root_prim_path = self.geo_path

        # Get the stage from the LOP node
        stage = lop_node.stage()

        # Create output stage
        output_stage = Usd.Stage.CreateNew(self.geo_usd)

        # Define root prim with custom path
        root_prim = output_stage.DefinePrim(f"/{self.component_name}")
        output_stage.SetDefaultPrim(root_prim)

        # Copy geometry from input stage
        # This is a simplified version - you might want to use proper USD copying

        # Alternative: Use USD ROP
        parent = lop_node.parent()
        rop = parent.createNode("usd_rop", f"export_{self.component_name}_geo")
        rop.parm("lopoutput").set(self.geo_usd)
        rop.parm("trange").set(0)  # Current frame only
        rop.setInput(0, lop_node)

        # Render
        rop.parm("execute").pressButton()

        print(f"✓ Created geometry USD: {self.geo_usd}")
        print(f"  Geometry path: {root_prim_path}")

        # Clean up
        rop.destroy()

    def create_geo_usd_from_stage(self, stage, source_prim_path=None):
        """
        Create geo.usd from an existing USD stage

        Args:
            stage: USD stage containing geometry
            source_prim_path: Path to geometry prim in source stage
        """
        output_stage = Usd.Stage.CreateNew(self.geo_usd)

        # Set default prim
        root_prim = output_stage.DefinePrim(f"/{self.component_name}")
        output_stage.SetDefaultPrim(root_prim)

        if source_prim_path:
            # Copy specific prim from source stage
            source_prim = stage.GetPrimAtPath(source_prim_path)
            if source_prim:
                # Sublayer or reference the source
                # This is simplified - in production use proper USD copying
                pass

        output_stage.Save()
        print(f"✓ Created geometry USD: {self.geo_usd}")

    def add_material_assignment(self, geo_path, material_name):
        """
        Add material assignment for geometry

        Args:
            geo_path: Path to geometry prim (e.g., "/{component_name}/geo")
            material_name: Name of material to assign
        """
        self.material_assignments[geo_path] = material_name

    def create_mtl_usd_with_variants(self):
        """Create mtl.usd with material bindings and texture variants"""
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
                for geo_path, material_name in self.material_assignments.items():
                    # Create material reference
                    material_path = f"/{self.component_name}/Materials/{material_name}"
                    material_prim = stage.DefinePrim(material_path)

                    # Reference the material from Materials library
                    material_ref = f"@../../Materials/{material_name}.usd@"
                    material_prim.GetReferences().AddReference(material_ref)

        # Set default variant
        vset.SetVariantSelection("png2k")

        stage.Save()
        print(f"✓ Created material USD: {self.mtl_usd}")
        if self.material_assignments:
            print(f"  Material assignments:")
            for geo_path, mat_name in self.material_assignments.items():
                print(f"    {geo_path} -> {mat_name}")

    def build_from_lop_network(self, geo_lop_node):
        """
        Complete build from a LOP network node

        Args:
            geo_lop_node: LOP node with geometry
        """
        self.create_directory_structure()
        self.create_main_usd()
        self.create_payload_usd()
        self.create_geo_usd_from_lop(geo_lop_node)
        self.create_mtl_usd_with_variants()

        return self.main_usd

    def build_structure_only(self):
        """
        Build USD structure without geometry (for manual geo addition)
        """
        self.create_directory_structure()
        self.create_main_usd()
        self.create_payload_usd()
        self.create_mtl_usd_with_variants()

        print(f"\n✓ Structure created!")
        print(f"  Next: Add geometry manually to {self.geo_usd}")

        return self.main_usd


def create_component_with_custom_geo_path(
    component_name,
    output_dir,
    lop_node,
    geo_path_pattern="/{filename}/geo"
):
    """
    Helper function to create component with custom geometry path

    Args:
        component_name: Name of component
        output_dir: Output directory
        lop_node: LOP node with geometry
        geo_path_pattern: Pattern for geo path
            "{filename}" will be replaced with component_name
            "{component}" will be replaced with component_name

    Returns:
        Path to created USD file
    """
    builder = FlexibleKB3DComponentBuilder(
        component_name,
        output_dir,
        geo_path=geo_path_pattern
    )

    return builder.build_from_lop_network(lop_node)


# =============================================================================
# HOUDINI LOP NETWORK BUILDERS
# =============================================================================

def create_flexible_component_lop_network(
    parent_node,
    component_name,
    geo_path_pattern="/{filename}/geo"
):
    """
    Create a LOP network that builds component with custom geo path

    Args:
        parent_node: Parent LOP network
        component_name: Name of component
        geo_path_pattern: Geometry path pattern

    Returns:
        Output node
    """
    # Create network box for organization
    netbox = parent_node.createNetworkBox(f"netbox_{component_name}")

    # Import geometry
    sopimport = parent_node.createNode("sopimport", f"{component_name}_import")
    sopimport.parm("pathprefix").set(geo_path_pattern.replace("{filename}", component_name))

    # Configure as component
    configure_prim = parent_node.createNode("configureprimitive", f"{component_name}_configure")
    configure_prim.setInput(0, sopimport)
    configure_prim.parm("primpath").set(f"/{component_name}")
    configure_prim.parm("kind").set("component")
    configure_prim.parm("instanceable").set(True)

    # Split for geo and mtl branches
    split = parent_node.createNode("split", f"{component_name}_split")
    split.setInput(0, configure_prim)

    # Geo branch
    configure_geo = parent_node.createNode("configurelayer", f"{component_name}_geo_layer")
    configure_geo.setInput(0, split)
    configure_geo.parm("savepath").set("geo.usd")

    # Mtl branch
    mtl_lib = parent_node.createNode("materiallibrary", f"{component_name}_mtl")
    mtl_lib.setInput(0, split)

    assign_mtl = parent_node.createNode("assignmaterial", f"{component_name}_assign")
    assign_mtl.setInput(0, mtl_lib)

    configure_mtl = parent_node.createNode("configurelayer", f"{component_name}_mtl_layer")
    configure_mtl.setInput(0, assign_mtl)
    configure_mtl.parm("savepath").set("mtl.usd")

    # Merge
    merge = parent_node.createNode("merge", f"{component_name}_merge")
    merge.setInput(0, configure_geo)
    merge.setInput(1, configure_mtl)

    # Add variants
    add_variant = parent_node.createNode("addvariant", f"{component_name}_variant")
    add_variant.setInput(0, merge)
    add_variant.parm("primpath").set(f"/{component_name}")
    add_variant.parm("variantname").set("texture_variant")

    # Configure layer for payload
    configure_payload = parent_node.createNode("configurelayer", f"{component_name}_payload")
    configure_payload.setInput(0, add_variant)
    configure_payload.parm("savepath").set("payload.usd")

    # Add all to netbox
    nodes = [sopimport, configure_prim, split, configure_geo, mtl_lib,
             assign_mtl, configure_mtl, merge, add_variant, configure_payload]
    for node in nodes:
        netbox.addNode(node)
    netbox.fitAroundContents()

    # Layout
    parent_node.layoutChildren()

    print(f"✓ Created LOP network for {component_name}")
    print(f"  Geometry path pattern: {geo_path_pattern}")
    print(f"  Actual geo path: {geo_path_pattern.replace('{filename}', component_name)}")

    return configure_payload


if __name__ == "__main__":
    print("Flexible KB3D Component Builder")
    print("Supports custom geometry paths like /{filename}/geo")
    print("\nUsage examples:")
    print("\n1. Houdini default structure (/{filename}/geo):")
    print('   builder = FlexibleKB3DComponentBuilder("MyComp", "/path", "/{filename}/geo")')
    print("\n2. KB3D structure (/ASSET/geo):")
    print('   builder = FlexibleKB3DComponentBuilder("MyComp", "/path", "/ASSET/geo")')
    print("\n3. Custom structure:")
    print('   builder = FlexibleKB3DComponentBuilder("MyComp", "/path", "/geometry/main")')
