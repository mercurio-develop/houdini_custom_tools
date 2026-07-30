"""
Houdini helpers aligned with ftrack-connect-houdini behavior (timeline, thumbnail).

The legacy Connect plugin (0.2.3) lives at:
  $CUSTOM_TOOLS/ftrack-connect-houdini-0.2.3
It targets Python 2.7 + legacy ``ftrack`` API; Production Hub uses ftrack_api instead.
These helpers reproduce the artist-facing parts that still apply in Houdini 21.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Optional, Tuple

import hou


def apply_timeline(
    frame_start: float,
    frame_end: float,
    fps: float = 24.0,
    handles: float = 0.0,
) -> None:
    """Match Connect ``setFrameRangeData`` (pythonrc) for playback range."""
    start_frame = float(frame_start)
    end_frame = float(frame_end)
    hsf = (start_frame - 1) - handles
    hef = end_frame + handles

    hou.setFps(fps)
    hou.setFrame(start_frame)

    if start_frame != end_frame:
        try:
            hou.hscript("tset {0} {1}".format(hsf / fps, hef / fps))
            hou.playbar.setPlaybackRange(start_frame, end_frame)
        except hou.OperationFailed:
            pass


def apply_timeline_from_env_or_ftrack(
    frame_start: Optional[int],
    frame_end: Optional[int],
    fps: Optional[float] = None,
    handles: Optional[float] = None,
) -> Tuple[float, float]:
    """Use FS/FE env if set, else provided values; default 1001–1101."""
    fs = frame_start
    fe = frame_end
    if fs is None:
        fs = _env_int("FS", 1001)
    if fe is None:
        fe = _env_int("FE", 1101)
    apply_timeline(float(fs), float(fe), fps=fps or 24.0, handles=handles or 0.0)
    return float(fs), float(fe)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def viewport_screenshot() -> str:
    """
    Save a viewport JPG (same idea as Connect ``Connector.takeScreenshot``).
    Returns path to temp file for ftrack thumbnail upload.
    """
    import toolutils

    res = [1024, 768]
    filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.jpg")

    desktop = hou.ui.curDesktop()
    scene_view = toolutils.sceneViewer()
    if scene_view is None or scene_view.type() != hou.paneTabType.SceneViewer:
        raise hou.Error("No scene view available for screenshot")

    viewport = scene_view.curViewport()
    if viewport.camera() is not None:
        res = [
            int(viewport.camera().parm("resx").eval()),
            int(viewport.camera().parm("resy").eval()),
        ]

    view = f"{desktop.name()}.{scene_view.name()}.{viewport.name()}"
    cmd = f"viewwrite -c -f 0 1 -r {res[0]} {res[1]} {view} {filename}"
    hou.hscript(cmd)
    if not os.path.isfile(filename):
        raise hou.Error(f"viewwrite did not create {filename}")
    return filename


def connect_plugin_root() -> str:
    custom = os.environ.get("CUSTOM_TOOLS", "")
    if custom:
        path = os.path.join(custom, "ftrack-connect-houdini-0.2.3")
        if os.path.isdir(path):
            return path
    return ""


def connect_feature_matrix() -> dict[str, str]:
    """Summary for UI / docs: Connect vs Production Hub."""
    return {
        "Launch from ftrack Connect": "Connect hook sets FTRACK_TASKID, FS, FE — Production Hub reads same env",
        "Publish .hip / Alembic / geo": "Production Hub Connect-style group (geo / scene / cam)",
        "Publish USD + Iconik": "Production Hub + LOPS Asset Builder v3",
        "Import / Asset Manager": "Connect menus only (legacy ftrack API)",
        "Tasks browser (web)": "Connect ftrack menu — or ftrack web",
        "Python version": "Connect 0.2.3: Py2.7 — Hub: Py3.11 + ftrack-python-api",
    }
