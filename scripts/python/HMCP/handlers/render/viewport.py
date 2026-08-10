"""Viewport capture and render helpers for HMCP."""

from __future__ import annotations

import base64
import os
import tempfile

import hou


def capture_viewport(params: dict) -> dict:
    output_path = params.get("output_path")
    if output_path:
        output_path = hou.text.expandString(output_path)
    else:
        output_path = os.path.join(tempfile.gettempdir(), "hmcp_viewport.png")

    desktop = hou.ui.curDesktop()
    viewer = desktop.paneTabOfType(hou.paneTabType.SceneViewer)
    if viewer is None:
        raise ValueError("No Scene Viewer pane is open")

    captured = False
    if hasattr(viewer, "captureViewportToFile"):
        viewer.captureViewportToFile(output_path)
        captured = os.path.isfile(output_path)
    elif hasattr(viewer, "saveViewportScreenshot"):
        viewer.saveViewportScreenshot(output_path)
        captured = os.path.isfile(output_path)
    else:
        settings = viewer.flipbookSettings() if hasattr(viewer, "flipbookSettings") else None
        if settings is not None:
            settings.output(output_path)
            settings.frameRange((int(hou.frame()), int(hou.frame())))
            viewer.flipbook(settings)
            captured = os.path.isfile(output_path)

    if not captured or not os.path.isfile(output_path):
        raise RuntimeError("Viewport capture failed — open a Scene Viewer and retry")

    with open(output_path, "rb") as handle:
        image_b64 = base64.b64encode(handle.read()).decode("utf-8")

    return {
        "output_path": output_path,
        "image": image_b64,
        "format": "png",
        "frame": hou.frame(),
    }


def cook_render_node(params: dict) -> dict:
    """Cook a ROP/render node (e.g. usdrender_rop) and report output."""
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    node.cook(force=True)

    output_image = None
    for parm_name in ("picture", "vm_picture", "output_image", "soho_outputimage"):
        parm = node.parm(parm_name)
        if parm is not None:
            try:
                output_image = hou.text.expandString(parm.eval())
                break
            except Exception:
                pass

    errors = []
    if hasattr(node, "errors"):
        try:
            raw = node.errors()
            if raw:
                errors.extend(raw if isinstance(raw, (list, tuple)) else [str(raw)])
        except Exception:
            pass

    return {
        "node_path": node.path(),
        "type": node.type().name(),
        "cooked": True,
        "output_image": output_image,
        "output_exists": bool(output_image and os.path.isfile(output_image)),
        "errors": errors,
    }


def set_frame_range(params: dict) -> dict:
    start = int(params.get("start_frame", 1))
    end = int(params.get("end_frame", 120))
    hou.playbar.setFrameRange(start, end)
    hou.playbar.setPlaybackRange(start, end)
    return {"start_frame": start, "end_frame": end, "current_frame": hou.frame()}
