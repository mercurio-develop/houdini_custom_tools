"""Deep USD / Solaris inspection and authoring handlers for HMCP."""

from __future__ import annotations

import os
import shutil
import subprocess

import hou

from tools.houdini_lop_utils import build_reference2, connect, get_or_create, set_parms


def _resolve_lop_stage(node_path: str, cook_first: bool = True) -> tuple[hou.Node, object]:
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")
    if not hasattr(node, "stage"):
        raise ValueError(f"Node has no USD stage: {node_path}")

    if cook_first:
        node.cook(force=True)

    stage = node.stage()
    if stage is None:
        raise ValueError(f"No USD stage after cook: {node_path}")
    return node, stage


def _serialize_usd_value(value) -> object:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str)):
        return value
    try:
        return [float(x) for x in value]
    except TypeError:
        pass
    try:
        return str(value)
    except Exception:
        return repr(value)


def _attribute_info(attr) -> dict:
    if not attr or not attr.IsValid():
        return {"valid": False}
    value = None
    try:
        value = attr.Get()
    except Exception as exc:
        value = f"<read error: {exc}>"
    return {
        "name": attr.GetName(),
        "type": str(attr.GetTypeName()),
        "value": _serialize_usd_value(value),
        "valid": True,
        "has_authored_value": attr.HasAuthoredValue(),
        "variability": str(attr.GetVariability()),
    }


def get_usd_stage_info(params: dict) -> dict:
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    root = stage.GetRootLayer()

    prim_count = 0
    type_counts: dict[str, int] = {}
    max_count = int(params.get("max_type_samples", 5000))
    for prim in stage.Traverse():
        prim_count += 1
        if prim_count > max_count:
            break
        type_name = prim.GetTypeName()
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    start_time = end_time = None
    try:
        start_time = stage.GetStartTimeCode()
        end_time = stage.GetEndTimeCode()
    except Exception:
        pass

    return {
        "node_path": node.path(),
        "root_layer": root.identifier if root else None,
        "default_prim": stage.GetDefaultPrim() or (root.defaultPrim if root else None),
        "up_axis": str(stage.GetUpAxis()) if hasattr(stage, "GetUpAxis") else None,
        "meters_per_unit": stage.GetMetersPerUnit(),
        "start_time_code": start_time,
        "end_time_code": end_time,
        "prim_count": prim_count,
        "truncated": prim_count > max_count,
        "type_counts": dict(sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))),
    }


def inspect_usd_attribute(params: dict) -> dict:
    node_path = params.get("node_path")
    prim_path = params.get("prim_path", "/")
    attr_name = params.get("attribute_name") or params.get("attr_name")
    time_code = params.get("time_code")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return {"node_path": node_path, "prim_path": prim_path, "found": False}

    if attr_name:
        attr = prim.GetAttribute(attr_name)
        if not attr or not attr.IsValid():
            return {"node_path": node_path, "prim_path": prim_path, "attribute_name": attr_name, "found": False}
        if time_code is not None:
            try:
                from pxr import Usd
                attr_value = attr.Get(Usd.TimeCode(float(time_code)))
            except Exception as exc:
                return {"found": True, "attribute_name": attr_name, "read_error": str(exc)}
            return {
                "node_path": node_path,
                "prim_path": prim_path,
                "found": True,
                "attribute": {**_attribute_info(attr), "value": _serialize_usd_value(attr_value), "time_code": time_code},
            }
        return {
            "node_path": node_path,
            "prim_path": prim_path,
            "found": True,
            "attribute": _attribute_info(attr),
        }

    attributes = []
    max_attrs = int(params.get("max_attributes", 100))
    for attr in prim.GetAttributes():
        attributes.append(_attribute_info(attr))
        if len(attributes) >= max_attrs:
            break

    return {
        "node_path": node_path,
        "prim_path": prim_path,
        "found": True,
        "attribute_count": len(attributes),
        "attributes": attributes,
    }


def get_usd_bounding_box(params: dict) -> dict:
    node_path = params.get("node_path")
    prim_path = params.get("prim_path", "/")
    purpose = params.get("purpose", "default")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return {"node_path": node_path, "prim_path": prim_path, "found": False}

    from pxr import Usd, UsdGeom

    time_code = Usd.TimeCode(float(params["time_code"])) if params.get("time_code") is not None else Usd.TimeCode.Default()
    purposes = [UsdGeom.Tokens.default_]
    if purpose == "render":
        purposes = [UsdGeom.Tokens.render]
    elif purpose == "proxy":
        purposes = [UsdGeom.Tokens.proxy]
    elif purpose == "guide":
        purposes = [UsdGeom.Tokens.guide]

    cache = UsdGeom.BBoxCache(time_code, purposes)
    bound = cache.ComputeWorldBound(prim)
    box = bound.ComputeAlignedBox()
    if box.IsEmpty():
        return {"node_path": node_path, "prim_path": prim_path, "found": True, "empty": True}

    min_pt = box.GetMin()
    max_pt = box.GetMax()
    size = max_pt - min_pt
    center = (min_pt + max_pt) * 0.5
    return {
        "node_path": node_path,
        "prim_path": prim_path,
        "found": True,
        "empty": False,
        "world_bounds": {
            "min": [min_pt[i] for i in range(3)],
            "max": [max_pt[i] for i in range(3)],
            "size": [size[i] for i in range(3)],
            "center": [center[i] for i in range(3)],
        },
    }


