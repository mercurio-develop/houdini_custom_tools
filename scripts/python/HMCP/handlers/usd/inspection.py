"""USD / LOP stage inspection handlers for HMCP."""

from __future__ import annotations

import hou


def inspect_usd_prim(params: dict) -> dict:
    node_path = params.get("node_path")
    prim_path = params.get("prim_path", "/")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    if not hasattr(node, "stage"):
        raise ValueError(f"Node has no USD stage: {node_path}")

    if params.get("cook_first", True):
        node.cook(force=True)

    stage = node.stage()
    if stage is None:
        return {"node_path": node_path, "prim_path": prim_path, "found": False}

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return {"node_path": node_path, "prim_path": prim_path, "found": False}

    variant_sets = {}
    try:
        vsets = prim.GetVariantSets()
        names = list(vsets.GetNames())
        for vset_name in names:
            variant_sets[vset_name] = vsets.GetVariantSelection(vset_name)
    except Exception:
        pass

    children = []
    max_children = int(params.get("max_children", 50))
    for i, child in enumerate(prim.GetChildren()):
        if i >= max_children:
            children.append("...(truncated)")
            break
        children.append({"path": str(child.GetPath()), "type": child.GetTypeName()})

    return {
        "node_path": node_path,
        "prim_path": prim_path,
        "found": True,
        "type": prim.GetTypeName(),
        "active": prim.IsActive(),
        "variant_sets": variant_sets,
        "children": children,
    }


def list_usd_prims(params: dict) -> dict:
    node_path = params.get("node_path")
    root_path = params.get("root_path", "/")
    type_filter = params.get("type_filter")
    max_prims = int(params.get("max_prims", 200))

    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    if params.get("cook_first", True):
        node.cook(force=True)

    stage = node.stage()
    if stage is None:
        return {"node_path": node_path, "prims": [], "count": 0}

    prims = []
    root = stage.GetPrimAtPath(root_path)
    if not root or not root.IsValid():
        return {"node_path": node_path, "root_path": root_path, "prims": [], "count": 0}

    for prim in root.GetAllChildren():
        type_name = prim.GetTypeName()
        if type_filter and type_name != type_filter:
            continue
        prims.append({"path": str(prim.GetPath()), "type": type_name})
        if len(prims) >= max_prims:
            break

    return {
        "node_path": node_path,
        "root_path": root_path,
        "count": len(prims),
        "truncated": len(prims) >= max_prims,
        "prims": prims,
    }


def export_usd_from_lop(params: dict) -> dict:
    node_path = params.get("node_path")
    output_path = params.get("output_path")
    if not node_path or not output_path:
        raise ValueError("node_path and output_path are required")

    output_path = hou.text.expandString(output_path)
    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    node.cook(force=True)
    stage = node.stage()
    if stage is None:
        raise ValueError("No USD stage on node after cook")

    stage.Export(output_path)
    return {"node_path": node_path, "output_path": output_path, "exported": True}
