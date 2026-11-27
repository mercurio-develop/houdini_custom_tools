"""Network box layout helpers for LOPS Asset Builder."""

from __future__ import annotations

import colorsys
import random
from typing import List, Type

import hou
from pxr import Usd, UsdGeom


def _random_color() -> tuple[hou.Color, hou.Color]:
    red_color = random.random()
    green_color = random.random()
    blue_color = random.random()
    main_colour = hou.Color(red_color, green_color, blue_color)
    hue, saturation, value = colorsys.rgb_to_hsv(red_color, green_color, blue_color)
    sec_red, sec_green, sec_blue = colorsys.hsv_to_rgb(hue, saturation * 0.5, value)
    secondary_colour = hou.Color(sec_red, sec_green, sec_blue)
    return main_colour, secondary_colour


def create_organized_net_note(
    asset_name: str,
    nodes_to_layout: list,
    offset_vector: hou.Vector2 | None = None,
    create_network_boxes: bool = True,
    category: str | None = None,
):
    """Create a network box and sticky note around selected nodes."""
    if not nodes_to_layout:
        print(f"Warning: No nodes provided to organize for {asset_name}")
        return None

    if offset_vector is None:
        offset_vector = hou.Vector2(0, 0)

    parent = nodes_to_layout[0].parent()

    for node in nodes_to_layout:
        node.setPosition(node.position() + offset_vector)

    if not create_network_boxes:
        parent.layoutChildren(items=nodes_to_layout)
        return None

    category_colors = {
        "Asset": (hou.Color(0.2, 0.4, 0.6), hou.Color(0.3, 0.5, 0.7)),
        "Light": (hou.Color(0.6, 0.5, 0.2), hou.Color(0.7, 0.6, 0.3)),
        "Camera": (hou.Color(0.5, 0.2, 0.5), hou.Color(0.6, 0.3, 0.6)),
        "Material": (hou.Color(0.2, 0.5, 0.3), hou.Color(0.3, 0.6, 0.4)),
        "Render": (hou.Color(0.6, 0.2, 0.2), hou.Color(0.7, 0.3, 0.3)),
    }

    if category and category in category_colors:
        parent_colour, child_colour = category_colors[category]
    else:
        background_colour = 0.189
        parent_colour = hou.Color(background_colour, background_colour, background_colour)
        child_colour, _ = _random_color()

    parent_box = parent.createNetworkBox()
    child_box = parent.createNetworkBox()
    parent_box.addItem(child_box)

    for node in nodes_to_layout:
        child_box.addItem(node)

    child_box.fitAroundContents()
    parent_box.setComment(asset_name)
    parent_box.setColor(parent_colour)
    child_box.setColor(child_colour)
    parent_box.fitAroundContents()
    return parent_box, child_box


def find_prims_by_attribute(stage: Usd.Stage, prim_type: Type[Usd.Typed]) -> List[str]:
    if stage is None:
        print("Warning: Stage is None in find_prims_by_attribute, returning empty list")
        return []
    names = set()
    for prim in stage.Traverse():
        if prim.IsA(prim_type) and "render" in str(prim.GetPath()):
            names.add(prim.GetName())
    return list(names)
