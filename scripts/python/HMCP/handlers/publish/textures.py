"""Texture path repair and material manifest comparison for HMCP."""

from __future__ import annotations

import os

import hou

from modules.texture_path_repair import compare_texture_manifests, repair_texture_map
from tools.lops_asset_builder_v3.texture_scan_utils import resolve_texture_search_roots, walk_texture_dirs


def repair_texture_paths(params: dict) -> dict:
    """
    Repair broken texture paths from analyze_usd_materials output or a LOP node.

    Searches folder_textures / search_roots for matching basenames.
    """
    node_path = params.get("node_path")
    textures = params.get("textures")
    folder_textures = params.get("folder_textures") or params.get("texture_folder")

    if not textures and node_path:
        from HMCP.handlers.usd.materials import analyze_usd_materials

        analysis = analyze_usd_materials({
            "node_path": node_path,
            "cook_first": params.get("cook_first", True),
            "max_materials": params.get("max_materials", 50),
        })
        merged = {}
        for mat in analysis.get("materials") or []:
            merged.update(mat.get("textures") or {})
        textures = merged

    if not textures:
        raise ValueError("Provide textures dict or node_path")

    search_roots = []
    if folder_textures:
        folder_textures = hou.text.expandString(folder_textures)
        search_roots.extend(resolve_texture_search_roots(folder_textures))
        search_roots.append(folder_textures)
    for root in params.get("search_roots") or []:
        search_roots.append(hou.text.expandString(root))

    copy_to = params.get("copy_to")
    if copy_to:
        copy_to = hou.text.expandString(copy_to)

    result = repair_texture_map(textures, search_roots, copy_to=copy_to)
    return result


def compare_material_manifests(params: dict) -> dict:
    """Compare folder texture scan vs USD material texture extraction."""
    node_path = params.get("node_path")
    folder_textures = params.get("folder_textures")
    if not node_path or not folder_textures:
        raise ValueError("node_path and folder_textures are required")

    folder_textures = hou.text.expandString(folder_textures)
    from HMCP.handlers.usd.materials import analyze_usd_materials

    analysis = analyze_usd_materials({
        "node_path": node_path,
        "cook_first": params.get("cook_first", True),
        "naming_strategy": params.get("naming_strategy", "usd_prim"),
    })

    expected = _scan_folder_textures(folder_textures, params.get("material_name"))
    usd_textures = {}
    for mat in analysis.get("materials") or []:
        if params.get("material_name") and mat.get("display_name") != params.get("material_name"):
            if mat.get("name") != params.get("material_name"):
                continue
        usd_textures.update(mat.get("textures") or {})

    comparison = compare_texture_manifests(expected, usd_textures)
    return {
        "node_path": node_path,
        "folder_textures": folder_textures,
        "material_count": analysis.get("material_count"),
        **comparison,
    }


def _scan_folder_textures(folder_textures: str, material_filter: str | None = None) -> dict[str, str]:
    from tools.material_tools.TexToMtlX_V2.tex_to_mtlx import TextureFolderScanner

    scanner = TextureFolderScanner()
    found: dict[str, str] = {}

    for search_root in resolve_texture_search_roots(folder_textures):
        if not os.path.isdir(search_root):
            continue
        for root, _dirs, _files in walk_texture_dirs(search_root):
            if not scanner.folder_with_textures(root):
                continue
            details = scanner.get_texture_details(root)
            if not isinstance(details, dict):
                continue
            for mat_name, info in details.items():
                if material_filter and mat_name != material_filter:
                    continue
                folder = info.get("FOLDER_PATH", root)
                for fname in os.listdir(folder):
                    lower = fname.lower()
                    channel = None
                    if "normal" in lower or "nrm" in lower:
                        channel = "normal"
                    elif "rough" in lower:
                        channel = "roughness"
                    elif "metal" in lower:
                        channel = "metallic"
                    elif "albedo" in lower or "diffuse" in lower or "basecolor" in lower:
                        channel = "base_color"
                    if channel and channel not in found:
                        found[channel] = os.path.join(folder, fname)
    return found
