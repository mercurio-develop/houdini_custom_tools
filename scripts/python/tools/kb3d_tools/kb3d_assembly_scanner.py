"""
KB3D Assembly Scanner and Reconstructor

Scans source part folders and production assemblies to extract transform data,
material assignments, and instance relationships. Then reconstructs production-ready
assemblies from source parts.

Author: Custom Tools
Date: 2025
"""

from pxr import Usd, UsdGeom, Sdf, Gf
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass, asdict
import re


@dataclass
class TransformData:
    """Stores USD transform operation data"""
    translate: Optional[Tuple[float, float, float]] = None
    rotate: Optional[Tuple[float, float, float]] = None
    scale: Optional[Tuple[float, float, float]] = None
    rotate_order: str = "XYZ"  # XYZ, XZY, YXZ, etc.

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class InstanceData:
    """Stores assembly instance information"""
    instance_name: str
    source_part_name: str
    referenced_model_path: Optional[str] = None
    transform: Optional[TransformData] = None
    instanceable: bool = True
    group_name: Optional[str] = None
    kind: str = "component"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        if self.transform:
            data['transform'] = self.transform.to_dict()
        return data


@dataclass
class AssemblyMetadata:
    """Stores assembly-level metadata"""
    assembly_name: str
    extent_hint: Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = None
    default_variant: str = "png1k"
    total_instances: int = 0
    groups: List[str] = None

    def __post_init__(self):
        if self.groups is None:
            self.groups = []


