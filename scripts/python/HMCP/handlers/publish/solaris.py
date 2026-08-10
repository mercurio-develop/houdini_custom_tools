"""Solaris publish-chain tools (Karma/USD ROP/version-up/cameras) for HMCP."""

from __future__ import annotations

import hou

from modules.usd_solaris_utils import (
    get_stage_from_lop,
    increment_version_token,
    list_usd_cameras,
)
from tools.houdini_lop_utils import connect, get_or_create, set_parms


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


def _create_usd_rop(parent: hou.Node, name: str) -> hou.Node:
    for node_type in ("usdrender_rop", "usd_rop", "usdrender"):
        try:
            return parent.createNode(node_type, name)
        except Exception:
            continue
    raise RuntimeError("Could not create USD render ROP in this LOP context")


def setup_karma_usd_publish_chain(params: dict) -> dict:
    """
    Build publish stack: [input] → Karma → USD ROP → Sublayer/Reference.

    Inspired by common Solaris publish workflows; original implementation.
    """
    parent_path = params.get("parent_path", "/stage")
    input_path = params.get("input_node_path") or params.get("node_path")
    name_prefix = params.get("name_prefix", "publish")
    import_mode = params.get("import_mode", "sublayer")
    picture = params.get("picture", "$JOB/render/$OS/$OS.$F4.exr")
    lop_output = params.get("lop_output", "$JOB/USD/$OS/$OS.usd")

    parent = hou.node(parent_path)
    if parent is None:
        raise ValueError(f"Parent not found: {parent_path}")

    safe_prefix = name_prefix.replace(" ", "_")
    karma_name = increment_version_token(f"{safe_prefix}_karma_").rstrip("_")
    rop_name = increment_version_token(f"{safe_prefix}_USD_")
    import_name = f"import_{rop_name.rstrip('_')}"

    karma = parent.createNode("karmarenderproperties", karma_name)
    rop = _create_usd_rop(parent, rop_name.rstrip("_"))

    if import_mode == "reference":
        import_node = get_or_create(parent, "reference::2.0", import_name)
        set_parms(import_node, {
            "enable": 1,
            "createprims": "off",
            "reftype": "file",
            "primpath": params.get("prim_path", f"/{safe_prefix}"),
        })
        filepath_parm = import_node.parm("filepath1") or import_node.parm("filepath")
        if filepath_parm is not None:
            filepath_parm.set(f'`chs("../{rop.name()}/lopoutput")`')
    else:
        import_node = get_or_create(parent, "sublayer", import_name)
        _set_parm(import_node, ("nfiles", "num_files"), 1)
        filepath_parm = import_node.parm("filepath1") or import_node.parm("sublayerfile1")
        if filepath_parm is not None:
            filepath_parm.set(f'`chs("../{rop.name()}/lopoutput")`')

    _set_parm(karma, ("picture",), picture)
    _set_parm(karma, ("resolution",), params.get("resolution", (1920, 1080)))
    _set_parm(rop, ("lopoutput", "lopoutputpath"), lop_output)

    rs_parm = rop.parm("rendersettings") or rop.parm("karma_settings")
    if rs_parm is not None:
        prim_parm = karma.parm("primpath")
        if prim_parm is not None:
            rs_parm.set(f'`chs("../{karma.name()}/primpath")`')
        else:
            rs_parm.set(karma.path())

    connect(rop, 0, karma)
    connect(import_node, 0, rop)

    input_node = hou.node(input_path) if input_path else None
    if input_node is not None:
        connect(karma, 0, input_node)

    karma.setColor(hou.Color(1.0, 0.32, 0.0))
    rop.setColor(hou.Color(0.38, 0.73, 1.0))
    import_node.setColor(hou.Color(0.0, 0.41, 0.73) if import_mode == "sublayer" else hou.Color(0.2, 0.6, 0.8))
    import_node.setDisplayFlag(True)

    return {
        "karma_node": karma.path(),
        "usd_rop_node": rop.path(),
        "import_node": import_node.path(),
        "import_mode": import_mode,
        "wired_input": input_node.path() if input_node else None,
    }


