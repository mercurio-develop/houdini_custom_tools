"""
KB3D USD Builder - Usage Examples

Demonstrates how to use the KB3D USD Builder system to create
production-ready USD assets following KitBash3D conventions.
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kb3d_usd_builder import (
    KB3DUSDBuilder,
    KB3DMaterialBuilder,
    KB3DComponentBuilder,
    KB3DAssemblyBuilder,
    KB3DMetadata,
    build_simple_material,
    build_simple_component
)


# =============================================================================
# EXAMPLE 1: Creating a Complete Asset Library
# =============================================================================

def example_01_complete_asset_library():
    """Create a complete asset library from scratch"""
    print("=" * 80)
    print("EXAMPLE 1: Creating Complete Asset Library")
    print("=" * 80)

    # Initialize the builder
    base_path = Path("/tmp/my_custom_assets")
    builder = KB3DUSDBuilder(
        base_path=base_path,
        kit_id="my_custom_kit",
        kit_display_name="My Custom Assets",
        kit_version="1.0.0"
    )

    # Save metadata
    builder.save_metadata()
    print(f"✓ Created asset library at: {base_path}")
    print(f"✓ Saved metadata file")
    return builder


# =============================================================================
# EXAMPLE 2: Creating a Material with Texture Variants
# =============================================================================

def example_02_create_material():
    """Create a material with full texture variants"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Creating Material with Texture Variants")
    print("=" * 80)

    output_dir = Path("/tmp/my_custom_assets/Materials")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create metadata
    metadata = KB3DMetadata(
        kit_id="my_custom_kit",
        kit_display_name="My Custom Assets",
        kit_version="1.0.0"
    )

    # Create material builder
    mat_builder = KB3DMaterialBuilder("CustomMetal_A", output_dir, metadata)

    # Add texture maps with variants
    # In real usage, you'd have actual texture files at these paths
    mat_builder.add_texture_map('basecolor', {
        'png1k': '../../Textures/png1k/CustomMetal_A_basecolor.png',
        'png2k': '../../Textures/png2k/CustomMetal_A_basecolor.png',
        'png4k': '../../Textures/png4k/CustomMetal_A_basecolor.png',
        'jpg1k': '../../Textures/jpg1k/CustomMetal_A_basecolor.jpg',
        'jpg2k': '../../Textures/jpg2k/CustomMetal_A_basecolor.jpg',
        'jpg4k': '../../Textures/jpg4k/CustomMetal_A_basecolor.jpg',
    })

    mat_builder.add_texture_map('metallic', {
        'png1k': '../../Textures/png1k/CustomMetal_A_metallic.png',
        'png2k': '../../Textures/png2k/CustomMetal_A_metallic.png',
        'png4k': '../../Textures/png4k/CustomMetal_A_metallic.png',
        'jpg1k': '../../Textures/jpg1k/CustomMetal_A_metallic.jpg',
        'jpg2k': '../../Textures/jpg2k/CustomMetal_A_metallic.jpg',
        'jpg4k': '../../Textures/jpg4k/CustomMetal_A_metallic.jpg',
    })

    mat_builder.add_texture_map('roughness', {
        'png1k': '../../Textures/png1k/CustomMetal_A_roughness.png',
        'png2k': '../../Textures/png2k/CustomMetal_A_roughness.png',
        'png4k': '../../Textures/png4k/CustomMetal_A_roughness.png',
        'jpg1k': '../../Textures/jpg1k/CustomMetal_A_roughness.jpg',
        'jpg2k': '../../Textures/jpg2k/CustomMetal_A_roughness.jpg',
        'jpg4k': '../../Textures/jpg4k/CustomMetal_A_roughness.jpg',
    })

    mat_builder.add_texture_map('normal', {
        'png1k': '../../Textures/png1k/CustomMetal_A_normal.png',
        'png2k': '../../Textures/png2k/CustomMetal_A_normal.png',
        'png4k': '../../Textures/png4k/CustomMetal_A_normal.png',
        'jpg1k': '../../Textures/jpg1k/CustomMetal_A_normal.jpg',
        'jpg2k': '../../Textures/jpg2k/CustomMetal_A_normal.jpg',
        'jpg4k': '../../Textures/jpg4k/CustomMetal_A_normal.jpg',
    })

    # Build the material
    mat_path = mat_builder.build(output_dir, default_variant='png1k')
    print(f"✓ Created material USD: {mat_path}")
    print(f"  - Material folder: {mat_path.parent}")
    print(f"  - MaterialX file: {mat_path.parent / 'CustomMetal_A.mtlx'}")
    print(f"  - Variants: {', '.join(KB3DMaterialBuilder.TEXTURE_VARIANTS)}")
    return mat_path


