"""
Shared LOP graph wiring for lookdev, light rig, env lights, camera, and Karma nodes.

Used by the interactive builder and CLI so lookdev setup stays in one place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, List, Optional

import hou

from modules.misc_utils import _sanitize
from tools import lops_light_rig
from tools.lops_asset_builder_v3.asset_builder_progress import ProgressLike
from tools.lops_asset_builder_v3.create_transform_nodes import (
    build_lights_spin_xform,
    build_transform_camera_and_scene_node,
)
from tools.lops_asset_builder_v3.network_layout import create_organized_net_note
from tools.lops_asset_builder_v3.subnet_lookdev_setup import create_subnet_lookdev_setup


@dataclass
class LookdevBuildOptions:
    """Options for building the lookdev branch after component output exists."""

    node_name: str
    create_light_rig: bool = True
    enable_env_lights: bool = False
    env_light_paths: List[str] = field(default_factory=list)
    create_network_boxes: bool = True


@dataclass
class LookdevBuildResult:
    """Handles to nodes created by the lookdev branch."""

    switch_lookdev_setup_node: hou.Node
    karma_nodes: List[hou.Node]
    lookdev_setup_layout: List[hou.Node]


def cook_lop_for_stage(node: hou.Node, progress: ProgressLike | None = None) -> bool:
    """Cook a LOP node and return True when a USD stage is available."""
    if node is None:
        return False
    try:
        if progress:
            progress.log(f"Cooking {node.path()} for USD stage…")
        node.cook(force=True)
        return node.stage() is not None
    except Exception as exc:
        if progress:
            progress.log(f"Cook failed for {node.path()}: {exc}")
        return False


def create_karma_nodes(parent: hou.Node, name_prefix: str = "") -> tuple[hou.Node, hou.Node]:
    """Create Karma render settings and USD Render ROP with lookdev camera defaults."""
    karma_name = _sanitize(f"{name_prefix}karmarendersettings") if name_prefix else "karmarendersettings"
    rop_name = _sanitize(f"{name_prefix}usdrender_rop") if name_prefix else "usdrender_rop"
    karma_settings = parent.createNode("karmarenderproperties", karma_name)
    usdrender_rop = parent.createNode("usdrender_rop", rop_name)
    karma_settings.parm("picture").set("$JOB/render/$HIPNAME.$OS.$F4.exr")
    ldev_cam_path = "/turntable/lookdev/ldevCam0"
    cam_parm = karma_settings.parm("camera") or karma_settings.parm("camerapath")
    if cam_parm is not None:
        cam_parm.set(ldev_cam_path)
    usdrender_rop.parm("rendersettings").set(f'`chs("../{karma_name}/primpath")`')
    return karma_settings, usdrender_rop


def _lookdev_node_name(asset_name: str, suffix: str) -> str:
    return _sanitize(f"{asset_name}_{suffix}")


def build_lookdev_setup(
    stage_context: hou.Node,
    comp_out: hou.Node,
    options: LookdevBuildOptions,
    progress: ProgressLike | None = None,
) -> LookdevBuildResult:
    """
    Wire lookdev scope, optional light rig/env lights, subnet, camera, and Karma nodes.

    Raises KeyboardInterrupt when progress.is_cancelled() is True mid-build.
    """
    def _check_cancelled() -> None:
        if progress and progress.is_cancelled():
            raise KeyboardInterrupt("Cancelled by user")

    if progress:
        progress.step("Creating lookdev scope and graft stages")

    asset = options.node_name
    lookdev_setup_layout: List[hou.Node] = []
    primitive_node = stage_context.createNode("primitive", _lookdev_node_name(asset, "lookdev_geo"))
    primitive_node.parm("primpath").set("/turntable/asset/\n/turntable/lookdev/\n/turntable/lights/")
    primitive_node.parm("parentprimtype").set("UsdGeomScope")

    graftstage_asset_node = stage_context.createNode(
        "graftstages", _lookdev_node_name(asset, "graftstage_asset")
    )
    graftstage_asset_node.parm("primpath").set("/turntable/asset")
    graftstage_asset_node.parm("destpath").set("/")
    graftstage_asset_node.setInput(0, primitive_node)
    graftstage_asset_node.setInput(1, comp_out)

    current_stream = graftstage_asset_node
    if options.create_light_rig:
        if progress:
            progress.step("Building light rig")
        _check_cancelled()

        if not cook_lop_for_stage(comp_out, progress):
            if progress:
                progress.log("Skipping light rig: component output has no cooked USD stage yet.")
        else:
            try:
                light_rig_nodes_to_layout, light_mixer = lops_light_rig.create_three_point_light(
                    selected_node=comp_out
                )
            except Exception as exc:
                if progress:
                    progress.log(f"Skipping light rig: {exc}")
                light_rig_nodes_to_layout = None
                light_mixer = None

            if light_rig_nodes_to_layout and light_mixer:
                graftstage_lights_node = stage_context.createNode(
                    "graftstages", _lookdev_node_name(asset, "graftstage_lights_rig")
                )
                graftstage_lights_node.parm("primpath").set("/turntable/")
                graftstage_lights_node.parm("destpath").set("/")
                graftstage_lights_node.setInput(0, current_stream)
                _check_cancelled()
                create_organized_net_note(
                    "Light Rig",
                    light_rig_nodes_to_layout,
                    hou.Vector2(5, 10),
                    create_network_boxes=options.create_network_boxes,
                )
                graftstage_lights_node.setInput(1, light_mixer)
                switch_lights_rig_node = stage_context.createNode(
                    "switch", _lookdev_node_name(asset, "switch_lights_rig")
                )
                switch_lights_rig_node.setInput(0, current_stream)
                switch_lights_rig_node.setInput(1, graftstage_lights_node)
                switch_lights_rig_node.parm("input").set(1)
                lookdev_setup_layout.extend([switch_lights_rig_node, graftstage_lights_node])
                current_stream = switch_lights_rig_node
            elif progress:
                progress.log("Light rig skipped; lookdev/camera/render will still be created.")

    if options.enable_env_lights:
        if progress:
            progress.step("Creating environment lights")
        graftstage_envlights_node = stage_context.createNode(
            "graftstages", _lookdev_node_name(asset, "graftstage_envlights")
        )
        graftstage_envlights_node.parm("primpath").set("/turntable/lights")
        graftstage_envlights_node.parm("destpath").set("/")
        graftstage_envlights_node.setInput(0, current_stream)

        domes: List[hou.Node] = []
        if options.env_light_paths:
            for idx, path in enumerate(options.env_light_paths):
                base = os.path.splitext(os.path.basename(path))[0]
                dome = stage_context.createNode(
                    "domelight::3.0",
                    _sanitize(f"{base or 'env_light'}_{idx + 1}"),
                )
                dome.parm("primpath").set("/$OS")
                dome.parm("xn__inputstexturefile_r3ah").set(path)
                domes.append(dome)
        else:
            dome = stage_context.createNode(
                "domelight::3.0", _lookdev_node_name(asset, "env_light")
            )
            dome.parm("primpath").set("/$OS")
            domes.append(dome)

        switch_envlights_selection_node = stage_context.createNode(
            "switch", _lookdev_node_name(asset, "switch_envlights_selection")
        )
        for i, dome in enumerate(domes):
            switch_envlights_selection_node.setInput(i, dome)
        envlights_nodes_to_layout = domes + [switch_envlights_selection_node]

        stage_context.layoutChildren(items=envlights_nodes_to_layout)
        _check_cancelled()
        create_organized_net_note(
            "Env Light",
            envlights_nodes_to_layout,
            hou.Vector2(5, 6),
            create_network_boxes=options.create_network_boxes,
        )

        graftstage_envlights_node.setInput(1, switch_envlights_selection_node)
        switch_env_lights = stage_context.createNode(
            "switch", _lookdev_node_name(asset, "switch_env_lights")
        )
        switch_env_lights.setInput(0, current_stream)
        switch_env_lights.setInput(1, graftstage_envlights_node)
        switch_env_lights.parm("input").set(1)
        current_stream = switch_env_lights
        lookdev_setup_layout.extend([switch_env_lights, graftstage_envlights_node])

    if progress:
        progress.step("Creating lookdev subnetwork")
    subnetwork_lookdevsetup_node = create_subnet_lookdev_setup(
        node_name=_lookdev_node_name(asset, "lookdev_setup")
    )
    subnetwork_lookdevsetup_node.setInput(0, current_stream)

    switch_lookdev_setup_node = stage_context.createNode(
        "switch", _lookdev_node_name(asset, "switch_lookdev_setup")
    )
    switch_lookdev_setup_node.setInput(0, current_stream)
    switch_lookdev_setup_node.setInput(1, subnetwork_lookdevsetup_node)
    switch_lookdev_setup_node.parm("input").set(1)
    lookdev_setup_layout = lookdev_setup_layout + [
        switch_lookdev_setup_node,
        subnetwork_lookdevsetup_node,
        graftstage_asset_node,
        primitive_node,
    ]
    stage_context.layoutChildren(items=lookdev_setup_layout, horizontal_spacing=0.3, vertical_spacing=1.5)
    create_organized_net_note(
        "LookDev Setup",
        lookdev_setup_layout,
        hou.Vector2(15, -5),
        create_network_boxes=options.create_network_boxes,
    )

    if progress:
        progress.step("Creating camera, animations, and render nodes")
    transform_camera_and_scene_node = build_transform_camera_and_scene_node(
        node_name=_lookdev_node_name(asset, "transform_camera_and_scene")
    )
    transform_camera_and_scene_node.setInput(0, switch_lookdev_setup_node)
    switch_transform_camera_and_scene_node = stage_context.createNode(
        "switch", _lookdev_node_name(asset, "switch_transform_camera_and_scene")
    )
    switch_transform_camera_and_scene_node.setInput(0, switch_lookdev_setup_node)
    switch_transform_camera_and_scene_node.setInput(1, transform_camera_and_scene_node)
    transform_envlights_node = build_lights_spin_xform(
        node_name=_lookdev_node_name(asset, "animate_lights")
    )
    transform_envlights_node.setInput(0, switch_transform_camera_and_scene_node)
    switch_animate_lights = stage_context.createNode(
        "switch", _lookdev_node_name(asset, "switch_animate_lights")
    )
    switch_animate_lights.setInput(0, switch_transform_camera_and_scene_node)
    switch_animate_lights.setInput(1, transform_envlights_node)

    karma_settings, usdrender_rop = create_karma_nodes(stage_context, name_prefix=f"{asset}_")
    karma_settings.setInput(0, switch_animate_lights)
    usdrender_rop.setInput(0, karma_settings)

    karma_nodes = [
        switch_transform_camera_and_scene_node,
        transform_camera_and_scene_node,
        switch_animate_lights,
        transform_envlights_node,
        karma_settings,
        usdrender_rop,
    ]
    stage_context.layoutChildren(items=karma_nodes, horizontal_spacing=0.25, vertical_spacing=1)
    _check_cancelled()
    create_organized_net_note(
        "Camera Render",
        karma_nodes,
        hou.Vector2(0, -5),
        create_network_boxes=options.create_network_boxes,
    )

    return LookdevBuildResult(
        switch_lookdev_setup_node=switch_lookdev_setup_node,
        karma_nodes=karma_nodes,
        lookdev_setup_layout=lookdev_setup_layout,
    )
