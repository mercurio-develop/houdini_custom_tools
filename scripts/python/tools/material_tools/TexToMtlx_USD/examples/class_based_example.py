"""
Class-Based Example - Using Exporter Classes Directly

This example shows how to use the MaterialXExporter and USDExporter classes
directly for more control over the export process.

Usage:
    python class_based_example.py
    or from Houdini Python Shell:
    exec(open('/path/to/class_based_example.py').read())
"""

from tools.material_tools.TexToMtlx_USD import MaterialXExporter, USDExporter

# Initialize exporters
mtlx_exporter = MaterialXExporter()
usd_exporter = USDExporter()

# Define paths
texture_folder = '/media/tushita/TUSHITA_LINUX_DATA/assets/kb3d_missiontominerva/Textures/png4k'
output_folder = '/tmp/materialx_class_test'
material_name = 'KB3D_MTM_Decals'

# MaterialX Export with custom options
print("Exporting MaterialX with custom options...")
mtlx_result = mtlx_exporter.export_from_folder(
    texture_folder=texture_folder,
    output_file=f'{output_folder}/{material_name}.mtlx',
    material_name=material_name,
    relative_texture_path='../../Textures/png4k/',
    colorspace='lin_rec709',
    materialx_version='1.38'
)

if mtlx_result['success']:
    print(f"✓ MaterialX exported: {mtlx_result['file']}")
    print(f"  Textures found: {mtlx_result['texture_count']}")
    print(f"  Texture types: {', '.join(mtlx_result.get('texture_types', []))}")

    # USD Export with full options
    print("\nExporting USD with texture variants...")
    usd_result = usd_exporter.export_material_usd(
        material_name=material_name,
        mtlx_file=f'./{material_name}.mtlx',
        output_file=f'{output_folder}/{material_name}.usd',
        texture_variants=['png4k', 'png2k', 'jpg4k', 'jpg2k', 'jpg1k'],
        default_variant='png4k',
        kit_info={
            'kitDisplayName': 'High Quality Materials',
            'kitId': 'hq_materials',
            'kitVersion': '2.0.0'
        },
        ascii_format=True  # Force ASCII format
    )

    if usd_result['success']:
        print(f"✓ USD exported: {usd_result['file']}")
        print(f"  Default variant: {usd_result.get('default_variant', 'N/A')}")
        print(f"  Variants: {', '.join(usd_result.get('variants', []))}")

        # You can now load this USD in Houdini:
        # import hou
        # stage = hou.node('/stage').createNode('reference', f'{material_name}_ref')
        # stage.parm('filepath1').set(usd_result['file'])
    else:
        print(f"✗ USD export failed: {usd_result.get('error', 'Unknown error')}")
else:
    print(f"✗ MaterialX export failed: {mtlx_result.get('error', 'Unknown error')}")
