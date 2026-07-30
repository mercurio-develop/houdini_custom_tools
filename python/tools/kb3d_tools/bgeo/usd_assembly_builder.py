"""
USD Assembly Builder - Create KB3D-style USD assemblies from components

This module creates assembly USD files that reference multiple components
with transforms, creating the full KB3D hierarchy.

An assembly follows the same 4-file pattern as components, but the main file
contains Xform prims that reference other components with instanceable flags.

Author: Custom Tools
Date: 2025-10-28
"""

import hou
from pxr import Usd, UsdGeom, Sdf, Kind, Gf
import os
from typing import Dict, List, Optional, Tuple


class USDAssemblyBuilder:
    """Builds KB3D-style USD assembly files from components."""

    def __init__(self):
        self.default_kit_info = {
            'kitDisplayName': 'Custom Assets',
            'kitId': 'custom_assets',
            'kitVersion': '1.0.0'
        }

    def create_assembly(
        self,
        assembly_name: str,
        components: List[Dict],
        output_folder: str,
        kit_info: Optional[Dict] = None,
        texture_variants: Optional[List[str]] = None,
        default_variant: str = 'png4k'
    ) -> Dict:
        """
        Create a KB3D-style USD assembly from components.

        Args:
            assembly_name: Name of the assembly (e.g., "MyBuilding_A")
            components: List of component dicts:
                [
                    {
                        'name': 'ModuleA_001',  # Instance name
                        'reference': '../ComponentName/ComponentName.usd',  # Path to component USD
                        'component_name': 'ComponentName',  # Base component name
                        'translate': (x, y, z),  # Optional
                        'rotate': (rx, ry, rz),  # Optional (degrees)
                        'scale': (sx, sy, sz),  # Optional
                        'kind': 'component' or 'assembly',  # Optional
                        'instanceable': True  # Optional
                    }
                ]
            output_folder: Where to save USD files
            kit_info: KB3D metadata dict
            texture_variants: List of texture variant names
            default_variant: Default texture variant

        Returns:
            {
                'success': bool,
                'assembly_name': str,
                'main_file': path,
                'payload_file': path,
                'geo_file': path,
                'mtl_file': path,
                'components_count': int,
                'error': str (if failed)
            }
        """
        try:
            # Create output folder
            os.makedirs(output_folder, exist_ok=True)

            # Set defaults
            if kit_info is None:
                kit_info = self.default_kit_info.copy()

            if texture_variants is None:
                texture_variants = ['jpg1k', 'jpg2k', 'jpg4k', 'png1k', 'png2k', 'png4k']

            # Define file paths
            main_file = os.path.join(output_folder, f'{assembly_name}.usd')
            payload_file = os.path.join(output_folder, 'payload.usd')
            geo_file = os.path.join(output_folder, 'geo.usd')
            mtl_file = os.path.join(output_folder, 'mtl.usd')

            # 1. Create geo.usd (empty for assemblies, or merged geometry)
            self._create_assembly_geo_usd(geo_file, assembly_name)

            # 2. Create mtl.usd (empty for assemblies)
            self._create_assembly_mtl_usd(mtl_file, assembly_name)

            # 3. Create payload.usd
            self._create_assembly_payload_usd(
                payload_file,
                assembly_name,
                components
            )

            # 4. Create main .usd file
            self._create_assembly_main_usd(
                main_file,
                assembly_name,
                kit_info,
                texture_variants,
                default_variant,
                components
            )

            return {
                'success': True,
                'assembly_name': assembly_name,
                'main_file': main_file,
                'payload_file': payload_file,
                'geo_file': geo_file,
                'mtl_file': mtl_file,
                'components_count': len(components)
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create assembly {assembly_name}: {str(e)}'
            }

    def _create_assembly_geo_usd(self, output_file: str, assembly_name: str):
        """Create geo.usd for assembly (usually empty or contains base geometry)."""
        # Create stage
        stage = Usd.Stage.CreateNew(output_file)

        # Set up metadata
        stage.SetDefaultPrim(stage.GetPrimAtPath(f'/{assembly_name}'))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

        # Create root prim (empty for assembly)
        root_xform = UsdGeom.Xform.Define(stage, f'/{assembly_name}')
        Usd.ModelAPI(root_xform).SetKind(Kind.Tokens.assembly)

        # Save as binary USDC
        stage.GetRootLayer().Export(output_file, args={'format': 'usdc'})

    def _create_assembly_mtl_usd(self, output_file: str, assembly_name: str):
        """Create mtl.usd for assembly (usually empty)."""
        # Create stage
        stage = Usd.Stage.CreateNew(output_file)

        # Set up metadata
        stage.SetDefaultPrim(stage.GetPrimAtPath(f'/{assembly_name}'))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

        # Create root prim (empty)
        root_prim = stage.DefinePrim(f'/{assembly_name}')

        # Save as binary USDC
        stage.GetRootLayer().Export(output_file, args={'format': 'usdc'})

    def _create_assembly_payload_usd(
        self,
        output_file: str,
        assembly_name: str,
        components: List[Dict]
    ):
        """Create payload.usd that references geo, mtl, and defines component hierarchy."""
        # Create stage
        stage = Usd.Stage.CreateNew(output_file)

        # Set up metadata
        stage.SetDefaultPrim(stage.GetPrimAtPath(f'/{assembly_name}'))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

        # Create root prim
        root_prim = stage.DefinePrim(f'/{assembly_name}')
        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.assembly)

        # Add references to geo.usd and mtl.usd (KB3D order: mtl first, then geo)
        references = root_prim.GetReferences()
        references.AddReference('./mtl.usd')
        references.AddReference('./geo.usd')

        # Note: Component references are added in the main file, not payload
        # The payload.usd stays simple like KB3D pattern

        # Save as ASCII
        stage.GetRootLayer().Export(output_file, args={'format': 'usda'})

    def _create_assembly_main_usd(
        self,
        output_file: str,
        assembly_name: str,
        kit_info: Dict,
        texture_variants: List[str],
        default_variant: str,
        components: List[Dict]
    ):
        """Create main .usd file with component references and transforms."""
        # Create stage
        stage = Usd.Stage.CreateNew(output_file)

        # Set up metadata
        stage.SetDefaultPrim(stage.GetPrimAtPath(f'/{assembly_name}'))
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

        # Create root prim
        root_xform = UsdGeom.Xform.Define(stage, f'/{assembly_name}')
        root_prim = root_xform.GetPrim()

        # Set kind to assembly
        Usd.ModelAPI(root_prim).SetKind(Kind.Tokens.assembly)

        # Add KB3D metadata
        root_prim.SetAssetInfoByKey('kb3d', {
            'kitDisplayName': kit_info['kitDisplayName'],
            'kitId': kit_info['kitId'],
            'kitVersion': kit_info['kitVersion']
        })

        # Add GeomModelAPI
        UsdGeom.ModelAPI.Apply(root_prim)

        # Add class inheritance
        inherits = root_prim.GetInherits()
        inherits.AddInherit(f'/__class__/{assembly_name}', position=Usd.ListPositionFrontOfPrependList)

        # Add payload reference
        payloads = root_prim.GetPayloads()
        payloads.AddPayload('./payload.usd')

        # Create texture variant set on root
        variant_set = root_prim.GetVariantSets().AddVariantSet('texture_variant')
        for variant_name in texture_variants:
            variant_set.AddVariant(variant_name)
        variant_set.SetVariantSelection(default_variant)

        # Prepend variant set order
        root_prim.SetMetadata('variantSets', Sdf.StringListOp.Create(
            prependedItems=['texture_variant']
        ))

        # Create building/group scope (KB3D pattern uses a scope like "Building")
        # This groups all the component instances
        group_name = f'{assembly_name}_Building'
        group_scope = UsdGeom.Scope.Define(stage, f'/{assembly_name}/{group_name}')
        group_scope.GetPrim().SetMetadata('kind', Kind.Tokens.group)

        # Add component instances
        for comp_data in components:
            instance_name = comp_data['name']
            reference_path = comp_data['reference']
            kind = comp_data.get('kind', 'component')
            instanceable = comp_data.get('instanceable', True)

            # Create Xform for this component instance
            instance_path = f'/{assembly_name}/{group_name}/{instance_name}'
            instance_xform = UsdGeom.Xform.Define(stage, instance_path)
            instance_prim = instance_xform.GetPrim()

            # Set kind
            Usd.ModelAPI(instance_prim).SetKind(kind)

            # Set instanceable flag
            instance_prim.SetInstanceable(instanceable)

            # Add reference to component USD
            references = instance_prim.GetReferences()
            references.AddReference(reference_path, position=Usd.ListPositionFrontOfPrependList)

            # Add transforms
            self._add_transforms(instance_xform, comp_data)

        # Create texture variant edits (propagate to all children)
        for variant_name in texture_variants:
            variant_set.SetVariantSelection(variant_name)

            with variant_set.GetVariantEditContext():
                # Set variant on all child components
                group_prim = stage.GetPrimAtPath(f'/{assembly_name}/{group_name}')

                for comp_data in components:
                    instance_name = comp_data['name']
                    instance_path = f'/{assembly_name}/{group_name}/{instance_name}'
                    instance_prim = stage.GetPrimAtPath(instance_path)

                    if instance_prim:
                        # Set texture variant on this instance
                        child_variant_set = instance_prim.GetVariantSets().AddVariantSet('texture_variant')
                        child_variant_set.SetVariantSelection(variant_name)

        # Reset to default variant
        variant_set.SetVariantSelection(default_variant)

        # Create class definition
        class_scope = stage.DefinePrim('/__class__', 'Scope')
        class_prim = stage.DefinePrim(f'/__class__/{assembly_name}')
        class_prim.SetSpecifier(Sdf.SpecifierClass)

        # Save as ASCII
        stage.GetRootLayer().Export(output_file, args={'format': 'usda'})

    def _add_transforms(self, xform: UsdGeom.Xform, comp_data: Dict):
        """Add transform operations to Xform."""
        # KB3D order: translate, rotate, scale
        xform_ops = []

        # Translate
        if 'translate' in comp_data:
            translate = comp_data['translate']
            translate_op = xform.AddTranslateOp()
            translate_op.Set(Gf.Vec3d(translate[0], translate[1], translate[2]))
            xform_ops.append('xformOp:translate')

        # Rotate (XYZ Euler angles in degrees)
        if 'rotate' in comp_data:
            rotate = comp_data['rotate']
            rotate_op = xform.AddRotateXYZOp()
            rotate_op.Set(Gf.Vec3f(rotate[0], rotate[1], rotate[2]))
            xform_ops.append('xformOp:rotateXYZ')

        # Scale
        if 'scale' in comp_data:
            scale = comp_data['scale']
            scale_op = xform.AddScaleOp()
            scale_op.Set(Gf.Vec3f(scale[0], scale[1], scale[2]))
            xform_ops.append('xformOp:scale')

        # Set xformOpOrder
        if xform_ops:
            xform.SetXformOpOrder(xform_ops)


# Convenience functions
def create_assembly_from_components(
    assembly_name: str,
    components: List[Dict],
    output_folder: str,
    **kwargs
) -> Dict:
    """
    Create USD assembly from list of components.

    Args:
        assembly_name: Name for the assembly
        components: List of component data dicts
        output_folder: Where to save files
        **kwargs: Additional arguments for create_assembly()

    Returns:
        Result dictionary
    """
    builder = USDAssemblyBuilder()
    return builder.create_assembly(assembly_name, components, output_folder, **kwargs)
