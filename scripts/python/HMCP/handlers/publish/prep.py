"""Publish prep — output paths and scan-to-config helpers."""

from __future__ import annotations

import os

import hou

from modules.asset_folder_scanner import scan_asset_folder
from modules.lop_helpers import find_component_output
from tools.lops_asset_builder_v3.asset_builder_config import derive_asset_name


def _expand(node: hou.Node, parm_name: str) -> str | None:
    parm = node.parm(parm_name)
    if parm is None:
        return None
    try:
        return hou.text.expandString(parm.eval())
    except Exception:
        return None


def get_build_output_paths(params: dict) -> dict:
    node = find_component_output(params.get("node_path"))
    if node is None:
        raise ValueError("No componentoutput node found — provide node_path")

    path_keys = (
        "filename",
        "lopoutput",
        "geolayer",
        "mtllayer",
        "payloadlayer",
        "extralayer",
        "manualpayloadlayer",
    )
    paths = {key: _expand(node, key) for key in path_keys}

    rop = node.node("rop") if node.node("rop") else None
    rop_paths = {}
    if rop is not None:
        rop_paths = {
            "rop_lopoutput": _expand(rop, "lopoutput"),
            "save_directory": _expand(rop, "savetodirectory_directory"),
        }

    resolved = {}
    main_file = paths.get("lopoutput")
    if main_file and paths.get("filename"):
        for key in ("geolayer", "mtllayer", "payloadlayer", "extralayer", "manualpayloadlayer"):
            layer = paths.get(key)
            if layer and main_file and paths.get("filename"):
                resolved[key] = layer

    exists = {key: bool(val and os.path.isfile(val)) for key, val in {**paths, **rop_paths}.items() if val}

    return {
        "node_path": node.path(),
        "asset_name": node.name(),
        "paths": {k: v for k, v in paths.items() if v},
        "rop_paths": {k: v for k, v in rop_paths.items() if v},
        "resolved_layers": resolved,
        "files_on_disk": exists,
    }


def scan_to_lops_config(params: dict) -> dict:
    folder_path = params.get("folder_path")
    if not folder_path:
        raise ValueError("folder_path is required")

    folder_path = hou.text.expandString(folder_path)
    geo_subfolder = params.get("geo_subfolder", "geo")
    tex_subfolder = params.get("tex_subfolder", "tex")

    scan = scan_asset_folder(folder_path, geo_subfolder, tex_subfolder)
    main_asset = scan.get("main_asset")
    main_textures = scan.get("main_textures")

    if not main_asset:
        raise ValueError(f"No main asset found in {folder_path}")

    config = {
        "main_asset_file_path": main_asset,
        "folder_textures": main_textures or folder_path,
        "asset_name": params.get("asset_name") or derive_asset_name(main_asset),
        "asset_variants": scan.get("asset_variants") or [],
        "mtl_variants": scan.get("material_variants") or [],
        "create_lookdev": bool(params.get("create_lookdev", False)),
        "create_geo_variants": bool(params.get("create_geo_variants", True)),
        "validate_materials": bool(params.get("validate_materials", True)),
    }

    return {
        "folder_path": folder_path,
        "scan_summary": {
            "main_asset": main_asset,
            "main_textures": main_textures,
            "variant_count": len(config["asset_variants"]),
            "material_variant_count": len(config["mtl_variants"]),
            "errors": scan.get("errors") or [],
        },
        "config": config,
    }
