"""
Transform Extractor - Extract transform data from FBX/BGEO before separation

CRITICAL: Run this BEFORE separating merged assets into individual parts
to preserve original assembly transforms.

Usage:
    from tools.kb3d_tools.core.transform_extractor import extract_transforms_from_geometry

    transforms = extract_transforms_from_geometry(
        geometry_file="/path/to/merged.fbx",
        output_json="/path/to/transforms.json",
        identify_parts_by="material"
    )
"""

import hou
import json
import os
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


def extract_transforms_from_geometry(
    geometry_file: str,
    output_json: Optional[str] = None,
    identify_parts_by: str = "material",  # "material", "group", "name", "attribute"
    attribute_name: str = "part_name",
    reference_origin: str = "world"  # "world", "local", "centroid"
) -> Dict:
    """
    Extract part transforms from merged geometry file (FBX, BGEO, USD).

    This is the CRITICAL step before separation - preserves assembly transforms!

    Args:
        geometry_file: Path to merged geometry file
        output_json: Optional path to save transforms as JSON
        identify_parts_by: How to identify individual parts
            - "material": Group by shop_materialpath attribute
            - "group": Group by primitive groups
            - "name": Group by name attribute
            - "attribute": Group by custom attribute
        attribute_name: Attribute name if identify_parts_by="attribute"
        reference_origin: Transform reference point
            - "world": World space transforms
            - "local": Local space transforms
            - "centroid": Relative to part centroid

    Returns:
        Dict mapping part names to transform data:
        {
            "PartA": {
                "translate": [x, y, z],
                "rotate": [rx, ry, rz],
                "scale": [sx, sy, sz],
                "bounds": {"min": [x,y,z], "max": [x,y,z]},
                "centroid": [x, y, z],
                "primitive_count": N
            },
            ...
        }
    """

    print(f"\n{'='*70}")
    print(f"Transform Extractor")
    print(f"{'='*70}")
    print(f"File: {geometry_file}")
    print(f"Identify by: {identify_parts_by}")
    print(f"Reference: {reference_origin}")
    print()

    # Load geometry
    geo = _load_geometry(geometry_file)
    if not geo:
        print("ERROR: Could not load geometry")
        return {}

    print(f"Loaded: {geo.intrinsicValue('primitivecount')} primitives")
    print()

    # Group primitives by part
    print("Grouping primitives by parts...")
    parts = _group_primitives_by_part(
        geo,
        identify_parts_by,
        attribute_name
    )

    if not parts:
        print("ERROR: No parts identified")
        return {}

    print(f"Found {len(parts)} parts:")
    for part_name in sorted(parts.keys()):
        print(f"  - {part_name}: {len(parts[part_name])} prims")
    print()

    # Extract transforms for each part
    print("Extracting transforms...")
    transforms = {}

    for part_name, prims in parts.items():
        xform = _calculate_part_transform(
            prims,
            part_name,
            reference_origin
        )
        transforms[part_name] = xform

        print(f"  {part_name}:")
        print(f"    Centroid: ({xform['centroid'][0]:.3f}, {xform['centroid'][1]:.3f}, {xform['centroid'][2]:.3f})")
        print(f"    Size: ({xform['size'][0]:.3f}, {xform['size'][1]:.3f}, {xform['size'][2]:.3f})")

    print()

    # Save to JSON if requested
    if output_json:
        _save_transforms_json(transforms, output_json)
        print(f"Saved transforms to: {output_json}")

    print(f"{'='*70}")
    print(f"Transform extraction complete!")
    print(f"{'='*70}\n")

    return transforms


def _load_geometry(geometry_file: str) -> Optional[hou.Geometry]:
    """Load geometry from file (FBX, BGEO, USD)."""

    # Create temporary geometry node
    obj = hou.node('/obj')
    temp_geo = obj.createNode('geo', 'temp_transform_extract', run_init_scripts=False)

    try:
        # Determine file type (handle .bgeo.sc specially)
        if geometry_file.endswith('.bgeo.sc'):
            ext = '.bgeo.sc'
        else:
            ext = os.path.splitext(geometry_file)[1].lower()

        if ext in ['.fbx']:
            # Load FBX via file SOP
            file_node = temp_geo.createNode('file', 'file1')
            file_node.parm('file').set(geometry_file)

        elif ext in ['.bgeo', '.bgeo.sc', '.geo', '.sc']:
            # Load BGEO
            file_node = temp_geo.createNode('file', 'file1')
            file_node.parm('file').set(geometry_file)

        elif ext in ['.usd', '.usda', '.usdc']:
            # Load USD via SOP import
            # This requires converting USD → SOP
            # For now, use file SOP (may need LOPS → SOP workflow)
            file_node = temp_geo.createNode('file', 'file1')
            file_node.parm('file').set(geometry_file)

        else:
            print(f"WARNING: Unknown file type: {ext}")
            return None

        file_node.cook(force=True)
        geo = file_node.geometry()

        # Store temp_geo reference so it doesn't get destroyed
        geo._temp_geo_node = temp_geo

        return geo

    except Exception as e:
        print(f"ERROR loading geometry: {e}")
        temp_geo.destroy()
        return None


