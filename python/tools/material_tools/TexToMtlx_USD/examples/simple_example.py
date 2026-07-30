"""
Simple Example - Basic MaterialX and USD Export

This example shows the most basic usage of TexToMtlx_USD:
1. Convert a texture folder to MaterialX
2. Create a USD file with the material

Usage:
    python simple_example.py
    or from Houdini Python Shell:
    exec(open('/path/to/simple_example.py').read())
"""

from tools.material_tools.TexToMtlx_USD import (
    export_materialx_from_textures,
    create_kb3d_style_usd
)

# Define paths
texture_folder = '/media/tushita/TUSHITA_LINUX_DATA/assets/kb3d_missiontominerva/Textures/png4k'
output_folder = '/tmp/materialx_test'

# Material name (should match texture naming)
material_name = 'KB3D_MTM_Decals'

# 1. Export MaterialX file
print(f"Exporting MaterialX for {material_name}...")
mtlx_result = export_materialx_from_textures(
    texture_folder=texture_folder,
    output_file=f'{output_folder}/{material_name}.mtlx',
    material_name=material_name,
    relative_texture_path='../../Textures/png4k/'
)

if mtlx_result['success']:
    print(f"✓ MaterialX exported: {mtlx_result['file']}")

    # 2. Create USD file
    print(f"Creating USD file for {material_name}...")
    usd_result = create_kb3d_style_usd(
        material_name=material_name,
        mtlx_file=f'./{material_name}.mtlx',
        output_file=f'{output_folder}/{material_name}.usd',
        kit_info={
            'kitDisplayName': 'Custom Materials',
            'kitId': 'custom_materials',
            'kitVersion': '1.0.0'
        }
    )

    if usd_result['success']:
        print(f"✓ USD exported: {usd_result['file']}")
        print("\nDone! You can now:")
        print(f"  - View MaterialX: {mtlx_result['file']}")
        print(f"  - Load USD in Houdini: {usd_result['file']}")
    else:
        print(f"✗ USD export failed: {usd_result.get('error', 'Unknown error')}")
else:
    print(f"✗ MaterialX export failed: {mtlx_result.get('error', 'Unknown error')}")
