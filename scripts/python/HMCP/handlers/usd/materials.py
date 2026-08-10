"""USD material import and USDZ extraction tools for HMCP."""

from __future__ import annotations

import os

import hou

from modules.misc_utils import _sanitize
from modules.usd_material_naming import allocate_safe_names
from modules.usd_solaris_utils import (
    extract_texture_map_from_material,
    extract_usdz_archive as unpack_usdz_archive,
    get_all_usd_materials,
    get_material_assignments,
    get_materials_in_binding_order,
    get_stage_from_lop,
    get_usd_root_folder,
)
from tools.houdini_lop_utils import connect, configure_assign_material, get_or_create, set_parms

OPENPBR_PORT_MAP = {
    "base_color": "base_color",
    "metallic": "base_metalness",
    "roughness": "roughness",
    "normal": "normal",
    "specular": "specular",
    "opacity": "opacity",
    "emission": "emission",
}


def extract_usdz_archive(params: dict) -> dict:
    usdz_path = params.get("usdz_path") or params.get("file_path")
    if not usdz_path:
        raise ValueError("usdz_path is required")

    usdz_path = hou.text.expandString(usdz_path)
    extract_to = params.get("extract_to")
    if extract_to:
        extract_to = hou.text.expandString(extract_to)

    root = unpack_usdz_archive(usdz_path, extract_to)
    if root is None:
        raise ValueError(f"Could not extract USDZ: {usdz_path}")

    usd_files = []
    for dirpath, _dirs, files in os.walk(root):
        for fname in files:
            if fname.lower().endswith((".usd", ".usda", ".usdc")):
                usd_files.append(os.path.join(dirpath, fname))

    return {
        "usdz_path": usdz_path,
        "extract_root": root,
        "usd_file_count": len(usd_files),
        "usd_files": usd_files[: int(params.get("max_files", 50))],
    }


def analyze_usd_materials(params: dict) -> dict:
    """Inspect USD materials, bindings, and texture maps without building LOP nodes."""
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    stage = get_stage_from_lop(node, params.get("cook_first", True))
    if stage is None:
        raise ValueError("No USD stage found")

    usd_folder = get_usd_root_folder(stage)
    assignments = get_material_assignments(stage)
    order = get_materials_in_binding_order(stage)
    strategy = params.get("naming_strategy", "usd_prim")

    materials = []
    max_materials = int(params.get("max_materials", 100))
    mat_by_path = {str(m.GetPath()): m for m in get_all_usd_materials(stage)}

    for mat_path in order[:max_materials]:
        usd_mat = mat_by_path.get(mat_path)
        if usd_mat is None:
            continue
        textures = extract_texture_map_from_material(usd_mat, usd_folder)
        materials.append({
            "material_path": mat_path,
            "name": usd_mat.GetPrim().GetName(),
            "bound_prims": assignments.get(mat_path, [])[:20],
            "bound_prim_count": len(assignments.get(mat_path, [])),
            "textures": textures,
        })

    materials = allocate_safe_names(materials, strategy, stage, mat_by_path, assignments)

    return {
        "node_path": node_path,
        "usd_folder": usd_folder,
        "naming_strategy": strategy,
        "material_count": len(materials),
        "materials": materials,
    }


def _wire_mtlx_images(subnet: hou.Node, textures: dict[str, str], engine: str = "mtlx") -> None:
    surface_type = "mtlxopen_pbr_surface" if engine == "openpbr" else "mtlxstandard_surface"
    surface = None
    for child in subnet.children():
        if child.type().name() in ("mtlxstandard_surface", "mtlxopen_pbr_surface"):
            surface = child
            break
    if surface is None:
        surface = subnet.createNode(surface_type, "surface")

    port_map = OPENPBR_PORT_MAP if engine == "openpbr" else {
        "base_color": "base_color",
        "metallic": "metallic",
        "roughness": "roughness",
        "normal": "normal",
        "specular": "specular",
        "opacity": "opacity",
        "emission": "emission",
    }

    for channel, path in textures.items():
        if not os.path.isfile(path):
            continue
        img = subnet.createNode("mtlximage", _sanitize(f"img_{channel}"))
        file_parm = img.parm("file") or img.parm("filename")
        if file_parm is not None:
            file_parm.set(path)

        target = port_map.get(channel)
        if channel == "normal":
            normal_map = subnet.createNode("mtlxnormalmap", "normal_map")
            normal_map.setInput(0, img)
            if hasattr(surface, "inputIndex"):
                try:
                    idx = surface.inputIndex("normal")
                    if idx >= 0:
                        surface.setInput(idx, normal_map)
                except Exception:
                    pass
            continue

        if target and hasattr(surface, "inputIndex"):
            try:
                idx = surface.inputIndex(target)
                if idx >= 0:
                    surface.setInput(idx, img)
            except Exception:
                pass

    subnet.layoutChildren()


