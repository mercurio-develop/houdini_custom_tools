"""Material binding inspection on cooked LOP USD stages."""

from __future__ import annotations

import hou


def list_material_assignments(params: dict) -> dict:
    node_path = params.get("node_path")
    root_path = params.get("root_path", "/")
    max_prims = int(params.get("max_prims", 500))
    include_unbound = bool(params.get("include_unbound", False))

    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    if params.get("cook_first", True):
        node.cook(force=True)

    stage = node.stage() if hasattr(node, "stage") else None
    if stage is None:
        raise ValueError(f"No USD stage on node: {node_path}")

    try:
        from pxr import UsdGeom, UsdShade
    except ImportError as exc:
        raise RuntimeError("pxr.UsdShade not available") from exc

    root = stage.GetPrimAtPath(root_path)
    if not root or not root.IsValid():
        raise ValueError(f"Invalid root prim: {root_path}")

    assignments = []
    unbound = []
    material_paths = set()

    if root_path == "/":
        prims = list(stage.Traverse())
    else:
        prims = [root] + list(root.GetAllChildren())

    for prim in prims:
        if len(assignments) + len(unbound) >= max_prims:
            break
        if not prim.IsActive():
            continue

        binding_api = UsdShade.MaterialBindingAPI(prim)
        mat, rel = binding_api.ComputeBoundMaterial()
        if mat and mat.GetPrim().IsValid():
            mat_path = str(mat.GetPath())
            material_paths.add(mat_path)
            entry = {
                "prim_path": str(prim.GetPath()),
                "prim_type": prim.GetTypeName(),
                "material_path": mat_path,
            }
            if rel:
                entry["binding_relationship"] = str(rel.GetPath())
            assignments.append(entry)
        elif include_unbound and prim.IsA(UsdGeom.Boundable):
            unbound.append({"prim_path": str(prim.GetPath()), "prim_type": prim.GetTypeName()})

    return {
        "node_path": node_path,
        "root_path": root_path,
        "assignment_count": len(assignments),
        "unique_materials": sorted(material_paths),
        "assignments": assignments,
        "unbound_count": len(unbound),
        "unbound_prims": unbound[:50],
        "truncated": len(assignments) + len(unbound) >= max_prims,
    }
