"""Create a Component Output LOP with pipeline defaults (replaces decompiled generator)."""

from __future__ import annotations

import hou

from modules.houdini_node_utils import set_parm


def componentoutput_custom_creation(
    node_name: str = "componentoutput_custom",
    parent_path: str = "/stage",
) -> hou.Node:
    parent = hou.node(parent_path)
    if parent is None:
        raise hou.NodeError(f"Stage context not found: {parent_path}")

    if parent.node(node_name) is not None:
        node_name = parent.uniqueName(node_name)

    node = parent.createNode("componentoutput", node_name)
    set_parm(node, "rootprim", "/$OS")
    set_parm(node, "kind", "component")
    set_parm(node, "setdefaultvariants", 1)
    return node