def _configure_multi_assign(assign: hou.Node, bindings: list[dict], max_slots: int = 32) -> None:
    count = min(len(bindings), max_slots)
    set_parms(assign, {"nummaterials": count})
    for idx, binding in enumerate(bindings[:count], start=1):
        prims = binding.get("prims") or []
        mat_path = binding.get("material_path", "")
        set_parms(assign, {
            f"enable{idx}": 1,
            f"primpattern{idx}": " ".join(prims) if prims else "%type:Mesh",
            f"ispathexpression{idx}": 0,
            f"matspecmethod{idx}": "path",
            f"matspecpath{idx}": mat_path,
            f"bindpurpose{idx}": "full",
            f"bindstrength{idx}": "fallback",
        })


def import_usd_materials(params: dict) -> dict:
    """Rebuild USD materials as Material Library + Assign Material LOP chain."""
    node_path = params.get("node_path")
    parent_path = params.get("parent_path", "/stage")
    if not node_path:
        raise ValueError("node_path is required")

    source = hou.node(node_path)
    parent = hou.node(parent_path)
    if source is None or parent is None:
        raise ValueError("Invalid node_path or parent_path")

    engine = params.get("engine", "mtlx")
    assign_all = bool(params.get("assign_all", True))
    dry_run = bool(params.get("dry_run", False))

    analysis = analyze_usd_materials({
        "node_path": node_path,
        "cook_first": params.get("cook_first", True),
        "max_materials": params.get("max_materials", 20),
        "naming_strategy": params.get("naming_strategy", "usd_prim"),
    })
    if not analysis["materials"]:
        raise ValueError("No USD materials found to import")

    plan = []
    for entry in analysis["materials"][: int(params.get("max_materials", 20))]:
        if not entry.get("textures") and not params.get("build_empty", False):
            continue
        plan.append({
            "material_path": entry["material_path"],
            "safe_name": entry["safe_name"],
            "display_name": entry.get("display_name", entry["safe_name"]),
            "bound_prims": entry.get("bound_prims") or [],
            "textures": entry.get("textures") or {},
            "stage_material_path": f"/materials/{entry['safe_name']}",
        })

    if dry_run:
        return {
            "dry_run": True,
            "source_node": source.path(),
            "engine": engine,
            "assign_all": assign_all,
            "planned_count": len(plan),
            "plan": plan,
        }

    mat_lib = get_or_create(parent, "materiallibrary", params.get("library_name", "hmcp_imported_materials"))
    assign = get_or_create(parent, "assignmaterial", params.get("assign_name", "hmcp_assign_imported"))

    connect(assign, 0, mat_lib)
    if params.get("wire_source", True):
        connect(mat_lib, 0, source)

    built = []
    for item in plan:
        mat_subnet = mat_lib.createNode("subnet", item["safe_name"])
        _wire_mtlx_images(mat_subnet, item["textures"], engine=engine)
        built.append({**item, "subnet": mat_subnet.path()})

    mat_lib.layoutChildren()

    if built:
        if assign_all:
            bindings = [
                {"prims": item["bound_prims"], "material_path": item["stage_material_path"]}
                for item in built
                if item.get("bound_prims")
            ]
            if bindings:
                _configure_multi_assign(assign, bindings, max_slots=int(params.get("max_assignments", 32)))
            else:
                _configure_multi_assign(assign, [{"prims": ["%type:Mesh"], "material_path": built[0]["stage_material_path"]}])
        else:
            first = built[0]
            configure_assign_material(
                assign,
                primpattern_expr=" ".join(first["bound_prims"]) or "%type:Mesh",
                vexpression_expr=f'"{first["safe_name"]}"',
                bind_purpose_expr='"full"',
                bind_strength_expr='"fallback"',
            )
            set_parms(assign, {
                "matspecmethod1": "path",
                "matspecpath1": first["stage_material_path"],
            })

    assign.setDisplayFlag(True)
    return {
        "source_node": source.path(),
        "material_library": mat_lib.path(),
        "assign_node": assign.path(),
        "engine": engine,
        "imported_count": len(built),
        "materials": built,
        "analysis_summary": {
            "material_count": analysis["material_count"],
            "usd_folder": analysis["usd_folder"],
            "naming_strategy": analysis["naming_strategy"],
        },
    }