def version_up_usd_output(params: dict) -> dict:
    """Increment _v### on USD ROP (or given node) and optionally spawn import LOP."""
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    rop_types = {"usdrender_rop", "usd_rop", "usdrender", "componentoutput"}
    if node.type().name() not in rop_types:
        raise ValueError(f"Node type not supported for version-up: {node.type().name()}")

    old_name = node.name()
    new_name = increment_version_token(old_name).rstrip("_")
    if new_name == old_name:
        new_name = increment_version_token(old_name + "_").rstrip("_")

    new_node = node.parent().copyItems([node])[0]
    new_node.setName(new_name, unique_name=True)

    for parm_name in ("lopoutput", "filename", "picture", "vm_picture"):
        parm = new_node.parm(parm_name)
        if parm is None:
            continue
        try:
            expr = parm.unexpandedString()
            if "_v" in expr:
                import re

                updated = re.sub(r"_v(\d+)", lambda m: f"_v{int(m.group(1)) + 1:03d}", expr)
                parm.set(updated)
        except Exception:
            pass

    result = {
        "previous_node": node.path(),
        "new_node": new_node.path(),
        "previous_name": old_name,
        "new_name": new_node.name(),
    }

    if params.get("create_import_lop", False):
        parent = new_node.parent()
        import_mode = params.get("import_mode", "sublayer")
        import_name = f"import_{new_node.name()}"
        if import_mode == "reference":
            import_node = get_or_create(parent, "reference::2.0", import_name)
            set_parms(import_node, {"enable": 1, "createprims": "off", "reftype": "file"})
            filepath_parm = import_node.parm("filepath1")
            if filepath_parm is not None:
                filepath_parm.set(f'`chs("../{new_node.name()}/lopoutput")`')
        else:
            import_node = get_or_create(parent, "sublayer", import_name)
            filepath_parm = import_node.parm("filepath1")
            if filepath_parm is not None:
                filepath_parm.set(f'`chs("../{new_node.name()}/lopoutput")`')
        connect(import_node, 0, new_node)
        import_node.setDisplayFlag(True)
        result["import_node"] = import_node.path()

    return result


def extract_usd_cameras(params: dict) -> dict:
    """Find USD cameras on a cooked LOP stage and create Solaris camera LOP nodes."""
    node_path = params.get("node_path")
    parent_path = params.get("parent_path", "/stage")
    if not node_path:
        raise ValueError("node_path is required")

    source = hou.node(node_path)
    if source is None:
        raise ValueError(f"Node not found: {node_path}")

    stage = get_stage_from_lop(source, params.get("cook_first", True))
    if stage is None:
        raise ValueError("No USD stage found on node or inputs")

    cameras = list_usd_cameras(stage)
    if not cameras:
        return {"node_path": node_path, "count": 0, "cameras": [], "created_nodes": []}

    parent = hou.node(parent_path)
    if parent is None:
        raise ValueError(f"Parent not found: {parent_path}")

    input_node = source
    created = []
    for idx, cam in enumerate(cameras):
        cam_name = cam["name"].replace(" ", "_") or f"cam_{idx}"
        node_name = params.get("name_prefix", "usd_cam") + f"_{cam_name}"
        cam_lop = parent.createNode("camera", node_name)
        connect(cam_lop, 0, input_node)

        prim_path = cam["path"]
        _set_parm(cam_lop, ("primpath", "camera_path"), prim_path)
        _set_parm(cam_lop, ("createcamera", "create_camera"), 1)

        translate = cam.get("translate") or [0, 0, 0]
        rotate = cam.get("rotate") or [0, 0, 0]
        _set_parm(cam_lop, ("t", "tx"), translate[0] if len(translate) > 0 else 0)
        if cam_lop.parmTuple("t"):
            try:
                cam_lop.parmTuple("t").set(translate[:3])
            except Exception:
                pass
        if cam_lop.parmTuple("r"):
            try:
                cam_lop.parmTuple("r").set(rotate[:3])
            except Exception:
                pass

        focal = cam.get("focal_length")
        if focal is not None:
            _set_parm(cam_lop, ("focal", "focalLength"), focal)

        cam_lop.setDisplayFlag(idx == len(cameras) - 1)
        created.append({"usd_path": prim_path, "lop_node": cam_lop.path()})
        input_node = cam_lop

    return {
        "node_path": node_path,
        "count": len(cameras),
        "cameras": cameras,
        "created_nodes": created,
    }
