"""Wire PSX SOP effects into an asset import chain."""

from __future__ import annotations

import hou

from tools.psx_tools.psx_config import PSXAssetConfig
from tools.psx_tools.sop_effects import (
    create_decimate_node,
    create_screen_snap_node,
    create_triangulate_node,
    create_wobble_node,
)


def apply_psx_sop_chain(
    parent: hou.Node,
    input_node: hou.Node,
    config: PSXAssetConfig | None = None,
) -> hou.Node:
    """
    Insert PSX geometry processing after import/cleanup nodes.

    Order: decimate → triangulate → vertex wobble → screen snap
    Returns the tail node to wire into outputs.
    """
    cfg = config or PSXAssetConfig()
    current = input_node

    if cfg.decimate_ratio < 1.0:
        dec = create_decimate_node(parent, cfg.decimate_ratio)
        dec.setInput(0, current)
        current = dec

    if cfg.triangulate:
        tri = create_triangulate_node(parent)
        tri.setInput(0, current)
        current = tri

    if cfg.apply_vertex_wobble:
        wobble = create_wobble_node(parent, cfg)
        wobble.setInput(0, current)
        current = wobble

    if cfg.apply_screen_snap:
        snap = create_screen_snap_node(parent, cfg)
        snap.setInput(0, current)
        current = snap

    parent.layoutChildren()
    return current


def patch_geo_import_with_psx(comp_geo: hou.Node, config: PSXAssetConfig) -> None:
    """
    Find the default SOP output chain inside a componentgeometry and insert PSX nodes.

    Inserts after `remove_points` and rewires default, proxy, and sim branches.
    """
    sopnet = hou.node(f"{comp_geo.path()}/sopnet/geo")
    if sopnet is None:
        return

    anchor = sopnet.node("remove_points")
    if anchor is None:
        return

    tail = apply_psx_sop_chain(sopnet, anchor, config)

    for out_name in ("default",):
        out = sopnet.node(out_name)
        if out is not None:
            out.setInput(0, tail)

    for branch_name in ("reduce_to_5", "convex_hull_setup"):
        branch = sopnet.node(branch_name)
        if branch is not None and branch.inputs() and branch.inputs()[0] == anchor:
            branch.setInput(0, tail)

    sopnet.layoutChildren()
