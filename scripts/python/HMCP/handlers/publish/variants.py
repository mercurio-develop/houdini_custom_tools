"""Variant export and manifest tools for HMCP."""

from __future__ import annotations

import json
import os

import hou

from modules.usd_solaris_utils import get_stage_from_lop, increment_version_token
from modules.lop_helpers import find_component_output


def _collect_variant_sets(stage, prim_path: str) -> dict[str, list[str]]:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        prim = stage.GetDefaultPrim()
        if prim:
            prim_path = str(prim.GetPath())
        else:
            prim = stage.GetPrimAtPath("/")
            prim_path = "/"

    if not prim or not prim.IsValid():
        return {"prim_path": prim_path, "variant_sets": {}}

    result = {}
    vsets = prim.GetVariantSets()
    for name in vsets.GetNames():
        vset = vsets.GetVariantSet(name)
        result[name] = list(vset.GetVariantNames())
    return {"prim_path": prim_path, "variant_sets": result}


def list_component_variants(params: dict) -> dict:
    node = find_component_output(params.get("node_path"))
    if node is None:
        raise ValueError("No componentoutput node found")

    if params.get("cook_first", True):
        node.cook(force=True)

    stage = node.stage()
    if stage is None:
        raise ValueError("No stage on component output")

    prim_path = params.get("prim_path")
    if not prim_path:
        default = stage.GetDefaultPrim()
        prim_path = str(default.GetPath()) if default else "/"

    data = _collect_variant_sets(stage, prim_path)
    return {
        "node_path": node.path(),
        "asset_name": node.name(),
        **data,
    }


def _apply_variants(stage, prim_path: str, selections: dict[str, str]) -> None:
    from pxr import Usd

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        raise ValueError(f"Invalid prim for variants: {prim_path}")

    with Usd.EditContext(stage, stage.GetSessionLayer()):
        vsets = prim.GetVariantSets()
        for vset_name, variant_name in selections.items():
            vsets.SetSelection(vset_name, variant_name)


def batch_export_variants(params: dict) -> dict:
    """Export USD files for geo × material variant combinations."""
    node = find_component_output(params.get("node_path"))
    if node is None:
        raise ValueError("No componentoutput node found")

    output_dir = params.get("output_dir") or params.get("output_directory")
    if not output_dir:
        raise ValueError("output_dir is required")

    output_dir = hou.text.expandString(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if params.get("cook_first", True):
        node.cook(force=True)

    stage = node.stage()
    if stage is None:
        raise ValueError("No stage on component output")

    prim_path = params.get("prim_path")
    if not prim_path:
        default = stage.GetDefaultPrim()
        prim_path = str(default.GetPath()) if default else "/"

    variant_info = _collect_variant_sets(stage, prim_path)
    all_sets = variant_info.get("variant_sets") or {}

    geo_set = params.get("geo_variant_set") or params.get("geo_vset")
    mtl_set = params.get("mtl_variant_set") or params.get("mtl_vset")

    if not geo_set and len(all_sets) >= 1:
        geo_set = next(iter(all_sets.keys()))
    if not mtl_set and len(all_sets) >= 2:
        keys = list(all_sets.keys())
        mtl_set = keys[1] if keys[0] == geo_set else keys[0]

    geo_variants = params.get("geo_variants") or (all_sets.get(geo_set) if geo_set else [None])
    mtl_variants = params.get("mtl_variants") or (all_sets.get(mtl_set) if mtl_set else [None])

    if geo_variants is None:
        geo_variants = [None]
    if mtl_variants is None:
        mtl_variants = [None]

    asset_name = params.get("asset_name") or node.name()
    version = params.get("version", "v001")
    exports = []

    for geo in geo_variants:
        for mtl in mtl_variants:
            selections = {}
            if geo_set and geo:
                selections[geo_set] = geo
            if mtl_set and mtl:
                selections[mtl_set] = mtl

            if selections:
                _apply_variants(stage, prim_path, selections)
                node.cook(force=True)
                stage = node.stage()

            geo_token = geo or "default"
            mtl_token = mtl or "default"
            filename = f"{asset_name}_{geo_token}_{mtl_token}_{version}.usd"
            filename = filename.replace(" ", "_")
            out_path = os.path.join(output_dir, filename)

            stage.Export(out_path)
            exports.append({
                "output_path": out_path,
                "geo_variant": geo,
                "mtl_variant": mtl,
                "selections": selections,
                "exists": os.path.isfile(out_path),
            })

    manifest_path = os.path.join(output_dir, f"{asset_name}_variant_manifest.json")
    manifest = {
        "asset_name": asset_name,
        "node_path": node.path(),
        "prim_path": prim_path,
        "version": version,
        "export_count": len(exports),
        "exports": exports,
    }
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    return {
        "node_path": node.path(),
        "output_dir": output_dir,
        "manifest_path": manifest_path,
        "export_count": len(exports),
        "exports": exports,
    }


def get_variant_manifest(params: dict) -> dict:
    manifest_path = params.get("manifest_path")
    if manifest_path:
        manifest_path = hou.text.expandString(manifest_path)
        if not os.path.isfile(manifest_path):
            raise ValueError(f"Manifest not found: {manifest_path}")
        with open(manifest_path, encoding="utf-8") as handle:
            return json.load(handle)

    result = batch_export_variants(params)
    with open(result["manifest_path"], encoding="utf-8") as handle:
        return json.load(handle)