# =============================================================================
# EXAMPLE 3: Creating a Simple Component
# =============================================================================

def example_03_create_component():
    """Create a component that references materials"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Creating Component with Material References")
    print("=" * 80)

    output_dir = Path("/tmp/my_custom_assets/Models")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = KB3DMetadata(
        kit_id="my_custom_kit",
        kit_display_name="My Custom Assets",
        kit_version="1.0.0"
    )

    # Create component builder
    comp_builder = KB3DComponentBuilder("CustomProp_A", output_dir, metadata)

    # Set bounding box
    comp_builder.set_extent_hint(
        min_point=(-5.0, 0.0, -3.0),
        max_point=(5.0, 10.0, 3.0)
    )

    # Add material references
    comp_builder.add_material_reference(
        material_name="CustomMetal_A",
        material_path="../../Materials/CustomMetal_A/CustomMetal_A.usd"
    )

    comp_builder.add_material_reference(
        material_name="CustomGlass_A",
        material_path="../../Materials/CustomGlass_A/CustomGlass_A.usd"
    )

    # Build the component
    # Note: In real usage, you'd also create/provide a geo.usd file
    comp_path = comp_builder.build_main_usd()
    print(f"✓ Created component USD: {comp_path}")
    print(f"  - Component folder: {comp_path.parent}")
    print(f"  - Payload file: {comp_path.parent / 'payload.usd'}")
    print(f"  - Material layer: {comp_path.parent / 'mtl.usd'}")
    print(f"  - Materials: CustomMetal_A, CustomGlass_A")
    return comp_path


# =============================================================================
# EXAMPLE 4: Creating an Assembly from Components
# =============================================================================

def example_04_create_assembly():
    """Create an assembly that references multiple components"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Creating Assembly with Component References")
    print("=" * 80)

    output_dir = Path("/tmp/my_custom_assets/Models")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = KB3DMetadata(
        kit_id="my_custom_kit",
        kit_display_name="My Custom Assets",
        kit_version="1.0.0"
    )

    # Create assembly builder
    asm_builder = KB3DAssemblyBuilder("CustomBuilding_A", output_dir, metadata)

    # Set overall bounding box
    asm_builder.set_extent_hint(
        min_point=(-50.0, 0.0, -30.0),
        max_point=(50.0, 40.0, 30.0)
    )

    # Add components organized by groups
    # Group 1: Foundation
    asm_builder.add_component_reference(
        component_name="Foundation_Base_001",
        component_path="../CustomFoundation_A/CustomFoundation_A.usd",
        transform={'translate': (0, 0, 0)},
        group_name="Foundation",
        instanceable=True
    )

    # Group 2: Walls
    asm_builder.add_component_reference(
        component_name="Wall_North_001",
        component_path="../CustomWall_A/CustomWall_A.usd",
        transform={'translate': (0, 5, 20), 'rotate': (0, 0, 0)},
        group_name="Walls",
        instanceable=True
    )

    asm_builder.add_component_reference(
        component_name="Wall_South_001",
        component_path="../CustomWall_A/CustomWall_A.usd",
        transform={'translate': (0, 5, -20), 'rotate': (0, 180, 0)},
        group_name="Walls",
        instanceable=True
    )

    asm_builder.add_component_reference(
        component_name="Wall_East_001",
        component_path="../CustomWall_A/CustomWall_A.usd",
        transform={'translate': (25, 5, 0), 'rotate': (0, 90, 0)},
        group_name="Walls",
        instanceable=True
    )

    asm_builder.add_component_reference(
        component_name="Wall_West_001",
        component_path="../CustomWall_A/CustomWall_A.usd",
        transform={'translate': (-25, 5, 0), 'rotate': (0, -90, 0)},
        group_name="Walls",
        instanceable=True
    )

    # Group 3: Props
    asm_builder.add_component_reference(
        component_name="Prop_Equipment_001",
        component_path="../CustomProp_A/CustomProp_A.usd",
        transform={'translate': (10, 0, 10)},
        group_name="Props",
        instanceable=True
    )

    asm_builder.add_component_reference(
        component_name="Prop_Equipment_002",
        component_path="../CustomProp_A/CustomProp_A.usd",
        transform={'translate': (-10, 0, -10), 'rotate': (0, 45, 0)},
        group_name="Props",
        instanceable=True
    )

    # Build the assembly
    asm_path = asm_builder.build(default_variant='png1k')
    print(f"✓ Created assembly USD: {asm_path}")
    print(f"  - Assembly folder: {asm_path.parent}")
    print(f"  - Groups: Foundation, Walls, Props")
    print(f"  - Total components: 7")
    print(f"  - Default variant: png1k")
    return asm_path


