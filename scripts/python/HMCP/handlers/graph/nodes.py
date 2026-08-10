"""Node graph wiring and layout handlers for HMCP."""

from __future__ import annotations

import hou


def connect_nodes(params: dict) -> dict:
    output_path = params.get("output_node")
    input_path = params.get("input_node")
    input_index = int(params.get("input_index", 0))

    if not output_path or not input_path:
        raise ValueError("output_node and input_node are required")

    output_node = hou.node(output_path)
    input_node = hou.node(input_path)
    if output_node is None:
        raise ValueError(f"Output node not found: {output_path}")
    if input_node is None:
        raise ValueError(f"Input node not found: {input_path}")

    input_node.setInput(input_index, output_node)
    return {
        "input_node": input_node.path(),
        "output_node": output_node.path(),
        "input_index": input_index,
        "connected": True,
    }


def layout_nodes(params: dict) -> dict:
    parent_path = params.get("parent_path")
    node_paths = params.get("node_paths")

    if node_paths:
        nodes = []
        for path in node_paths:
            n = hou.node(path)
            if n is not None:
                nodes.append(n)
        if nodes:
            parent = nodes[0].parent()
            parent.layoutChildren(items=nodes)
            return {"parent": parent.path(), "laid_out": len(nodes), "mode": "selection"}
        raise ValueError("No valid nodes in node_paths")

    if not parent_path:
        raise ValueError("parent_path or node_paths is required")

    parent = hou.node(parent_path)
    if parent is None:
        raise ValueError(f"Parent not found: {parent_path}")

    parent.layoutChildren()
    return {"parent": parent.path(), "child_count": len(parent.children()), "mode": "all_children"}


def set_node_flags(params: dict) -> dict:
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    updated = []
    flag_map = {
        "display": "setDisplayFlag",
        "render": "setRenderFlag",
        "template": "setTemplateFlag",
        "bypass": "setBypass",
        "lock": "setLocked",
    }
    for key, method_name in flag_map.items():
        if key not in params:
            continue
        method = getattr(node, method_name, None)
        if method is None:
            continue
        try:
            method(bool(params[key]))
            updated.append(key)
        except Exception:
            pass

    return {"node_path": node.path(), "updated_flags": updated}