class KB3DAssemblyScanner:
    """
    Scans KB3D assembly USD files to extract instance and transform data
    """

    def __init__(self, production_assembly_path: Path):
        """
        Initialize scanner with production assembly path

        Args:
            production_assembly_path: Path to production assembly USD file
        """
        self.production_path = Path(production_assembly_path)
        self.stage = None
        self.instances = []
        self.metadata = None

    def scan(self) -> Tuple[AssemblyMetadata, List[InstanceData]]:
        """
        Scan the production assembly and extract all data

        Returns:
            Tuple of (AssemblyMetadata, List[InstanceData])
        """
        if not self.production_path.exists():
            raise FileNotFoundError(f"Assembly file not found: {self.production_path}")

        # Open USD stage
        self.stage = Usd.Stage.Open(str(self.production_path))
        if not self.stage:
            raise RuntimeError(f"Failed to open USD stage: {self.production_path}")

        # Get default prim (assembly root)
        root_prim = self.stage.GetDefaultPrim()
        if not root_prim:
            raise RuntimeError("No default prim found in assembly")

        # Extract metadata
        self.metadata = self._extract_metadata(root_prim)

        # Extract instances recursively
        self.instances = self._extract_instances_recursive(root_prim)
        self.metadata.total_instances = len(self.instances)

        return self.metadata, self.instances

    def _extract_metadata(self, prim: Usd.Prim) -> AssemblyMetadata:
        """Extract assembly-level metadata"""
        assembly_name = prim.GetName()

        # Extract extent hint
        extent_hint = None
        extent_attr = prim.GetAttribute('extentsHint')
        if extent_attr and extent_attr.IsValid():
            extent_data = extent_attr.Get()
            if extent_data and len(extent_data) >= 2:
                extent_hint = (
                    tuple(extent_data[0]),
                    tuple(extent_data[1])
                )

        # Extract default variant
        default_variant = "png1k"
        vset = prim.GetVariantSet('texture_variant')
        if vset:
            default_variant = vset.GetVariantSelection()

        return AssemblyMetadata(
            assembly_name=assembly_name,
            extent_hint=extent_hint,
            default_variant=default_variant
        )

    def _extract_instances_recursive(self, prim: Usd.Prim, group_name: Optional[str] = None) -> List[InstanceData]:
        """Recursively extract instances from prim hierarchy"""
        instances = []

        for child in prim.GetChildren():
            # Check if this is a group/scope
            kind = Usd.ModelAPI(child).GetKind()

            if kind == 'group':
                # Recurse into group
                group_instances = self._extract_instances_recursive(child, child.GetName())
                instances.extend(group_instances)
                if child.GetName() not in self.metadata.groups:
                    self.metadata.groups.append(child.GetName())

            elif kind == 'component' or child.GetTypeName() == 'Xform':
                # Extract instance data
                instance = self._extract_instance_data(child, group_name)
                if instance:
                    instances.append(instance)

        return instances

    def _extract_instance_data(self, prim: Usd.Prim, group_name: Optional[str]) -> Optional[InstanceData]:
        """Extract data from a single instance prim"""
        instance_name = prim.GetName()

        # Get reference path
        ref_path = None
        prim_stack = prim.GetPrimStack()
        for spec in prim_stack:
            if spec.referenceList:
                refs = spec.referenceList.GetAddedOrExplicitItems()
                if refs:
                    ref_path = refs[0].assetPath

        if not ref_path:
            return None

        # Extract source part name from reference path
        source_part_name = self._extract_source_part_name(ref_path, instance_name)

        # Extract transform
        transform = self._extract_transform(prim)

        # Check if instanceable
        instanceable = prim.IsInstanceable()

        # Get kind
        kind = Usd.ModelAPI(prim).GetKind()

        return InstanceData(
            instance_name=instance_name,
            source_part_name=source_part_name,
            referenced_model_path=ref_path,
            transform=transform,
            instanceable=instanceable,
            group_name=group_name,
            kind=kind
        )

    def _extract_transform(self, prim: Usd.Prim) -> Optional[TransformData]:
        """Extract transform operations from prim"""
        xformable = UsdGeom.Xformable(prim)
        if not xformable:
            return None

        transform_data = TransformData()
        xform_ops = xformable.GetOrderedXformOps()

        for op in xform_ops:
            op_type = op.GetOpType()
            value = op.Get()

            if not value:
                continue

            if op_type == UsdGeom.XformOp.TypeTranslate:
                transform_data.translate = tuple(value)

            elif op_type == UsdGeom.XformOp.TypeRotateXYZ:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "XYZ"

            elif op_type == UsdGeom.XformOp.TypeRotateXZY:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "XZY"

            elif op_type == UsdGeom.XformOp.TypeRotateYXZ:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "YXZ"

            elif op_type == UsdGeom.XformOp.TypeRotateYZX:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "YZX"

            elif op_type == UsdGeom.XformOp.TypeRotateZXY:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "ZXY"

            elif op_type == UsdGeom.XformOp.TypeRotateZYX:
                transform_data.rotate = tuple(value)
                transform_data.rotate_order = "ZYX"

            elif op_type == UsdGeom.XformOp.TypeScale:
                transform_data.scale = tuple(value)

        # Only return if at least one transform exists
        if any([transform_data.translate, transform_data.rotate, transform_data.scale]):
            return transform_data

        return None

    def _extract_source_part_name(self, ref_path: str, instance_name: str) -> str:
        """
        Extract source part name from reference path or instance name

        Examples:
            ref_path: "../KB3D_MTM_PropSolarPanel_A/KB3D_MTM_PropSolarPanel_A.usd"
            -> "PropSolarPanel_A"

            instance_name: "KB3D_MTM_BldgLgCommsArray_A_1LPlatform_001"
            -> "1LPlatform"
        """
        # Try to extract from reference path first
        if ref_path:
            # Get filename without extension
            filename = Path(ref_path).stem
            # Remove KB3D_MTM_ prefix if present
            if filename.startswith("KB3D_MTM_"):
                return filename[9:]  # Remove "KB3D_MTM_"

        # Fall back to instance name pattern matching
        # Remove assembly prefix and instance suffix
        # Pattern: AssemblyName_PartName_001
        parts = instance_name.split('_')

        # Remove numeric suffix if present
        if parts and parts[-1].isdigit():
            parts = parts[:-1]

        # Remove common assembly prefixes
        if len(parts) > 4:
            # Assume format: KB3D_MTM_BldgLgCommsArray_A_PartName
            return '_'.join(parts[4:])

        return instance_name

    def save_mapping(self, output_path: Path):
        """Save extracted data to JSON mapping file"""
        mapping_data = {
            'metadata': asdict(self.metadata),
            'instances': [inst.to_dict() for inst in self.instances]
        }

        with open(output_path, 'w') as f:
            json.dump(mapping_data, f, indent=2)

        print(f"✓ Saved mapping to: {output_path}")
        print(f"  - Assembly: {self.metadata.assembly_name}")
        print(f"  - Instances: {self.metadata.total_instances}")
        print(f"  - Groups: {len(self.metadata.groups)}")