def _group_primitives_by_part(
    geo: hou.Geometry,
    identify_by: str,
    attribute_name: str = "part_name"
) -> Dict[str, List]:
    """Group primitives by part based on identification method."""

    parts = defaultdict(list)

    if identify_by == "material":
        # Group by shop_materialpath attribute
        mat_attrib = geo.findPrimAttrib('shop_materialpath')
        if not mat_attrib:
            print("WARNING: No shop_materialpath attribute found")
            print("Available attributes:")
            for attrib in geo.primAttribs():
                print(f"  - {attrib.name()}")
            return {}

        for prim in geo.prims():
            mat_path = prim.attribValue('shop_materialpath')
            if mat_path:
                # Extract material name from path
                # e.g. "/shop/Material_Wings" → "Wings"
                mat_name = os.path.basename(mat_path)
                parts[mat_name].append(prim)

    elif identify_by == "group":
        # Group by primitive groups
        for group in geo.primGroups():
            group_name = group.name()
            parts[group_name] = list(group.prims())

    elif identify_by == "name":
        # Group by name attribute
        name_attrib = geo.findPrimAttrib('name')
        if not name_attrib:
            print("WARNING: No 'name' attribute found")
            return {}

        for prim in geo.prims():
            name = prim.attribValue('name')
            if name:
                parts[name].append(prim)

    elif identify_by == "attribute":
        # Group by custom attribute
        custom_attrib = geo.findPrimAttrib(attribute_name)
        if not custom_attrib:
            print(f"WARNING: No '{attribute_name}' attribute found")
            return {}

        for prim in geo.prims():
            value = prim.attribValue(attribute_name)
            if value:
                parts[value].append(prim)

    else:
        print(f"ERROR: Unknown identify_by method: {identify_by}")
        return {}

    return dict(parts)


def _calculate_part_transform(
    prims: List,
    part_name: str,
    reference_origin: str
) -> Dict:
    """Calculate transform data for a group of primitives."""

    # Calculate bounding box
    bbox = hou.BoundingBox()
    for prim in prims:
        bbox.enlargeToContain(prim.boundingBox())

    # Get bounds
    min_vec = bbox.minvec()
    max_vec = bbox.maxvec()
    center = bbox.center()
    size = bbox.sizevec()

    # Calculate transform based on reference origin
    if reference_origin == "world":
        # Transform relative to world origin
        translate = (center[0], center[1], center[2])

    elif reference_origin == "local":
        # Transform relative to part's local origin (centroid)
        translate = (0, 0, 0)

    elif reference_origin == "centroid":
        # Transform relative to centroid
        translate = (center[0], center[1], center[2])

    else:
        translate = (center[0], center[1], center[2])

    return {
        "translate": list(translate),
        "rotate": [0, 0, 0],  # Rotation not easily extractable from prims
        "scale": [1, 1, 1],    # Scale assumed 1
        "bounds": {
            "min": [min_vec[0], min_vec[1], min_vec[2]],
            "max": [max_vec[0], max_vec[1], max_vec[2]]
        },
        "centroid": [center[0], center[1], center[2]],
        "size": [size[0], size[1], size[2]],
        "primitive_count": len(prims),
        "reference_origin": reference_origin
    }


def _save_transforms_json(transforms: Dict, output_path: str):
    """Save transforms to JSON file."""

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Add metadata
    output_data = {
        "metadata": {
            "version": "1.0",
            "tool": "USD Library Pipeline - Transform Extractor",
            "part_count": len(transforms)
        },
        "transforms": transforms
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)


def load_transforms_json(json_path: str) -> Dict:
    """Load transforms from JSON file."""

    with open(json_path, 'r') as f:
        data = json.load(f)

    return data.get('transforms', {})


# Convenience function for your TOPs workflow
def extract_and_save(
    geometry_file: str,
    output_folder: str,
    identify_by: str = "material"
) -> str:
    """
    Extract transforms and save to default location.

    Convenience function for TOPs workflow integration.

    Returns path to saved JSON file.
    """

    # Generate output path
    base_name = os.path.splitext(os.path.basename(geometry_file))[0]
    output_json = os.path.join(output_folder, f"{base_name}_transforms.json")

    # Extract and save
    extract_transforms_from_geometry(
        geometry_file=geometry_file,
        output_json=output_json,
        identify_parts_by=identify_by
    )

    return output_json


if __name__ == "__main__":
    # Test with example file
    import sys

    if len(sys.argv) > 1:
        geometry_file = sys.argv[1]
    else:
        # Example usage
        geometry_file = "/media/tushita/TUSHITA_LINUX_DATA/assets/KitBash3D - Spaceships/KB3D_SPACESHIP_CLONE/geo/KB3D_SPS_Spaceship_C/KB3D_SPS_Spaceship_C.bgeo.sc"

    if not os.path.exists(geometry_file):
        print(f"File not found: {geometry_file}")
        sys.exit(1)

    output_folder = os.path.dirname(geometry_file)

    transforms = extract_and_save(
        geometry_file=geometry_file,
        output_folder=output_folder,
        identify_by="material"
    )

    print(f"\nTransforms saved to: {transforms}")
