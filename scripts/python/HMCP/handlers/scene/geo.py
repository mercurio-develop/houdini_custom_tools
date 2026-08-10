"""SOP geometry statistics for PSX / geo debugging."""

from __future__ import annotations

import hou


def get_geo_stats(params: dict) -> dict:
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    if params.get("cook_first", True):
        node.cook(force=params.get("force", True))

    geo = node.geometry()
    if geo is None:
        return {
            "node_path": node.path(),
            "type": node.type().name(),
            "has_geometry": False,
        }

    bbox = geo.boundingBox()
    point_groups = [g.name() for g in geo.pointGroups()]
    prim_groups = [g.name() for g in geo.primGroups()]
    vertex_groups = [g.name() for g in geo.vertexGroups()]

    point_attrs = []
    for attr in geo.pointAttribs():
        point_attrs.append({"name": attr.name(), "size": attr.size(), "type": str(attr.dataType())})

    prim_attrs = []
    for attr in geo.primAttribs():
        prim_attrs.append({"name": attr.name(), "size": attr.size(), "type": str(attr.dataType())})

    try:
        vertex_count = len(geo.iterVertices())
    except Exception:
        vertex_count = 0

    return {
        "node_path": node.path(),
        "type": node.type().name(),
        "has_geometry": True,
        "points": len(geo.points()),
        "prims": len(geo.prims()),
        "vertices": vertex_count,
        "bounds": {
            "min": list(bbox.minvec()),
            "max": list(bbox.maxvec()),
            "size": list(bbox.sizevec()),
            "center": list(bbox.center()),
        },
        "point_groups": point_groups,
        "prim_groups": prim_groups,
        "vertex_groups": vertex_groups,
        "point_attributes": point_attrs[: int(params.get("max_attributes", 40))],
        "prim_attributes": prim_attrs[: int(params.get("max_attributes", 40))],
    }