class KB3DSourcePartScanner:
    """
    Scans source part folders to catalog available components
    """

    def __init__(self, source_parts_dir: Path):
        """
        Initialize scanner with source parts directory

        Args:
            source_parts_dir: Path to directory containing part folders
        """
        self.source_dir = Path(source_parts_dir)
        self.parts = {}

    def scan(self) -> Dict[str, Dict]:
        """
        Scan source directory for part folders

        Returns:
            Dict mapping part name to part info
        """
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        for part_folder in self.source_dir.iterdir():
            if not part_folder.is_dir():
                continue

            part_name = part_folder.name
            usd_file = part_folder / f"{part_name}.usd"

            if usd_file.exists():
                part_info = self._analyze_part(usd_file, part_folder)
                # Extract clean part name (remove assembly prefix)
                clean_name = self._extract_clean_name(part_name)
                self.parts[clean_name] = part_info

        print(f"✓ Found {len(self.parts)} source parts")
        return self.parts

    def _extract_clean_name(self, full_name: str) -> str:
        """
        Extract clean part name from full folder name

        Example:
            "KB3D_MTM_BldgLgCommsArray_A_1LPlatform" -> "1LPlatform"
        """
        parts = full_name.split('_')
        if len(parts) > 4 and parts[0] == "KB3D":
            return '_'.join(parts[4:])
        return full_name

    def _analyze_part(self, usd_file: Path, part_folder: Path) -> Dict:
        """Analyze a single part and extract info"""
        part_info = {
            'usd_path': str(usd_file),
            'folder': str(part_folder),
            'has_payload': (part_folder / "payload.usd").exists(),
            'has_geo': (part_folder / "geo.usdc").exists() or (part_folder / "geo.usd").exists(),
            'has_mtl': (part_folder / "mtl.usd").exists(),
            'has_thumbnail': (part_folder / f"{part_folder.name}.png").exists(),
        }

        # Try to open USD and get extent
        try:
            stage = Usd.Stage.Open(str(usd_file))
            if stage:
                default_prim = stage.GetDefaultPrim()
                if default_prim:
                    extent_attr = default_prim.GetAttribute('extentsHint')
                    if extent_attr and extent_attr.IsValid():
                        extent_data = extent_attr.Get()
                        if extent_data and len(extent_data) >= 2:
                            part_info['extent'] = {
                                'min': tuple(extent_data[0]),
                                'max': tuple(extent_data[1])
                            }
        except Exception as e:
            print(f"Warning: Could not analyze {usd_file}: {e}")

        return part_info

    def save_catalog(self, output_path: Path):
        """Save parts catalog to JSON"""
        with open(output_path, 'w') as f:
            json.dump(self.parts, f, indent=2)

        print(f"✓ Saved parts catalog to: {output_path}")


