"""
KB3D USD Builder - Modular USD Creation System
Based on KitBash3D Mission to Minerva USD structure patterns

This module provides a comprehensive class-based system for creating production-ready
USD assets following KitBash3D conventions with proper layering, materials, variants,
and hierarchy management.

Author: Custom Tools
Date: 2025
"""

from pxr import Usd, UsdGeom, UsdShade, Sdf, Gf, Kind
import os
from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import json


class KB3DMetadata:
    """Handles KB3D asset metadata management"""

    def __init__(self, kit_id: str = "custom_assets",
                 kit_display_name: str = "Custom Assets",
                 kit_version: str = "1.0.0"):
        self.kit_id = kit_id
        self.kit_display_name = kit_display_name
        self.kit_version = kit_version

    def apply_to_prim(self, prim: Usd.Prim):
        """Apply KB3D metadata to a prim"""
        asset_info = {
            'kb3d': {
                'kitId': self.kit_id,
                'kitDisplayName': self.kit_display_name,
                'kitVersion': self.kit_version
            }
        }
        prim.SetAssetInfo(asset_info)


class KB3DMaterialBuilder:
    """Builds KB3D-style materials with MaterialX and texture variants"""

    TEXTURE_VARIANTS = ['jpg1k', 'jpg2k', 'jpg4k', 'png1k', 'png2k', 'png4k']

    TEXTURE_MAPS = {
        'basecolor': {'colorspace': 'srgb_texture', 'type': 'color3'},
        'metallic': {'colorspace': 'lin_rec709', 'type': 'float'},
        'roughness': {'colorspace': 'lin_rec709', 'type': 'float'},
        'normal': {'colorspace': 'lin_rec709', 'type': 'vector3'},
        'opacity': {'colorspace': 'lin_rec709', 'type': 'float'},
        'emissive': {'colorspace': 'srgb_texture', 'type': 'color3'},
        'displacement': {'colorspace': 'lin_rec709', 'type': 'float'}
    }

    def __init__(self, material_name: str, base_path: Path, metadata: Optional[KB3DMetadata] = None):
        self.material_name = material_name
        self.base_path = Path(base_path)
        self.metadata = metadata or KB3DMetadata()
        self.texture_maps = {}

    def add_texture_map(self, map_type: str, variants: Dict[str, str]):
        """
        Add a texture map with variant paths

        Args:
            map_type: Type of map (basecolor, metallic, roughness, etc.)
            variants: Dict mapping variant name to texture path
                     e.g., {'png1k': '../../Textures/png1k/Material_basecolor.png'}
        """
        if map_type not in self.TEXTURE_MAPS:
            print(f"Warning: Unknown map type '{map_type}'. Supported: {list(self.TEXTURE_MAPS.keys())}")
        self.texture_maps[map_type] = variants

    def generate_materialx(self, output_path: Path, default_variant: str = 'png4k'):
        """Generate MaterialX (.mtlx) file"""
        mtlx_content = f'''<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_{self.material_name}">
'''

        # Add image nodes for each texture map
        for map_type, variants in self.texture_maps.items():
            if map_type not in self.TEXTURE_MAPS:
                continue

            map_info = self.TEXTURE_MAPS[map_type]
            default_path = variants.get(default_variant, next(iter(variants.values())))

            mtlx_content += f'''    <image name="image_{map_type}" type="{map_info['type']}">
      <input name="file" type="filename" value="{default_path}" colorspace="{map_info['colorspace']}" />
    </image>
    <output name="image_{map_type}_output" type="{map_info['type']}" nodename="image_{map_type}" />

'''

        # Add normal map processing if present
        if 'normal' in self.texture_maps:
            mtlx_content += f'''    <normalmap name="normalmap" type="vector3">
      <input name="in" type="vector3" nodename="image_normal" />
      <input name="scale" type="float" value="1" />
    </normalmap>
    <output name="normalmap_output" type="vector3" nodename="normalmap" />

'''

        # Create standard surface shader
        mtlx_content += f'''  </nodegraph>

  <standard_surface name="SR_{self.material_name}" type="surfaceshader">
'''

        # Connect texture maps to shader inputs
        if 'basecolor' in self.texture_maps:
            mtlx_content += f'''    <input name="base_color" type="color3" nodegraph="NG_{self.material_name}" output="image_basecolor_output" />
'''
        if 'roughness' in self.texture_maps:
            mtlx_content += f'''    <input name="specular_roughness" type="float" nodegraph="NG_{self.material_name}" output="image_roughness_output" />
'''
        if 'metallic' in self.texture_maps:
            mtlx_content += f'''    <input name="metalness" type="float" nodegraph="NG_{self.material_name}" output="image_metallic_output" />
'''
        if 'normal' in self.texture_maps:
            mtlx_content += f'''    <input name="normal" type="vector3" nodegraph="NG_{self.material_name}" output="normalmap_output" />
'''
        if 'opacity' in self.texture_maps:
            mtlx_content += f'''    <input name="opacity" type="float" nodegraph="NG_{self.material_name}" output="image_opacity_output" />
'''
        if 'emissive' in self.texture_maps:
            mtlx_content += f'''    <input name="emission_color" type="color3" nodegraph="NG_{self.material_name}" output="image_emissive_output" />
'''

        mtlx_content += f'''    <input name="specular_IOR" type="float" value="1.45" />
    <input name="transmission" type="float" value="0" />
  </standard_surface>

  <surfacematerial name="{self.material_name}" type="material">
    <input name="surfaceshader" type="surfaceshader" nodename="SR_{self.material_name}" />
  </surfacematerial>
</materialx>
'''

        output_path.write_text(mtlx_content)
        return output_path

    def build(self, output_dir: Path, default_variant: str = 'png1k') -> Path:
        """
        Build complete material USD with variants

        Returns:
            Path to created material USD file
        """
        material_dir = output_dir / self.material_name
        material_dir.mkdir(parents=True, exist_ok=True)

        # Generate MaterialX file
        mtlx_path = material_dir / f"{self.material_name}.mtlx"
        self.generate_materialx(mtlx_path, default_variant)

        # Create material USD
        usd_path = material_dir / f"{self.material_name}.usd"
        stage = Usd.Stage.CreateNew(str(usd_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create material prim
        mat_prim = stage.DefinePrim(f"/{self.material_name}", 'Material')
        stage.SetDefaultPrim(mat_prim)

        # Apply metadata
        self.metadata.apply_to_prim(mat_prim)

        # Add class inheritance
        class_prim = stage.DefinePrim("/__class__/KB3D_Class", "Scope")
        class_mat = stage.DefinePrim(f"/__class__/{self.material_name}", 'Material')
        mat_prim.GetInherits().AddInherit(class_mat.GetPath())

        # Make instanceable
        mat_prim.SetInstanceable(True)

        # Add reference to MaterialX
        mat_prim.GetReferences().AddReference(
            f"./{self.material_name}.mtlx",
            f"/MaterialX/Materials/{self.material_name}"
        )

        # Create variant set for texture resolution
        vset = mat_prim.GetVariantSets().AddVariantSet('texture_variant')
        vset.SetVariantSelection(default_variant)

        for variant_name in self.TEXTURE_VARIANTS:
            vset.AddVariant(variant_name)
            vset.SetVariantSelection(variant_name)

            with vset.GetVariantEditContext():
                # Override texture paths for this variant
                ng_prim = stage.OverridePrim(f"/{self.material_name}/NG_{self.material_name}")

                for map_type, variants in self.texture_maps.items():
                    if variant_name in variants:
                        img_prim = stage.OverridePrim(f"{ng_prim.GetPath()}/image_{map_type}")
                        img_prim.CreateAttribute('inputs:file', Sdf.ValueTypeNames.Asset).Set(
                            Sdf.AssetPath(variants[variant_name])
                        )

        # Reset to default variant
        vset.SetVariantSelection(default_variant)

        stage.GetRootLayer().Save()
        return usd_path


class KB3DComponentBuilder:
    """Builds KB3D-style component USD files with payload structure"""

    def __init__(self, component_name: str, output_dir: Path, metadata: Optional[KB3DMetadata] = None):
        self.component_name = component_name
        self.output_dir = Path(output_dir)
        self.metadata = metadata or KB3DMetadata()
        self.material_bindings = []
        self.extent_hint = None

    def set_extent_hint(self, min_point: Tuple[float, float, float],
                        max_point: Tuple[float, float, float]):
        """Set bounding box extent hint"""
        self.extent_hint = (min_point, max_point)

    def add_material_reference(self, material_name: str, material_path: str):
        """Add a material reference for this component"""
        self.material_bindings.append({
            'name': material_name,
            'path': material_path
        })

    def build_payload_usd(self) -> Path:
        """Create payload.usd file that references mtl and geo"""
        payload_path = self.output_dir / self.component_name / "payload.usd"
        stage = Usd.Stage.CreateNew(str(payload_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create component prim with references to mtl and geo
        comp_prim = stage.DefinePrim(f"/{self.component_name}")
        stage.SetDefaultPrim(comp_prim)
        Kind.Registry().SetDefaultKind('component')
        Usd.ModelAPI(comp_prim).SetKind('component')

        # Add references to mtl and geo files
        comp_prim.GetReferences().AddReference("./mtl.usd")
        comp_prim.GetReferences().AddReference("./geo.usd")

        stage.GetRootLayer().Save()
        return payload_path

    def build_mtl_usd(self) -> Path:
        """Create mtl.usd file with material references"""
        mtl_path = self.output_dir / self.component_name / "mtl.usd"
        stage = Usd.Stage.CreateNew(str(mtl_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create component prim
        comp_prim = stage.OverridePrim(f"/{self.component_name}")
        stage.SetDefaultPrim(comp_prim)

        # Create variant set for texture variants
        vset = comp_prim.GetVariantSets().AddVariantSet('texture_variant')
        vset.SetVariantSelection('png4k')

        # Create mtl scope
        mtl_scope = stage.OverridePrim(f"/{self.component_name}/mtl")

        # Add material references
        for mat_binding in self.material_bindings:
            mat_prim = stage.OverridePrim(f"{mtl_scope.GetPath()}/{mat_binding['name']}")
            mat_prim.GetReferences().AddReference(
                mat_binding['path'],
                f"/{mat_binding['name']}"
            )

        # Create variants that cascade to materials
        for variant_name in KB3DMaterialBuilder.TEXTURE_VARIANTS:
            vset.AddVariant(variant_name)
            vset.SetVariantSelection(variant_name)

            with vset.GetVariantEditContext():
                over_mtl = stage.OverridePrim(f"/{self.component_name}/mtl")
                for mat_binding in self.material_bindings:
                    over_mat = stage.OverridePrim(f"{over_mtl.GetPath()}/{mat_binding['name']}")
                    mat_vset = over_mat.GetVariantSets().AddVariantSet('texture_variant')
                    mat_vset.SetVariantSelection(variant_name)

        vset.SetVariantSelection('png4k')
        stage.GetRootLayer().Save()
        return mtl_path

    def build_main_usd(self, geo_usd_path: Optional[Path] = None) -> Path:
        """
        Create main component USD file

        Args:
            geo_usd_path: Path to existing geo.usd file (if already created)
        """
        comp_dir = self.output_dir / self.component_name
        comp_dir.mkdir(parents=True, exist_ok=True)

        # Build payload and mtl files
        self.build_payload_usd()
        self.build_mtl_usd()

        # Create main USD
        main_path = comp_dir / f"{self.component_name}.usd"
        stage = Usd.Stage.CreateNew(str(main_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create component prim
        comp_prim = stage.DefinePrim(f"/{self.component_name}")
        stage.SetDefaultPrim(comp_prim)

        # Apply metadata and model API
        self.metadata.apply_to_prim(comp_prim)
        UsdGeom.ModelAPI.Apply(comp_prim)
        Usd.ModelAPI(comp_prim).SetKind('component')

        # Add class inheritance
        class_prim = stage.DefinePrim(f"/__class__/{self.component_name}")
        comp_prim.GetInherits().AddInherit(class_prim.GetPath())

        # Add payload
        comp_prim.GetPayloads().AddPayload("./payload.usd")

        # Create variant set
        vset = comp_prim.GetVariantSets().AddVariantSet('texture_variant')
        vset.SetVariantSelection('png1k')

        # Add empty variant definitions (actual data in payload)
        for variant_name in KB3DMaterialBuilder.TEXTURE_VARIANTS:
            vset.AddVariant(variant_name)

        # Set extent hint if provided
        if self.extent_hint:
            comp_prim.CreateAttribute('extentsHint', Sdf.ValueTypeNames.Float3Array).Set([
                Gf.Vec3f(*self.extent_hint[0]),
                Gf.Vec3f(*self.extent_hint[1])
            ])

        stage.GetRootLayer().Save()
        return main_path


class KB3DAssemblyBuilder:
    """Builds KB3D-style assembly USD files with component references"""

    def __init__(self, assembly_name: str, output_dir: Path, metadata: Optional[KB3DMetadata] = None):
        self.assembly_name = assembly_name
        self.output_dir = Path(output_dir)
        self.metadata = metadata or KB3DMetadata()
        self.groups = {}  # Dict of group_name -> list of components
        self.extent_hint = None

    def add_component_reference(self,
                                component_name: str,
                                component_path: str,
                                transform: Optional[Dict] = None,
                                group_name: Optional[str] = None,
                                instanceable: bool = True):
        """
        Add a component reference to the assembly

        Args:
            component_name: Unique name for this instance
            component_path: Path to component USD file
            transform: Dict with 'translate', 'rotate', 'scale' keys
            group_name: Optional group/scope to organize under
            instanceable: Whether to make this reference instanceable
        """
        component_data = {
            'name': component_name,
            'path': component_path,
            'transform': transform or {},
            'instanceable': instanceable
        }

        if group_name:
            if group_name not in self.groups:
                self.groups[group_name] = []
            self.groups[group_name].append(component_data)
        else:
            if '__root__' not in self.groups:
                self.groups['__root__'] = []
            self.groups['__root__'].append(component_data)

    def set_extent_hint(self, min_point: Tuple[float, float, float],
                        max_point: Tuple[float, float, float]):
        """Set bounding box extent hint"""
        self.extent_hint = (min_point, max_point)

    def build(self, default_variant: str = 'png1k') -> Path:
        """Build the assembly USD file"""
        assembly_dir = self.output_dir / self.assembly_name
        assembly_dir.mkdir(parents=True, exist_ok=True)

        assembly_path = assembly_dir / f"{self.assembly_name}.usd"
        stage = Usd.Stage.CreateNew(str(assembly_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create assembly prim
        asm_prim = stage.DefinePrim(f"/{self.assembly_name}", 'Xform')
        stage.SetDefaultPrim(asm_prim)

        # Apply metadata and model API
        self.metadata.apply_to_prim(asm_prim)
        UsdGeom.ModelAPI.Apply(asm_prim)
        Usd.ModelAPI(asm_prim).SetKind('assembly')

        # Add class inheritance
        class_prim = stage.DefinePrim(f"/__class__/{self.assembly_name}")
        asm_prim.GetInherits().AddInherit(class_prim.GetPath())

        # Create variant set
        vset = asm_prim.GetVariantSets().AddVariantSet('texture_variant')
        vset.SetVariantSelection(default_variant)

        # Set extent hint
        if self.extent_hint:
            asm_prim.CreateAttribute('extentsHint', Sdf.ValueTypeNames.Float3Array).Set([
                Gf.Vec3f(*self.extent_hint[0]),
                Gf.Vec3f(*self.extent_hint[1])
            ])

        # Add component references by group
        for group_name, components in self.groups.items():
            if group_name == '__root__':
                parent_prim = asm_prim
            else:
                # Create group scope
                group_prim = stage.DefinePrim(f"{asm_prim.GetPath()}/{group_name}", 'Scope')
                Usd.ModelAPI(group_prim).SetKind('group')
                parent_prim = group_prim

            # Add each component
            for comp_data in components:
                comp_prim = stage.DefinePrim(f"{parent_prim.GetPath()}/{comp_data['name']}", 'Xform')
                comp_prim.SetInstanceable(comp_data['instanceable'])
                Usd.ModelAPI(comp_prim).SetKind('component')

                # Add reference
                comp_prim.GetReferences().AddReference(comp_data['path'])

                # Apply transform
                xformable = UsdGeom.Xformable(comp_prim)
                if 'translate' in comp_data['transform']:
                    xformable.AddTranslateOp().Set(Gf.Vec3d(*comp_data['transform']['translate']))
                if 'rotate' in comp_data['transform']:
                    # Assuming XYZ Euler angles in degrees
                    rot = comp_data['transform']['rotate']
                    xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rot))
                if 'scale' in comp_data['transform']:
                    xformable.AddScaleOp().Set(Gf.Vec3f(*comp_data['transform']['scale']))

        # Create variants that cascade texture variant to all children
        all_components = []
        for components in self.groups.values():
            all_components.extend(components)

        for variant_name in KB3DMaterialBuilder.TEXTURE_VARIANTS:
            vset.AddVariant(variant_name)
            vset.SetVariantSelection(variant_name)

            with vset.GetVariantEditContext():
                # Override each component's variant
                for group_name, components in self.groups.items():
                    if group_name == '__root__':
                        parent_path = f"/{self.assembly_name}"
                    else:
                        over_group = stage.OverridePrim(f"/{self.assembly_name}/{group_name}")
                        parent_path = str(over_group.GetPath())

                    for comp_data in components:
                        over_comp = stage.OverridePrim(f"{parent_path}/{comp_data['name']}")
                        comp_vset = over_comp.GetVariantSets().AddVariantSet('texture_variant')
                        comp_vset.SetVariantSelection(variant_name)

        # Reset to default variant
        vset.SetVariantSelection(default_variant)

        stage.GetRootLayer().Save()
        return assembly_path


class KB3DUSDBuilder:
    """
    Main class for building KB3D-style USD asset libraries

    This class orchestrates the creation of complete USD asset structures
    following KitBash3D conventions.
    """

    def __init__(self, base_path: Path, kit_id: str = "custom_assets",
                 kit_display_name: str = "Custom Assets", kit_version: str = "1.0.0"):
        """
        Initialize USD builder

        Args:
            base_path: Root directory for the asset library
            kit_id: Unique identifier for the kit
            kit_display_name: Human-readable kit name
            kit_version: Version string
        """
        self.base_path = Path(base_path)
        self.metadata = KB3DMetadata(kit_id, kit_display_name, kit_version)

        # Create standard directory structure
        self.materials_dir = self.base_path / "Materials"
        self.models_dir = self.base_path / "Models"
        self.textures_dir = self.base_path / "Textures"

        self.materials_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.textures_dir.mkdir(parents=True, exist_ok=True)

    def create_material_builder(self, material_name: str) -> KB3DMaterialBuilder:
        """Create a material builder instance"""
        return KB3DMaterialBuilder(material_name, self.materials_dir, self.metadata)

    def create_component_builder(self, component_name: str) -> KB3DComponentBuilder:
        """Create a component builder instance"""
        return KB3DComponentBuilder(component_name, self.models_dir, self.metadata)

    def create_assembly_builder(self, assembly_name: str) -> KB3DAssemblyBuilder:
        """Create an assembly builder instance"""
        return KB3DAssemblyBuilder(assembly_name, self.models_dir, self.metadata)

    def save_metadata(self):
        """Save kb3d_metadata.json file"""
        metadata_path = self.base_path / "kb3d_metadata.json"
        metadata = {
            "kitId": self.metadata.kit_id,
            "kitDisplayName": self.metadata.kit_display_name,
            "version": self.metadata.kit_version
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)


# Convenience functions

def build_simple_material(material_name: str,
                         texture_folder: Path,
                         output_dir: Path,
                         metadata: Optional[KB3DMetadata] = None) -> Path:
    """
    Quick function to build a material from a texture folder

    Assumes standard KB3D texture naming: {material_name}_{maptype}.{ext}
    """
    builder = KB3DMaterialBuilder(material_name, output_dir, metadata)
    texture_folder = Path(texture_folder)

    # Auto-detect texture maps
    for map_type in KB3DMaterialBuilder.TEXTURE_MAPS.keys():
        variants = {}
        for variant in KB3DMaterialBuilder.TEXTURE_VARIANTS:
            # Check for PNG and JPG
            ext = variant[:3]  # 'png' or 'jpg'
            res = variant[3:]  # '1k', '2k', '4k'

            tex_name = f"{material_name}_{map_type}.{ext}"
            tex_path = texture_folder / variant / tex_name

            if tex_path.exists():
                # Use relative path from material location
                rel_path = f"../../Textures/{variant}/{tex_name}"
                variants[variant] = rel_path

        if variants:
            builder.add_texture_map(map_type, variants)

    return builder.build(output_dir)


def build_simple_component(component_name: str,
                          geo_usd_path: Path,
                          material_bindings: List[Dict[str, str]],
                          output_dir: Path,
                          metadata: Optional[KB3DMetadata] = None) -> Path:
    """
    Quick function to build a component

    Args:
        component_name: Name of component
        geo_usd_path: Path to existing geo.usd file
        material_bindings: List of dicts with 'name' and 'path' keys
        output_dir: Output directory
        metadata: Optional metadata
    """
    builder = KB3DComponentBuilder(component_name, output_dir, metadata)

    for binding in material_bindings:
        builder.add_material_reference(binding['name'], binding['path'])

    return builder.build_main_usd(geo_usd_path)