# =============================================================================
# EXAMPLE 5: Using Convenience Functions
# =============================================================================

def example_05_convenience_functions():
    """Use quick convenience functions for simple workflows"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Using Convenience Functions")
    print("=" * 80)

    # Quick material creation from texture folder
    # Assumes textures are organized like:
    # /path/to/textures/
    #   png1k/MaterialName_basecolor.png, MaterialName_metallic.png, etc.
    #   png2k/MaterialName_basecolor.png, MaterialName_metallic.png, etc.
    #   ...

    texture_folder = Path("/path/to/textures")
    output_dir = Path("/tmp/my_custom_assets/Materials")

    metadata = KB3DMetadata("my_kit", "My Kit", "1.0.0")

    # This function auto-detects all texture maps
    # mat_path = build_simple_material(
    #     material_name="AutoMaterial_A",
    #     texture_folder=texture_folder,
    #     output_dir=output_dir,
    #     metadata=metadata
    # )
    # print(f"✓ Quick material created: {mat_path}")

    # Quick component creation
    component_path = build_simple_component(
        component_name="QuickComponent_A",
        geo_usd_path=Path("/path/to/geo.usd"),
        material_bindings=[
            {'name': 'Material1', 'path': '../../Materials/Material1/Material1.usd'},
            {'name': 'Material2', 'path': '../../Materials/Material2/Material2.usd'}
        ],
        output_dir=Path("/tmp/my_custom_assets/Models"),
        metadata=metadata
    )
    print(f"✓ Quick component created: {component_path}")


# =============================================================================
# EXAMPLE 6: Advanced Material with All Texture Maps
# =============================================================================

def example_06_advanced_material():
    """Create a material with all possible texture maps"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Advanced Material with All Texture Maps")
    print("=" * 80)

    output_dir = Path("/tmp/my_custom_assets/Materials")
    metadata = KB3DMetadata("my_kit", "My Kit", "1.0.0")

    mat_builder = KB3DMaterialBuilder("AdvancedMaterial_A", output_dir, metadata)

    # Add ALL texture map types
    texture_types = ['basecolor', 'metallic', 'roughness', 'normal',
                    'opacity', 'emissive', 'displacement']

    for tex_type in texture_types:
        variants = {}
        for variant in KB3DMaterialBuilder.TEXTURE_VARIANTS:
            ext = variant[:3]
            variants[variant] = f"../../Textures/{variant}/AdvancedMaterial_A_{tex_type}.{ext}"
        mat_builder.add_texture_map(tex_type, variants)

    mat_path = mat_builder.build(output_dir, default_variant='png4k')
    print(f"✓ Created advanced material: {mat_path}")
    print(f"  - Texture maps: {', '.join(texture_types)}")
    print(f"  - Default variant: png4k")


