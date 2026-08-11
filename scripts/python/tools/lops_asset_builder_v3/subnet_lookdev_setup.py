"""Build lookdev setup subnet for LOPs Asset Builder (hand-written, replaces decompiled generator)."""

from __future__ import annotations

import hou

from modules.houdini_node_utils import set_parm

_LOOKDEV_CAMERA_SCRIPT = """
from tools import lops_lookdev_camera
import importlib
importlib.reload(lops_lookdev_camera)
lops_lookdev_camera.create_lookdev_camera("ASSET")
"""

_LINKED_PARMS = (
    "target",
    "camera_path",
    "use_existing_camera",
    "existing_camera_path",
    "spin",
    "pitch",
    "distance",
    "animate",
    "frames",
    "start_frame",
)


def _subnet_parm_templates() -> hou.ParmTemplateGroup:
    ptg = hou.ParmTemplateGroup()
    ptg.append(
        hou.LabelParmTemplate("lookdev_camera_settings", "Lookdev Camera Settings", column_labels=["Lookdev Camera Settings"])
    )
    ptg.append(hou.StringParmTemplate("target", "Target Prim", 1, default_value=["/turntable/asset"]))
    ptg.append(
        hou.StringParmTemplate("camera_path", "Camera Path", 1, default_value=["/turntable/lookdev/__ThumbnailCamera__"])
    )
    ptg.append(hou.ToggleParmTemplate("use_existing_camera", "Use Existing Camera", default_value=False))
    ptg.append(
        hou.StringParmTemplate(
            "existing_camera_path",
            "Existing Camera Path",
            1,
            default_value=["/turntable/lookdev/ldevCam0"],
            disable_when="{ use_existing_camera == 0 }",
        )
    )
    ptg.append(hou.FloatParmTemplate("spin", "Spin Camera", 1, default_value=(0.0,), min=-180, max=180))
    ptg.append(hou.FloatParmTemplate("pitch", "Pitch Camera", 1, default_value=(14.4,), min=-90, max=90))
    ptg.append(hou.FloatParmTemplate("distance", "Distance", 1, default_value=(0.0,), min=-50, max=50))
    ptg.append(hou.LabelParmTemplate("lookdev_animated_camera_settings", "LookDev Animated Camera Settings", column_labels=["Animated Camera"]))
    ptg.append(hou.ToggleParmTemplate("animate", "Animate", default_value=False))
    ptg.append(
        hou.IntParmTemplate("frames", "Frames", 1, default_value=(60,), disable_when="{ animate == 0 }")
    )
    ptg.append(
        hou.IntParmTemplate("start_frame", "Start Frame", 1, default_value=(1,), disable_when="{ animate == 0 }")
    )
    ptg.append(hou.ToggleParmTemplate("color_chart", "Color Chart", default_value=False))
    return ptg


def _link_pythonscript_parms(lookdev_cam: hou.Node) -> None:
    """Mirror subnet spare parms onto the pythonscript node via ch() expressions."""
    from tools import lops_lookdev_camera

    lops_lookdev_camera._create_parameters(lookdev_cam, "ASSET")
    for name in _LINKED_PARMS:
        parm = lookdev_cam.parm(name)
        if parm is not None:
            parm.setExpression(f'chs("../{name}")', language=hou.exprLanguage.Hscript)


def create_subnet_lookdev_setup(node_name: str = "lookdev_setup", parent_path: str = "/stage") -> hou.Node:
    parent = hou.node(parent_path)
    if parent is None:
        raise hou.NodeError(f"Stage context not found: {parent_path}")

    if parent.node(node_name) is not None:
        node_name = parent.uniqueName(node_name)

    subnet = parent.createNode("subnet", node_name)
    subnet.setParmTemplateGroup(_subnet_parm_templates())
    set_parm(subnet, "target", "/turntable/asset")
    set_parm(subnet, "camera_path", "/turntable/lookdev/__ThumbnailCamera__")
    set_parm(subnet, "existing_camera_path", "/turntable/lookdev/ldevCam0")
    set_parm(subnet, "pitch", 14.4)
    set_parm(subnet, "frames", 120)
    set_parm(subnet, "start_frame", 1)

    for child in list(subnet.children()):
        if child.type().name() == "output":
            child.destroy()

    ldev_cam = subnet.createNode("camera", "ldevCam0")
    set_parm(ldev_cam, "primpath", "/turntable/lookdev/$OS")
    set_parm(ldev_cam, "createprims", "on")
    set_parm(ldev_cam, "primpattern", "`lopinputprims('.', 0)`")

    lookdev_cam = subnet.createNode("pythonscript", "lookdev_camera")
    set_parm(lookdev_cam, "python", _LOOKDEV_CAMERA_SCRIPT)
    _link_pythonscript_parms(lookdev_cam)

    output = subnet.createNode("output", "output0")
    set_parm(output, "modifiedprims", '`lopinputprims(".", 0)`')

    subnet_input = subnet.indirectInputs()
    if subnet_input:
        ldev_cam.setInput(0, subnet_input[0])
    lookdev_cam.setInput(0, ldev_cam)
    output.setInput(0, lookdev_cam)

    subnet.layoutChildren()
    return subnet
