"""
Pipeline Integration Example - Material Library Management

This example shows how to integrate TexToMtlx_USD into a production pipeline
with versioning, multiple libraries, and organized output structure.

Usage:
    python pipeline_integration_example.py
    or from Houdini Python Shell:
    exec(open('/path/to/pipeline_integration_example.py').read())
"""

import os
from tools.material_tools.TexToMtlx_USD import convert_textures_to_materialx

class MaterialLibraryManager:
    """Manages material library creation and versioning."""

    def __init__(self, base_path='/tmp/material_libraries'):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def create_library(self, library_name, texture_path, version='1.0.0'):
        """Create a material library with proper structure."""

        # Create library folder structure
        lib_id = library_name.lower().replace(' ', '_')
        lib_path = os.path.join(self.base_path, lib_id, version)
        materials_path = os.path.join(lib_path, 'Materials')

        os.makedirs(materials_path, exist_ok=True)

        # Kit metadata
        kit_info = {
            'kitDisplayName': library_name,
            'kitId': lib_id,
            'kitVersion': version
        }

        print(f"\nCreating library: {library_name} v{version}")
        print(f"Output path: {materials_path}")
        print("-" * 60)

        # Convert all textures
        results = convert_textures_to_materialx(
            texture_folder=texture_path,
            output_folder=materials_path,
            kit_info=kit_info,
            create_usd=True,
            texture_variants=['png4k', 'png2k', 'jpg4k', 'jpg2k', 'jpg1k'],
            relative_texture_path='../../../Textures/'
        )

        # Generate manifest
        self._create_manifest(lib_path, library_name, version, results)

        return results

    def _create_manifest(self, lib_path, name, version, results):
        """Create a manifest file for the library."""
        manifest_path = os.path.join(lib_path, 'manifest.txt')

        with open(manifest_path, 'w') as f:
            f.write(f"Material Library: {name}\n")
            f.write(f"Version: {version}\n")
            f.write(f"Total Materials: {len(results)}\n")
            f.write(f"\nMaterials:\n")
            f.write("-" * 40 + "\n")

            for result in results:
                status = "SUCCESS" if result['success'] else "FAILED"
                f.write(f"{status}: {result['material']}\n")

        print(f"\n✓ Manifest created: {manifest_path}")


# Example usage: Create multiple library versions

manager = MaterialLibraryManager('/tmp/production_materials')

# Library 1: Wood Materials v1.0.0
wood_results = manager.create_library(
    library_name='Wood Materials',
    texture_path='/project/assets/textures/wood',
    version='1.0.0'
)

# Library 2: Metal Materials v1.0.0
metal_results = manager.create_library(
    library_name='Metal Materials',
    texture_path='/project/assets/textures/metal',
    version='1.0.0'
)

# Library 3: Updated Wood Materials v1.1.0
wood_v2_results = manager.create_library(
    library_name='Wood Materials',
    texture_path='/project/assets/textures/wood_updated',
    version='1.1.0'
)

print("\n" + "="*60)
print("PIPELINE SUMMARY")
print("="*60)
print(f"Wood Materials v1.0.0: {len(wood_results)} materials")
print(f"Metal Materials v1.0.0: {len(metal_results)} materials")
print(f"Wood Materials v1.1.0: {len(wood_v2_results)} materials")
print("="*60)
print(f"\nAll libraries saved to: {manager.base_path}")
print("\nDirectory structure:")
print("  production_materials/")
print("    wood_materials/")
print("      1.0.0/")
print("        Materials/  (MaterialX + USD files)")
print("        manifest.txt")
print("      1.1.0/")
print("        Materials/")
print("        manifest.txt")
print("    metal_materials/")
print("      1.0.0/")
print("        Materials/")
print("        manifest.txt")
