"""Shared LOP node discovery helpers."""

from __future__ import annotations

import hou


def find_component_output(node_path: str | None = None) -> hou.Node | None:
    """Return a componentoutput node by path or heuristics under /stage."""
    if node_path:
        node = hou.node(node_path)
        if node is None:
            raise ValueError(f"Node not found: {node_path}")
        return node

    stage = hou.node("/stage")
    if stage is None:
        return None

    outputs = [child for child in stage.allSubChildren() if child.type().name() == "componentoutput"]
    if not outputs:
        return None

    for node in outputs:
        if node.isDisplayFlagSet() or node.isRenderFlagSet():
            return node
    return outputs[-1]