def get_usd_layer_stack(params: dict) -> dict:
    node_path = params.get("node_path")
    prim_path = params.get("prim_path", "/")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    root = stage.GetRootLayer()

    stack = {
        "root_layer": root.identifier if root else None,
        "default_prim": root.defaultPrim if root else None,
        "sub_layers": list(root.subLayerPaths) if root else [],
        "session_layer": stage.GetSessionLayer().identifier if stage.GetSessionLayer() else None,
    }

    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return {"node_path": node_path, "prim_path": prim_path, "found": False, "stack": stack}

    references = []
    for item in prim.GetReferences().GetAddedOrExplicitItems():
        references.append({"asset_path": str(item.assetPath), "prim_path": str(item.primPath)})

    payloads = []
    for item in prim.GetPayloads().GetAddedOrExplicitItems():
        payloads.append({"asset_path": str(item.assetPath), "prim_path": str(item.primPath)})

    prim_stack = []
    try:
        for spec in prim.GetPrimStack():
            prim_stack.append({
                "layer": spec.layer.identifier if spec.layer else None,
                "path": str(spec.path),
            })
    except Exception:
        pass

    return {
        "node_path": node_path,
        "prim_path": prim_path,
        "found": True,
        "stack": stack,
        "references": references,
        "payloads": payloads,
        "prim_stack": prim_stack[: int(params.get("max_composition_nodes", 50))],
    }


def list_variant_sets(params: dict) -> dict:
    node_path = params.get("node_path")
    prim_path = params.get("prim_path", "/")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return {"node_path": node_path, "prim_path": prim_path, "found": False}

    variant_sets = []
    vsets = prim.GetVariantSets()
    for set_name in vsets.GetNames():
        vset = vsets.GetVariantSet(set_name)
        variant_sets.append({
            "name": set_name,
            "selection": vset.GetVariantSelection(),
            "variants": list(vset.GetVariantNames()),
        })

    return {
        "node_path": node_path,
        "prim_path": prim_path,
        "found": True,
        "variant_set_count": len(variant_sets),
        "variant_sets": variant_sets,
    }


def set_variant_selection(params: dict) -> dict:
    variant_set = params.get("variant_set") or params.get("variantset")
    variant_name = params.get("variant_name") or params.get("variant")
    prim_path = params.get("prim_path", "/")
    mode = params.get("mode", "session")

    if not variant_set or not variant_name:
        raise ValueError("variant_set and variant_name are required")

    node_path = params.get("node_path")
    if mode == "create_lop":
        parent_path = params.get("parent_path", "/stage")
        input_path = params.get("input_node_path") or node_path
        parent = hou.node(parent_path)
        if parent is None:
            raise ValueError(f"Parent not found: {parent_path}")

        setvar = get_or_create(parent, "setvariant", params.get("node_name", "hmcp_setvariant"))
        if input_path:
            input_node = hou.node(input_path)
            if input_node is not None:
                connect(setvar, 0, input_node)

        set_parms(setvar, {
            "num_variants": 1,
            "enable1": 1,
            "primpattern1": prim_path,
            "variantset1": variant_set,
            "variantname1": variant_name,
        })
        setvar.setDisplayFlag(True)
        return {
            "mode": "create_lop",
            "node_path": setvar.path(),
            "prim_path": prim_path,
            "variant_set": variant_set,
            "variant_name": variant_name,
        }

    if not node_path:
        raise ValueError("node_path is required for session mode")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        raise ValueError(f"Prim not found: {prim_path}")

    from pxr import Usd
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        prim.GetVariantSets().SetSelection(variant_set, variant_name)

    return {
        "mode": "session",
        "node_path": node.path(),
        "prim_path": prim_path,
        "variant_set": variant_set,
        "variant_name": variant_name,
        "applied": True,
    }


