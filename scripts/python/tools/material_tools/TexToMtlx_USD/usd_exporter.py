#!/usr/bin/env python
"""
Modular USD Material Exporter

This module provides standalone USD material export functionality that can be used
independently or integrated into other tools. It creates USD files that reference
MaterialX documents and support texture variants.

Features:
    - Create USD files referencing MaterialX materials
    - Support for texture variants (4k, 2k, 1k, jpg/png)
    - KB3D-compatible metadata and structure
    - Binary or ASCII USD output
    - Class-based inheritance patterns

Usage:
    from tools.material_tools.usd_exporter import USDExporter

    exporter = USDExporter()
    result = exporter.export_material_usd(
        material_name='MyMaterial',
        mtlx_file='./MyMaterial.mtlx',
        output_file='./MyMaterial.usd',
        variants={'texture_variant': ['png4k', 'jpg2k', 'jpg1k']}
    )
"""

import os
from typing import Dict, List, Optional


class USDExporter:
    """Export USD material files with MaterialX references and variants."""

    def __init__(self):
        """Initialize USD exporter."""
        try:
            from pxr import Usd, UsdShade, Sdf
            self.Usd = Usd
            self.UsdShade = UsdShade
            self.Sdf = Sdf
            self.available = True
        except ImportError:
            self.Usd = None
            self.UsdShade = None
            self.Sdf = None
            self.available = False
            print("WARNING: USD library not available")

    def export_material_usd(
        self,
        material_name: str,
        mtlx_file: str,
        output_file: str,
        variants: Optional[Dict[str, List[str]]] = None,
        default_variant: Optional[Dict[str, str]] = None,
        use_class_inheritance: bool = True,
        metadata: Optional[Dict] = None,
        ascii_format: bool = False
    ) -> Dict:
        """
        Export USD file for a material with MaterialX reference.

        Args:
            material_name: Material name (used as prim name)
            mtlx_file: Path to MaterialX file (relative or absolute)
            output_file: Output USD file path
            variants: Dictionary of variant sets and their values
                     e.g., {'texture_variant': ['png4k', 'jpg2k', 'jpg1k']}
            default_variant: Default variant selections
                           e.g., {'texture_variant': 'png4k'}
            use_class_inheritance: Whether to use class-based inheritance pattern
            metadata: Additional asset metadata (KB3D format)
            ascii_format: Output as ASCII .usda instead of binary .usd

        Returns:
            dict: Result with success status and details
        """
        if not self.available:
            return {
                'success': False,
                'error': 'USD library not available',
                'file': None
            }

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)

            # Remove existing file
            if os.path.exists(output_file):
                os.remove(output_file)

            # Create stage (use InMemory to control ordering)
            # Set to ASCII format for human-readable output
            stage = self.Usd.Stage.CreateInMemory()

            # Force ASCII format if requested or by default
            if ascii_format or output_file.endswith('.usda'):
                # Will be set during Export()
                pass

            # Set metadata
            stage.SetMetadata("defaultPrim", material_name)
            stage.SetMetadata("metersPerUnit", 1.0)
            stage.SetMetadata("upAxis", "Y")

            # Create material prim FIRST (KB3D pattern: material before class)
            mat_prim = stage.DefinePrim(f"/{material_name}", "Material")

            # Add KB3D metadata if provided
            if metadata:
                mat_prim.SetAssetInfoByKey("kb3d", metadata)

            # Add class inheritance if enabled (set BEFORE adding references and variants)
            if use_class_inheritance:
                inherits = mat_prim.GetInherits()
                inherits.AddInherit(f"/__class__/{material_name}", position=self.Usd.ListPositionFrontOfPrependList)

            # Make instanceable
            mat_prim.SetInstanceable(True)

            # Add MaterialX reference
            mtlx_ref_path = os.path.relpath(mtlx_file, os.path.dirname(output_file)) if not mtlx_file.startswith('.') else mtlx_file
            if not mtlx_ref_path.startswith('.'):
                mtlx_ref_path = f"./{os.path.basename(mtlx_ref_path)}"

            # Keep original material name casing for MaterialX reference
            mtlx_material_path = f"/MaterialX/Materials/{material_name}"

            references = mat_prim.GetReferences()
            references.AddReference(mtlx_ref_path, mtlx_material_path, position=self.Usd.ListPositionFrontOfPrependList)

            # Add variants if provided
            if variants:
                for variant_set_name, variant_values in variants.items():
                    self._add_variant_set(
                        mat_prim=mat_prim,
                        variant_set_name=variant_set_name,
                        variant_values=variant_values,
                        material_name=material_name
                    )

                # Set default variant selections
                if default_variant:
                    for vset_name, vset_value in default_variant.items():
                        variant_sets = mat_prim.GetVariantSets()
                        variant_sets.SetSelection(vset_name, vset_value)

            # Create class prim AFTER material (KB3D pattern)
            if use_class_inheritance:
                class_root = stage.DefinePrim("/__class__")
                class_prim = stage.DefinePrim(f"/__class__/{material_name}", "Material")

            # Export to file
            # KB3D uses .usd extension with ASCII format inside
            # To create ASCII format, we need to use ExportToString or save the layer
            root_layer = stage.GetRootLayer()

            if ascii_format or output_file.endswith('.usda') or output_file.endswith('.usd'):
                # Save as ASCII format (human-readable)
                # USD's Export() creates binary by default, we need to explicitly save as ASCII
                root_layer.Export(output_file, args={'format': 'usda'})
            else:
                # Binary format
                root_layer.Export(output_file)

            # Verify file was created
            if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                return {
                    'success': False,
                    'error': 'USD file not created properly',
                    'file': None
                }

            return {
                'success': True,
                'file': output_file,
                'material_name': material_name,
                'variants': variants,
                'format': 'ASCII' if ascii_format else 'Binary'
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f'{str(e)}\n{traceback.format_exc()}',
                'file': None
            }

    def _add_variant_set(
        self,
        mat_prim,
        variant_set_name: str,
        variant_values: List[str],
        material_name: str
    ):
        """
        Add a variant set to material prim (e.g., texture resolution variants).

        Args:
            mat_prim: Material prim
            variant_set_name: Name of variant set (e.g., 'texture_variant')
            variant_values: List of variant values (e.g., ['png4k', 'jpg2k'])
            material_name: Material name for node graph reference (keeps original casing)
        """
        variant_sets = mat_prim.GetVariantSets()
        variant_set = variant_sets.AddVariantSet(variant_set_name)

        # Define texture type mappings
        texture_nodes = [
            'image_base_color',
            'image_metalness',
            'image_specular_roughness',
            'image_opacity',
            'image_normal',
            'image_emission_color',
            'image_displacement'
        ]

        for variant_value in variant_values:
            variant_set.AddVariant(variant_value)
            variant_set.SetVariantSelection(variant_value)

            with variant_set.GetVariantEditContext():
                # Create over for the node graph (keep original material name casing)
                nodegraph_path = f"{mat_prim.GetPath()}/NG_{material_name}"
                nodegraph = mat_prim.GetStage().OverridePrim(nodegraph_path)

                # Override texture paths for each image node
                for node_name in texture_nodes:
                    node_path = f"{nodegraph_path}/{node_name}"
                    node_prim = mat_prim.GetStage().OverridePrim(node_path)

                    # Determine file extension and folder from variant value
                    folder, ext = self._parse_variant_value(variant_value)

                    # Get texture type from node name
                    tex_type = self._get_texture_type_from_node(node_name)

                    # Build texture path (keep original material name casing)
                    texture_path = f"../../Textures/{folder}/{material_name}_{tex_type}.{ext}"

                    # Set file input
                    if node_prim:
                        file_attr = node_prim.CreateAttribute(
                            "inputs:file",
                            self.Sdf.ValueTypeNames.Asset
                        )
                        file_attr.Set(self.Sdf.AssetPath(texture_path))

    def _parse_variant_value(self, variant_value: str) -> tuple:
        """
        Parse variant value to extract folder and extension.

        Args:
            variant_value: Variant value (e.g., 'png4k', 'jpg2k', 'jpg1k')

        Returns:
            tuple: (folder_name, file_extension)
        """
        # Common patterns: png4k, jpg2k, jpg1k, exr4k, etc.
        if 'png' in variant_value.lower():
            ext = 'png'
        elif 'jpg' in variant_value.lower() or 'jpeg' in variant_value.lower():
            ext = 'jpg'
        elif 'exr' in variant_value.lower():
            ext = 'exr'
        else:
            ext = 'png'  # default

        # Folder is the variant value itself
        folder = variant_value

        return folder, ext

    def _get_texture_type_from_node(self, node_name: str) -> str:
        """
        Get texture type keyword from node name.

        Args:
            node_name: MaterialX node name (e.g., 'image_base_color')

        Returns:
            str: Texture type keyword (e.g., 'basecolor')
        """
        # Map node names to texture keywords
        mapping = {
            'image_base_color': 'basecolor',
            'image_metalness': 'metallic',
            'image_specular_roughness': 'roughness',
            'image_opacity': 'opacity',
            'image_normal': 'normal',
            'image_emission_color': 'emissive',
            'image_displacement': 'displacement'
        }

        return mapping.get(node_name, node_name.replace('image_', ''))

    def create_simple_usd_reference(
        self,
        material_name: str,
        mtlx_file: str,
        output_file: str
    ) -> Dict:
        """
        Create a simple USD file that just references a MaterialX file.
        No variants, minimal metadata.

        Args:
            material_name: Material name
            mtlx_file: Path to MaterialX file (relative)
            output_file: Output USD file path

        Returns:
            dict: Result with success status
        """
        return self.export_material_usd(
            material_name=material_name,
            mtlx_file=mtlx_file,
            output_file=output_file,
            variants=None,
            use_class_inheritance=False,
            metadata=None
        )


