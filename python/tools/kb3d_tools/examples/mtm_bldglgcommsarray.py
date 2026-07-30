#!/usr/bin/env hython
"""
Example: build a KB3D-style assembly from part folders (Mission to Minerva).

Set environment variables before running, or edit the defaults below.
"""

import os

from tools.kb3d_tools.kb3d_assembly_builder import build_kb3d_assembly

PARTS = os.environ.get(
    "KB3D_PARTS_SOURCE",
    "/path/to/geo/KB3D_MTM_BldgLgCommsArray_A/KB3D_MTM_BldgLgCommsArray_A",
)
MERGED_BGEO = os.environ.get(
    "KB3D_MERGED_BGEO",
    "/path/to/geo/KB3D_MTM_BldgLgCommsArray_A/KB3D_MTM_BldgLgCommsArray_A.bgeo.sc",
)
MODELS_BASE = os.environ.get("KB3D_MODELS_BASE", "/path/to/Models")
MATERIALS = os.environ.get("KB3D_MATERIALS_FOLDER", "/path/to/Textures")
ASSEMBLY_NAME = os.environ.get("KB3D_ASSEMBLY_NAME", "KB3D_MTM_BldgLgCommsArray_A")

if __name__ == "__main__":
    assembly_usd = build_kb3d_assembly(
        parts_source_folder=PARTS,
        merged_bgeo=MERGED_BGEO,
        models_base=MODELS_BASE,
        assembly_name=ASSEMBLY_NAME,
        materials_folder=MATERIALS,
    )
    print(f"Assembly USD: {assembly_usd}")