def create_usd_reference_lop(params: dict) -> dict:
    usd_path = params.get("usd_path") or params.get("filepath")
    if not usd_path:
        raise ValueError("usd_path is required")

    usd_path = hou.text.expandString(usd_path)
    if not os.path.isfile(usd_path):
        raise ValueError(f"USD file not found: {usd_path}")

    parent_path = params.get("parent_path", "/stage")
    parent = hou.node(parent_path)
    if parent is None:
        raise ValueError(f"Parent not found: {parent_path}")

    input_path = params.get("input_node_path")
    prim_path = params.get("prim_path") or f"/{os.path.splitext(os.path.basename(usd_path))[0]}"
    ref_type = params.get("reference_type", "reference")
    node_name = params.get("node_name") or f"ref_{os.path.splitext(os.path.basename(usd_path))[0]}"

    if ref_type in ("reference::2.0", "reference2"):
        ref = build_reference2(parent, node_name, prim_path, params.get("ref_prim_path") or prim_path)
        filepath_parm = ref.parm("filepath1") or ref.parm("filepath")
        if filepath_parm is not None:
            filepath_parm.set(usd_path)
    else:
        ref = parent.createNode("reference", node_name)
        ref.parm("primpath").set(prim_path)
        for enable_name, file_name in (("enable1", "filepath1"), ("enable", "filepath")):
            enable = ref.parm(enable_name)
            filepath = ref.parm(file_name)
            if enable is not None and filepath is not None:
                enable.set(1)
                filepath.set(usd_path)
                break

    if input_path:
        input_node = hou.node(input_path)
        if input_node is not None:
            connect(ref, 0, input_node)

    if params.get("set_display_flag", True):
        ref.setDisplayFlag(True)

    return {
        "reference_node": ref.path(),
        "usd_path": usd_path,
        "prim_path": prim_path,
        "reference_type": ref.type().name(),
        "parent_path": parent.path(),
    }


def set_default_prim(params: dict) -> dict:
    default_prim = params.get("default_prim") or params.get("prim_name")
    if not default_prim:
        raise ValueError("default_prim is required")

    mode = params.get("mode", "session")
    node_path = params.get("node_path")

    if mode == "create_lop":
        parent_path = params.get("parent_path", "/stage")
        input_path = params.get("input_node_path") or node_path
        parent = hou.node(parent_path)
        if parent is None:
            raise ValueError(f"Parent not found: {parent_path}")

        cfg = get_or_create(parent, "configurelayer", params.get("node_name", "hmcp_set_default_prim"))
        if input_path:
            input_node = hou.node(input_path)
            if input_node is not None:
                connect(cfg, 0, input_node)

        for parm_name in ("defaultprim", "defaultprimname", "setdefaultprim"):
            parm = cfg.parm(parm_name)
            if parm is not None:
                parm.set(default_prim)
                break
        set_parms(cfg, {"setdefaultprim": 1, "setstagemetadata": 1})
        cfg.setDisplayFlag(True)
        return {"mode": "create_lop", "node_path": cfg.path(), "default_prim": default_prim}

    if not node_path:
        raise ValueError("node_path is required for session mode")

    node, stage = _resolve_lop_stage(node_path, params.get("cook_first", True))
    prim = stage.GetPrimAtPath(f"/{default_prim.lstrip('/')}")
    if not prim or not prim.IsValid():
        prim = stage.GetPrimAtPath(default_prim)
    if not prim or not prim.IsValid():
        raise ValueError(f"Prim not found for defaultPrim: {default_prim}")

    from pxr import Usd
    with Usd.EditContext(stage, stage.GetSessionLayer()):
        stage.SetDefaultPrim(prim)

    return {
        "mode": "session",
        "node_path": node.path(),
        "default_prim": prim.GetName(),
        "applied": True,
    }


def validate_usd_file(params: dict) -> dict:
    usd_path = params.get("usd_path") or params.get("file_path")
    if not usd_path:
        raise ValueError("usd_path is required")

    usd_path = hou.text.expandString(os.path.abspath(usd_path))
    if not os.path.isfile(usd_path):
        raise ValueError(f"File not found: {usd_path}")

    from pxr import Usd

    stage = Usd.Stage.Open(usd_path)
    if stage is None:
        return {"usd_path": usd_path, "valid": False, "errors": ["Failed to open USD stage"]}

    errors = []
    warnings = []
    root = stage.GetRootLayer()

    if not root.defaultPrim:
        warnings.append("No defaultPrim authored on root layer")

    prim_count = 0
    inactive = 0
    undef_types = 0
    for prim in stage.Traverse():
        prim_count += 1
        if not prim.IsActive():
            inactive += 1
        if not prim.GetTypeName():
            undef_types += 1

    if prim_count == 0:
        errors.append("Stage contains no prims")

    usdchecker = shutil.which("usdchecker")
    checker_output = None
    if params.get("run_usdchecker", True) and usdchecker:
        try:
            proc = subprocess.run(
                [usdchecker, usd_path],
                capture_output=True,
                text=True,
                timeout=int(params.get("timeout", 120)),
                check=False,
            )
            checker_output = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode != 0:
                errors.append(f"usdchecker exited with code {proc.returncode}")
        except Exception as exc:
            warnings.append(f"usdchecker failed: {exc}")

    return {
        "usd_path": usd_path,
        "valid": not errors,
        "default_prim": root.defaultPrim,
        "up_axis": str(stage.GetUpAxis()) if hasattr(stage, "GetUpAxis") else None,
        "meters_per_unit": stage.GetMetersPerUnit(),
        "prim_count": prim_count,
        "inactive_prim_count": inactive,
        "undefined_type_prim_count": undef_types,
        "errors": errors,
        "warnings": warnings,
        "usdchecker_available": bool(usdchecker),
        "usdchecker_output": checker_output,
    }