class KB3DAssemblyReconstructor:
    """
    Reconstructs production assembly from source parts using mapping data
    """

    def __init__(self, mapping_data: Dict, source_parts_catalog: Dict):
        """
        Initialize reconstructor

        Args:
            mapping_data: Loaded from JSON (output of KB3DAssemblyScanner)
            source_parts_catalog: Loaded from JSON (output of KB3DSourcePartScanner)
        """
        self.mapping = mapping_data
        self.catalog = source_parts_catalog
        self.metadata = AssemblyMetadata(**mapping_data['metadata'])

    def reconstruct(self, output_path: Path, relative_parts_path: str = "../../parts"):
        """
        Reconstruct assembly USD from mapping data

        Args:
            output_path: Where to save the reconstructed assembly USD
            relative_parts_path: Relative path from assembly to source parts directory
        """
        print(f"Reconstructing assembly: {self.metadata.assembly_name}")

        # Create new stage
        stage = Usd.Stage.CreateNew(str(output_path))
        stage.SetMetadata('metersPerUnit', 1.0)
        stage.SetMetadata('upAxis', 'Y')

        # Create assembly root
        asm_prim = stage.DefinePrim(f"/{self.metadata.assembly_name}", 'Xform')
        stage.SetDefaultPrim(asm_prim)

        # Set kind
        Usd.ModelAPI(asm_prim).SetKind('assembly')

        # Apply GeomModelAPI
        UsdGeom.ModelAPI.Apply(asm_prim)

        # Set extent hint if available
        if self.metadata.extent_hint:
            asm_prim.CreateAttribute('extentsHint', Sdf.ValueTypeNames.Float3Array).Set([
                Gf.Vec3f(*self.metadata.extent_hint[0]),
                Gf.Vec3f(*self.metadata.extent_hint[1])
            ])

        # Create variant set
        vset = asm_prim.GetVariantSets().AddVariantSet('texture_variant')
        vset.SetVariantSelection(self.metadata.default_variant)

        # Organize instances by group
        grouped_instances = {}
        for inst_data in self.mapping['instances']:
            inst = InstanceData(**inst_data)
            if inst.transform:
                inst.transform = TransformData(**inst_data['transform'])

            group = inst.group_name or '__root__'
            if group not in grouped_instances:
                grouped_instances[group] = []
            grouped_instances[group].append(inst)

        # Create instances
        for group_name, instances in grouped_instances.items():
            if group_name == '__root__':
                parent_prim = asm_prim
            else:
                # Create group scope
                group_prim = stage.DefinePrim(f"{asm_prim.GetPath()}/{group_name}", 'Scope')
                Usd.ModelAPI(group_prim).SetKind('group')
                parent_prim = group_prim

            # Add each instance
            for inst in instances:
                self._create_instance(stage, parent_prim, inst, relative_parts_path)

        # Save stage
        stage.GetRootLayer().Save()
        print(f"✓ Reconstructed assembly saved to: {output_path}")
        print(f"  - Instances: {self.metadata.total_instances}")
        print(f"  - Groups: {len(self.metadata.groups)}")

    def _create_instance(self, stage: Usd.Stage, parent: Usd.Prim,
                        inst: InstanceData, parts_path: str):
        """Create a single instance in the assembly"""
        inst_prim = stage.DefinePrim(f"{parent.GetPath()}/{inst.instance_name}", 'Xform')

        # Set instanceable
        inst_prim.SetInstanceable(inst.instanceable)

        # Set kind
        Usd.ModelAPI(inst_prim).SetKind(inst.kind)

        # Find matching source part
        part_info = self.catalog.get(inst.source_part_name)

        if part_info:
            # Reference source part
            part_usd = part_info['usd_path']
            # Convert to relative path
            rel_path = f"{parts_path}/{Path(part_usd).parent.name}/{Path(part_usd).name}"
            inst_prim.GetReferences().AddReference(rel_path)
        else:
            print(f"  Warning: Source part not found for '{inst.source_part_name}', using reference path")
            # Fall back to original reference path
            if inst.referenced_model_path:
                inst_prim.GetReferences().AddReference(inst.referenced_model_path)

        # Apply transform
        if inst.transform:
            xformable = UsdGeom.Xformable(inst_prim)

            if inst.transform.translate:
                xformable.AddTranslateOp().Set(Gf.Vec3d(*inst.transform.translate))

            if inst.transform.rotate:
                # Add rotation based on order
                order = inst.transform.rotate_order
                if order == "XYZ":
                    xformable.AddRotateXYZOp().Set(Gf.Vec3f(*inst.transform.rotate))
                elif order == "XZY":
                    xformable.AddRotateXZYOp().Set(Gf.Vec3f(*inst.transform.rotate))
                elif order == "YXZ":
                    xformable.AddRotateYXZOp().Set(Gf.Vec3f(*inst.transform.rotate))
                elif order == "YZX":
                    xformable.AddRotateYZXOp().Set(Gf.Vec3f(*inst.transform.rotate))
                elif order == "ZXY":
                    xformable.AddRotateZXYOp().Set(Gf.Vec3f(*inst.transform.rotate))
                elif order == "ZYX":
                    xformable.AddRotateZYXOp().Set(Gf.Vec3f(*inst.transform.rotate))

            if inst.transform.scale:
                xformable.AddScaleOp().Set(Gf.Vec3f(*inst.transform.scale))


# Convenience functions

def scan_assembly(production_assembly_path: Path, output_mapping_path: Optional[Path] = None) -> Tuple[AssemblyMetadata, List[InstanceData]]:
    """
    Quick function to scan an assembly and optionally save mapping

    Args:
        production_assembly_path: Path to production assembly USD
        output_mapping_path: Optional path to save JSON mapping

    Returns:
        Tuple of (metadata, instances)
    """
    scanner = KB3DAssemblyScanner(production_assembly_path)
    metadata, instances = scanner.scan()

    if output_mapping_path:
        scanner.save_mapping(output_mapping_path)

    return metadata, instances


def scan_source_parts(source_parts_dir: Path, output_catalog_path: Optional[Path] = None) -> Dict:
    """
    Quick function to scan source parts and optionally save catalog

    Args:
        source_parts_dir: Path to directory containing part folders
        output_catalog_path: Optional path to save JSON catalog

    Returns:
        Parts catalog dict
    """
    scanner = KB3DSourcePartScanner(source_parts_dir)
    parts = scanner.scan()

    if output_catalog_path:
        scanner.save_catalog(output_catalog_path)

    return parts


def reconstruct_from_files(mapping_json: Path, catalog_json: Path,
                          output_usd: Path, relative_parts_path: str = "../../parts"):
    """
    Quick function to reconstruct assembly from JSON files

    Args:
        mapping_json: Path to mapping JSON file
        catalog_json: Path to catalog JSON file
        output_usd: Where to save reconstructed USD
        relative_parts_path: Relative path to source parts
    """
    # Load JSON files
    with open(mapping_json) as f:
        mapping = json.load(f)

    with open(catalog_json) as f:
        catalog = json.load(f)

    # Reconstruct
    reconstructor = KB3DAssemblyReconstructor(mapping, catalog)
    reconstructor.reconstruct(output_usd, relative_parts_path)