# =============================================================================
# EXAMPLE 7: Building Complete Asset from Houdini Geometry
# =============================================================================

def example_07_houdini_integration():
    """Example showing how to integrate with Houdini workflow"""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Houdini Integration Workflow")
    print("=" * 80)

    print("""
    WORKFLOW: Creating KB3D-Style Asset from Houdini

    1. In Houdini (LOP context):
       - Build your geometry in SOPs
       - Create materials with MaterialX
       - Use SOP Import/Create LOP to bring geometry to LOPs
       - Assign materials using Material Library and Assign Material
       - Export geo.usd using USD ROP

    2. In Python (this script):
       - Use KB3DComponentBuilder to wrap geo.usd
       - Add material references
       - Build component structure

    3. For assemblies:
       - Use KB3DAssemblyBuilder
       - Reference multiple components
       - Add transforms and grouping
    """)

    # Example code structure:
    output_dir = Path("/tmp/my_custom_assets/Models")
    metadata = KB3DMetadata("my_kit", "My Kit", "1.0.0")

    # Step 1: Component was created in Houdini, geo.usd exported
    geo_path = Path("/path/to/houdini_export/geo.usd")

    # Step 2: Wrap with KB3D structure
    comp_builder = KB3DComponentBuilder("HoudiniAsset_A", output_dir, metadata)
    comp_builder.add_material_reference("Mat1", "../../Materials/Mat1/Mat1.usd")

    # Note: You would copy geo.usd to the component folder
    # or reference it from the payload.usd

    print("✓ Integration workflow outlined")


# =============================================================================
# EXAMPLE 8: Batch Processing Multiple Assets
# =============================================================================

def example_08_batch_processing():
    """Batch process multiple assets"""
    print("\n" + "=" * 80)
    print("EXAMPLE 8: Batch Processing Multiple Assets")
    print("=" * 80)

    base_path = Path("/tmp/my_custom_assets")
    builder = KB3DUSDBuilder(base_path, "batch_kit", "Batch Assets", "1.0.0")

    # Define assets to create
    materials = ['Metal_A', 'Metal_B', 'Glass_A', 'Concrete_A']
    components = ['Prop_A', 'Prop_B', 'Equipment_A']

    print(f"Processing {len(materials)} materials...")
    for mat_name in materials:
        mat_builder = builder.create_material_builder(mat_name)
        # Add minimal texture maps
        mat_builder.add_texture_map('basecolor', {
            'png1k': f'../../Textures/png1k/{mat_name}_basecolor.png'
        })
        # mat_builder.build(builder.materials_dir)
        print(f"  ✓ {mat_name}")

    print(f"\nProcessing {len(components)} components...")
    for comp_name in components:
        comp_builder = builder.create_component_builder(comp_name)
        comp_builder.add_material_reference('Metal_A',
            '../../Materials/Metal_A/Metal_A.usd')
        # comp_builder.build_main_usd()
        print(f"  ✓ {comp_name}")

    builder.save_metadata()
    print(f"\n✓ Batch processing complete!")


# =============================================================================
# Main Execution
# =============================================================================

if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "KB3D USD BUILDER EXAMPLES" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    # Run examples
    try:
        example_01_complete_asset_library()
        example_02_create_material()
        example_03_create_component()
        example_04_create_assembly()
        example_05_convenience_functions()
        example_06_advanced_material()
        example_07_houdini_integration()
        example_08_batch_processing()

        print("\n" + "=" * 80)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nCheck /tmp/my_custom_assets for generated USD files")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