def export_usd_material(
    material_name: str,
    mtlx_file: str,
    output_file: str,
    **kwargs
) -> Dict:
    """
    Convenience function to export USD material.

    Args:
        material_name: Material name
        mtlx_file: MaterialX file path
        output_file: Output USD file path
        **kwargs: Additional arguments for USDExporter.export_material_usd

    Returns:
        dict: Export result
    """
    exporter = USDExporter()
    return exporter.export_material_usd(
        material_name=material_name,
        mtlx_file=mtlx_file,
        output_file=output_file,
        **kwargs
    )


def create_kb3d_style_usd(
    material_name: str,
    mtlx_file: str,
    output_file: str,
    kit_info: Optional[Dict] = None
) -> Dict:
    """
    Create KB3D-style USD material with standard variants.
    Matches KB3D variant order and naming conventions.
    Creates .usd file with ASCII format inside (exactly like KB3D originals).

    Note: KB3D uses .usd extension but the file content is ASCII format (human-readable),
    not binary. We match this exact behavior.

    Args:
        material_name: Material name
        mtlx_file: MaterialX file path
        output_file: Output USD file path (.usd extension, ASCII content)
        kit_info: KB3D kit metadata dict

    Returns:
        dict: Export result
    """
    # Default KB3D metadata
    metadata = kit_info or {
        'kitDisplayName': 'Custom Materials',
        'kitId': 'custom_materials',
        'kitVersion': '1.0.0'
    }

    # Standard texture variants (KB3D order: jpg1k, jpg2k, jpg4k, png1k, png2k, png4k)
    variants = {
        'texture_variant': ['jpg1k', 'jpg2k', 'jpg4k', 'png1k', 'png2k', 'png4k']
    }

    default_variant = {
        'texture_variant': 'png4k'
    }

    # KB3D uses .usd extension with ASCII format inside (not binary)
    # Keep .usd extension but force ASCII format
    if not output_file.endswith('.usd') and not output_file.endswith('.usda'):
        output_file += '.usd'

    exporter = USDExporter()
    return exporter.export_material_usd(
        material_name=material_name,
        mtlx_file=mtlx_file,
        output_file=output_file,
        variants=variants,
        default_variant=default_variant,
        use_class_inheritance=True,
        metadata=metadata,
        ascii_format=True  # Always use ASCII format (like KB3D)
    )


# Example usage
if __name__ == '__main__':
    # Example 1: Simple USD reference
    result = export_usd_material(
        material_name='MyMaterial',
        mtlx_file='./MyMaterial.mtlx',
        output_file='./MyMaterial.usd'
    )

    # Example 2: KB3D-style USD with variants
    result = create_kb3d_style_usd(
        material_name='MyMaterial',
        mtlx_file='./MyMaterial.mtlx',
        output_file='./MyMaterial.usd',
        kit_info={
            'kitDisplayName': 'My Material Kit',
            'kitId': 'my_materials',
            'kitVersion': '1.0.0'
        }
    )

    if result['success']:
        print(f"USD created: {result['file']}")
    else:
        print(f"Error: {result['error']}")
