"""Asset library discovery, search, and reference import for HMCP."""

from __future__ import annotations

import os
from collections import defaultdict

import hou

from integrations.usd_discovery import default_discovery_config, discover_usd_files
from modules.asset_folder_scanner import scan_asset_folder
from modules.usd_reference_importer import import_scanned_assets


def _hit_to_dict(hit) -> dict:
    return {
        "usd_path": hit.usd_path,
        "asset_name": hit.asset_name,
        "folder_path": hit.folder_path,
        "selection_reason": hit.selection_reason,
        "file_size": hit.file_size,
        "kb3d_asset_code": hit.kb3d_asset_code,
    }


def discover_usd_assets(params: dict) -> dict:
    root = params.get("root_path") or params.get("folder_path")
    if not root:
        raise ValueError("root_path is required")

    root = hou.text.expandString(root)
    cfg = default_discovery_config(
        mode=params.get("mode", "primary"),
        recursive=params.get("recursive", True),
        max_items=int(params.get("max_items", 200)),
    )
    if params.get("include_globs"):
        cfg.include_globs = list(params["include_globs"])
    if params.get("exclude_globs"):
        cfg.exclude_globs = list(params["exclude_globs"])

    hits = discover_usd_files(root, cfg)
    return {
        "root_path": root,
        "count": len(hits),
        "assets": [_hit_to_dict(h) for h in hits],
    }


def search_assets(params: dict) -> dict:
    root = params.get("root_path") or params.get("library_path")
    query = (params.get("query") or params.get("search") or "").strip().lower()
    if not root:
        raise ValueError("root_path is required")

    root = hou.text.expandString(root)
    max_results = int(params.get("max_results", 50))
    cfg = default_discovery_config(mode="all", recursive=True, max_items=0)

    hits = discover_usd_files(root, cfg)
    if query:
        filtered = []
        for hit in hits:
            haystack = f"{hit.asset_name} {hit.usd_path} {hit.folder_path}".lower()
            if query in haystack or (hit.kb3d_asset_code and query in hit.kb3d_asset_code.lower()):
                filtered.append(hit)
        hits = filtered

    hits = hits[:max_results]
    return {
        "root_path": root,
        "query": query or None,
        "count": len(hits),
        "assets": [_hit_to_dict(h) for h in hits],
    }


def get_asset_categories(params: dict) -> dict:
    root = params.get("root_path") or params.get("library_path")
    if not root:
        raise ValueError("root_path is required")

    root = hou.text.expandString(root)
    group_by = params.get("group_by", "parent_folder")
    cfg = default_discovery_config(mode="primary", recursive=True, max_items=0)
    hits = discover_usd_files(root, cfg)

    buckets: dict[str, list] = defaultdict(list)
    for hit in hits:
        if group_by == "kb3d_code" and hit.kb3d_asset_code:
            key = hit.kb3d_asset_code
        elif group_by == "extension":
            key = os.path.splitext(hit.usd_path)[1].lower() or ".usd"
        else:
            key = os.path.basename(hit.folder_path) or hit.asset_name
        buckets[key].append(_hit_to_dict(hit))

    categories = [
        {"name": name, "count": len(items), "assets": items[: int(params.get("max_per_category", 20))]}
        for name, items in sorted(buckets.items(), key=lambda x: x[0].lower())
    ]
    return {"root_path": root, "group_by": group_by, "category_count": len(categories), "categories": categories}


def import_asset(params: dict) -> dict:
    """Scan a folder and import geometry as USD references in /stage."""
    folder_path = params.get("folder_path")
    if not folder_path:
        raise ValueError("folder_path is required")

    folder_path = hou.text.expandString(folder_path)
    geo_subfolder = params.get("geo_subfolder", "geo")
    tex_subfolder = params.get("tex_subfolder", "tex")
    stage_name = params.get("stage_name", "hmcp_asset_import")
    spacing = float(params.get("spacing", 5.0))
    layout_type = params.get("layout_type", "grid")

    if params.get("scan_result"):
        scan_result = params["scan_result"]
    else:
        scan_result = scan_asset_folder(folder_path, geo_subfolder, tex_subfolder)

    merge_node = import_scanned_assets(
        scan_result,
        stage_name=stage_name,
        spacing=spacing,
        layout_type=layout_type,
    )
    if merge_node is None:
        raise RuntimeError("Import failed — no geometry found in scan result")

    return {
        "folder_path": folder_path,
        "merge_node": merge_node.path(),
        "geo_file_count": len(scan_result.get("geometry_files", {})),
        "main_asset": scan_result.get("main_asset"),
        "layout_type": layout_type,
    }
