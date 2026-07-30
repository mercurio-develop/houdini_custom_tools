"""
Connect-style Houdini exports (geo / scene / cam) for ftrack publish.

Port of ftrack-connect-houdini ``houdiniassets.py`` for Houdini 21 / Python 3.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

import hou


class ConnectAssetKind(str, Enum):
    SCENE = "scene"
    GEO = "geo"
    CAM = "cam"


@dataclass
class PublishedComponent:
    name: str
    path: str

    @property
    def file_type(self) -> str:
        ext = os.path.splitext(self.path)[1].lstrip(".").lower()
        return ext or "bin"


@dataclass
class ConnectExportOptions:
    """Mirrors Connect publish checkboxes / radios."""

    export_mode_selection: bool = True
    alembic: bool = True
    alembic_animation: bool = False
    alembic_export_mode_selection: bool = True
    houdini_nodes: bool = True
    houdini_publish_scene: bool = False
    frame_start: float = 1001.0
    frame_end: float = 1101.0
    alembic_eval: float = 1.0

    @classmethod
    def from_playbar(cls) -> "ConnectExportOptions":
        fs = hou.playbar.playbackRange()[0]
        fe = hou.playbar.playbackRange()[1]
        return cls(frame_start=fs, frame_end=fe)


def _temp_path(suffix: str) -> str:
    return os.path.join(tempfile.gettempdir(), f"production_hub_{uuid.uuid4().hex}{suffix}")


def validate_for_publish(kind: ConnectAssetKind, options: ConnectExportOptions) -> Tuple[bool, str]:
    nodes = hou.selectedNodes()
    if kind == ConnectAssetKind.CAM:
        if len(nodes) != 1:
            return False, "Select exactly one camera object"
        if "cam" not in nodes[0].type().name().lower():
            return False, "Selected node is not a camera"
        return True, ""

    if options.export_mode_selection or options.alembic_export_mode_selection:
        if options.houdini_nodes or (options.alembic and options.alembic_export_mode_selection):
            if kind == ConnectAssetKind.GEO and options.alembic_export_mode_selection and options.alembic:
                if not nodes and options.alembic_export_mode_selection:
                    return False, "Nothing selected for Alembic export"
            if options.houdini_nodes and options.export_mode_selection and not nodes:
                return False, "Nothing selected for Houdini nodes export"
    return True, ""


def export_connect_asset(
    kind: ConnectAssetKind,
    options: ConnectExportOptions,
) -> List[PublishedComponent]:
    ok, msg = validate_for_publish(kind, options)
    if not ok:
        raise hou.Error(msg)

    if kind == ConnectAssetKind.SCENE:
        return _export_scene_only(options)
    if kind == ConnectAssetKind.GEO:
        return _export_geometry(options)
    if kind == ConnectAssetKind.CAM:
        return _export_camera(options)
    raise hou.Error(f"Unknown asset kind: {kind}")


def _export_scene_only(options: ConnectExportOptions) -> List[PublishedComponent]:
    path = _temp_path(".hip")
    if options.export_mode_selection:
        nodes = hou.selectedNodes()
        if not nodes:
            raise hou.Error("Nothing selected for scene export")
        nodes[0].parent().saveChildrenToFile(nodes, [], path)
    else:
        hou.hipFile.save(path, save_to_recent_files=False)
    return [PublishedComponent("houdiniPublishScene", path)]


def _export_houdini_nodes(options: ConnectExportOptions) -> List[PublishedComponent]:
    path = _temp_path(".hip")
    if options.export_mode_selection:
        nodes = hou.selectedNodes()
        if not nodes:
            raise hou.Error("Nothing selected")
        nodes[0].parent().saveChildrenToFile(nodes, [], path)
    else:
        root = hou.node("/obj")
        root.saveChildrenToFile(root.children(), [], path)
    return [PublishedComponent("houdiniNodes", path)]


def _export_alembic(
    options: ConnectExportOptions,
    *,
    objects_filter: Optional[str] = None,
    root_path: Optional[str] = None,
    object_paths: Optional[str] = None,
) -> PublishedComponent:
    path = _temp_path(".abc")
    obj = hou.node("/obj")
    rop_net = obj.createNode("ropnet")
    try:
        abc = rop_net.createNode("alembic")
        if options.alembic_animation:
            abc.parm("trange").set(1)
            abc.parm("f1").set(options.frame_start)
            abc.parm("f2").set(options.frame_end)
            if abc.parm("f3"):
                abc.parm("f3").set(options.alembic_eval)
        else:
            abc.parm("trange").set(0)

        abc.parm("filename").set(path)

        if object_paths is not None and root_path is not None:
            abc.parm("root").set(root_path)
            abc.parm("objects").set(object_paths)
        elif objects_filter == "selection":
            selected = hou.selectedNodes()
            if not selected:
                raise hou.Error("Nothing selected for Alembic")
            abc.parm("root").set(selected[0].parent().path())
            abc.parm("objects").set(" ".join(n.path() for n in selected))
        else:
            abc.parm("root").set(obj.path())
            abc.parm("objects").set("*")

        if abc.parm("format"):
            abc.parm("format").set("hdf5")
        abc.render()
    finally:
        rop_net.destroy()

    if not os.path.isfile(path):
        raise hou.Error("Alembic ROP did not produce a file")
    return PublishedComponent("alembic", path)


def _export_geometry(options: ConnectExportOptions) -> List[PublishedComponent]:
    out: List[PublishedComponent] = []
    if options.houdini_nodes:
        out.extend(_export_houdini_nodes(options))
    if options.houdini_publish_scene:
        out.extend(_export_scene_only(options))
    if options.alembic:
        mode = "selection" if options.alembic_export_mode_selection else "all"
        out.append(_export_alembic(options, objects_filter=mode))
    if not out:
        raise hou.Error("Enable at least one export option")
    return out


def _bake_camera(node: hou.Node, frame_start: float, frame_end: float) -> hou.Node:
    if "cam" not in node.type().name().lower():
        raise hou.Error("Node is not a camera")
    baked = hou.node("/obj").createNode("cam", f"{node.name()}_bake")
    for res in ("resx", "resy"):
        if baked.parm(res) and node.parm(res):
            baked.parm(res).set(node.parm(res).eval())

    fps = hou.fps()
    for frame in range(int(frame_start), int(frame_end) + 1):
        t = (frame - 1) / fps
        xform = node.worldTransformAtTime(t).explode()
        for key, values in xform.items():
            if "shear" in key:
                continue
            pt = baked.parmTuple(key)
            if pt is None:
                continue
            for i, p in enumerate(pt):
                p.setKeyframe(hou.Keyframe(values[i], t))
    return baked


def _export_camera(options: ConnectExportOptions) -> List[PublishedComponent]:
    cam = hou.selectedNodes()[0]
    baked = _bake_camera(cam, options.frame_start, options.frame_end)
    out: List[PublishedComponent] = []
    try:
        if options.houdini_nodes:
            path = _temp_path(".hip")
            baked.parent().saveChildrenToFile([baked], [], path)
            out.append(PublishedComponent("houdiniNodes", path))
        if options.houdini_publish_scene:
            out.extend(_export_scene_only(options))
        if options.alembic:
            out.append(
                _export_alembic(
                    options,
                    root_path=baked.parent().path(),
                    object_paths=baked.path(),
                )
            )
    finally:
        baked.destroy()
    if not out:
        raise hou.Error("Enable at least one camera export option")
    return out


def add_ftrack_parm_folder(node: hou.Node) -> None:
    """Optional: add Connect-style ftrack metadata parms (empty until import)."""
    group = node.parmTemplateGroup()
    if group.findFolder("ftrack"):
        return
    folder = hou.FolderParmTemplate("ftrack", "ftrack")
    for name in (
        "componentId",
        "componentName",
        "assetVersionId",
        "assetVersion",
        "assetName",
        "assetType",
        "assetId",
    ):
        folder.addParmTemplate(hou.StringParmTemplate(name, name, 1, ""))
    group.append(folder)
    node.setParmTemplateGroup(group)
