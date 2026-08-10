"""
Simple BGEO to USD Conversion Example

This example shows the most basic usage:
1. Analyze BGEO files in a folder
2. Convert them to KB3D USD structure

Usage:
    python bgeo_simple_conversion.py
    or from Houdini Python Shell:
    exec(open('/path/to/bgeo_simple_conversion.py').read())
"""

from tools.kb3d_tools.bgeo import (
    analyze_bgeo_folder,
    convert_bgeo_to_usd,
)


def main() -> None:
    bgeo_folder = '/path/to/your/bgeo/files'
    output_folder = '/path/to/output/usd'

    print("=" * 60)
    print("STEP 1: ANALYZING BGEO FILES")
    print("=" * 60)

    analysis = analyze_bgeo_folder(bgeo_folder)

    if not analysis['success']:
        print(f"Error: {analysis.get('error', 'Unknown error')}")
        return

    print(f"\nFound {len(analysis['assets'])} assets:")
    for asset_name, asset_data in analysis['assets'].items():
        print(f"\n  {asset_name}:")
        print(f"    Parts: {len(asset_data['parts'])}")
        print(f"    Materials: {', '.join(sorted(asset_data['all_materials']))}")

        for part_name, part_data in asset_data['parts'].items():
            print(f"      - {part_name}: {len(part_data['geometry'].prims())} prims")

    print("\n" + "=" * 60)
    input("Press ENTER to continue with conversion...")

    print("\n" + "=" * 60)
    print("STEP 2: CONVERTING TO USD")
    print("=" * 60)

    result = convert_bgeo_to_usd(
        bgeo_folder=bgeo_folder,
        output_folder=output_folder,
        kit_info={
            'kitDisplayName': 'Custom Assets',
            'kitId': 'custom_assets',
            'kitVersion': '1.0.0',
        },
        texture_variants=['jpg1k', 'jpg2k', 'jpg4k', 'png1k', 'png2k', 'png4k'],
        default_variant='png4k',
        create_assemblies=True,
    )

    if result['success']:
        print("\n" + "=" * 60)
        print("CONVERSION SUCCESSFUL!")
        print("=" * 60)
        print(f"Components created: {len(result['components'])}")
        print(f"Assemblies created: {len(result['assemblies'])}")
        print(f"Materials found: {len(result['materials'])}")
    else:
        print("\n" + "=" * 60)
        print("CONVERSION FAILED")
        print("=" * 60)
        for error in result.get('errors') or []:
            print(f"  - {error}")


if __name__ == "__main__":
    main()
