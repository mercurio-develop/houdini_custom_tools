"""Karma / Solaris preview rendering for HMCP."""

from __future__ import annotations

import base64
import os
import tempfile

import hou

from tools.lops_asset_builder_v3.asset_builder_graph import create_karma_nodes
from tools.psx_tools.karma_presets import apply_psx_karma_settings
from tools.psx_tools.psx_config import PSXAssetConfig


def _find_render_setup(parent: hou.Node, render_node_path: str | None):
    if render_node_path:
        rop = hou.node(render_node_path)
        if rop is None:
            raise ValueError(f"Render node not found: {render_node_path}")
        karma = None
        for inp in rop.inputs():
            if inp and inp.type().name() in ("karmarenderproperties", "karmarendersettings"):
                karma = inp
                break
        rs_parm = rop.parm("rendersettings") or rop.parm("karma_settings")
        if karma is None and rs_parm is not None:
            karma_path = rs_parm.eval()
            if karma_path:
                karma = hou.node(str(karma_path))
        return karma, rop

    for child in parent.children():
        if child.type().name() == "usdrender_rop":
            karma = None
            for inp in child.inputs():
                if inp and inp.type().name() in ("karmarenderproperties", "karmarendersettings"):
                    karma = inp
                    break
            return karma, child
    return None, None


def _set_parm(node: hou.Node, names: tuple[str, ...], value) -> bool:
    for name in names:
        parm = node.parm(name) or node.parmTuple(name)
        if parm is not None:
            try:
                parm.set(value)
                return True
            except Exception:
                pass
    return False


def _resolve_output_image(rop: hou.Node, frame: int) -> str | None:
    for parm_name in ("picture", "vm_picture", "output_image", "soho_outputimage"):
        parm = rop.parm(parm_name)
        if parm is None:
            continue
        try:
            path = hou.text.expandString(parm.eval())
            if "$F" in parm.unexpandedString() or "$F4" in parm.unexpandedString():
                path = hou.text.expandString(parm.evalAsStringAtFrame(frame))
            if path and os.path.isfile(path):
                return path
        except Exception:
            pass
    return None


def apply_psx_karma(params: dict) -> dict:
    node_path = params.get("node_path")
    karma_node = hou.node(node_path) if node_path else None
    cfg = PSXAssetConfig()
    if params.get("render_resolution"):
        res = params["render_resolution"]
        cfg.render_resolution = (int(res[0]), int(res[1]))

    node = apply_psx_karma_settings(karma_node=karma_node, config=cfg)
    if node is None:
        raise RuntimeError("Could not create or configure Karma render settings")
    return {"karma_node": node.path(), "resolution": cfg.render_resolution}


def render_karma_preview(params: dict) -> dict:
    lop_node_path = params.get("lop_node_path") or params.get("node_path")
    parent_path = params.get("parent_path", "/stage")
    frame = int(params.get("frame", hou.frame()))
    res = params.get("resolution", [1024, 1024])
    res_x, res_y = int(res[0]), int(res[1])
    psx_preset = bool(params.get("psx_preset", False))
    create_if_missing = params.get("create_if_missing", True)

    parent = hou.node(parent_path)
    if parent is None:
        raise ValueError(f"Parent not found: {parent_path}")

    lop_node = hou.node(lop_node_path) if lop_node_path else None
    karma, rop = _find_render_setup(parent, params.get("render_node_path"))

    if rop is None and create_if_missing:
        karma, rop = create_karma_nodes(parent, name_prefix="hmcp_")
        if lop_node is not None:
            rop.setInput(0, lop_node)
        if psx_preset and karma is not None:
            apply_psx_karma_settings(karma_node=karma)

    if rop is None:
        raise RuntimeError("No usdrender_rop found — provide render_node_path or create_if_missing=true")

    if lop_node is not None and rop.inputs() and rop.inputs()[0] != lop_node:
        rop.setInput(0, lop_node)
    elif lop_node is not None and not rop.inputs():
        rop.setInput(0, lop_node)

    if karma is not None:
        _set_parm(karma, ("resolution",), (res_x, res_y))
        _set_parm(karma, ("resolutionX",), res_x)
        _set_parm(karma, ("resolutionY",), res_y)
        camera_path = params.get("camera_path") or params.get("camera")
        if camera_path:
            _set_parm(karma, ("camera", "camerapath"), camera_path)
        if psx_preset:
            apply_psx_karma_settings(karma_node=karma)

    hou.setFrame(frame)
    output_path = params.get("output_path")
    if output_path:
        output_path = hou.text.expandString(output_path)
    else:
        output_path = os.path.join(tempfile.gettempdir(), f"hmcp_karma_{frame:04d}.png")

    _set_parm(rop, ("picture", "vm_picture", "output_image"), output_path)
    _set_parm(rop, ("trange",), 0)
    _set_parm(rop, ("f1",), frame)
    _set_parm(rop, ("f2",), frame)

    if hasattr(rop, "render"):
        rop.render(frame_range=(frame, frame), output_progress=True)
    else:
        execute = rop.parm("execute") or rop.parm("renderexecute")
        if execute is not None:
            execute.pressButton()
        else:
            rop.cook(force=True)

    image_path = _resolve_output_image(rop, frame)
    if image_path is None and os.path.isfile(output_path):
        image_path = output_path

    if image_path is None or not os.path.isfile(image_path):
        raise RuntimeError("Karma render completed but output image was not found")

    with open(image_path, "rb") as handle:
        image_b64 = base64.b64encode(handle.read()).decode("utf-8")

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    return {
        "render_node": rop.path(),
        "karma_node": karma.path() if karma else None,
        "lop_node": lop_node.path() if lop_node else None,
        "output_path": image_path,
        "image": image_b64,
        "format": ext or "png",
        "width": res_x,
        "height": res_y,
        "frame": frame,
    }
