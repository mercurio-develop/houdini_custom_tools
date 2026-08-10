"""Scene and node inspection handlers for HMCP."""

from __future__ import annotations

import hou


def get_node_errors(params: dict) -> dict:
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    errors = []
    warnings = []
    messages = []

    if hasattr(node, "errors"):
        try:
            raw = node.errors()
            if raw:
                errors.extend(raw if isinstance(raw, (list, tuple)) else [str(raw)])
        except Exception as exc:
            messages.append(f"errors(): {exc}")

    if hasattr(node, "warnings"):
        try:
            raw = node.warnings()
            if raw:
                warnings.extend(raw if isinstance(raw, (list, tuple)) else [str(raw)])
        except Exception as exc:
            messages.append(f"warnings(): {exc}")

    cook_failed = False
    if params.get("cook_first", True):
        try:
            node.cook(force=params.get("force", True))
        except hou.OperationFailed as exc:
            cook_failed = True
            errors.append(str(exc))
        except Exception as exc:
            cook_failed = True
            errors.append(str(exc))

        if hasattr(node, "errors"):
            try:
                post = node.errors()
                if post:
                    for item in post if isinstance(post, (list, tuple)) else [str(post)]:
                        if item not in errors:
                            errors.append(item)
            except Exception:
                pass

    return {
        "node_path": node.path(),
        "type": node.type().name(),
        "cook_failed": cook_failed,
        "errors": errors,
        "warnings": warnings,
        "messages": messages,
        "has_issues": bool(errors or warnings or cook_failed),
    }


def get_cook_chain(params: dict) -> dict:
    node_path = params.get("node_path")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    direction = params.get("direction", "upstream")
    max_depth = int(params.get("max_depth", 32))
    chain = [{"path": node.path(), "type": node.type().name(), "depth": 0}]

    if direction in ("upstream", "both"):
        current = node
        depth = 0
        visited = {node.path()}
        while depth < max_depth:
            inputs = [inp for inp in current.inputs() if inp is not None]
            if not inputs:
                break
            current = inputs[0]
            if current.path() in visited:
                break
            visited.add(current.path())
            depth += 1
            chain.append({"path": current.path(), "type": current.type().name(), "depth": depth})

    if direction in ("downstream", "both"):
        depth = 0
        stack = list(node.outputs())
        visited = {n.path() for n in [node]}
        while stack and depth < max_depth:
            current = stack.pop(0)
            if current.path() in visited:
                continue
            visited.add(current.path())
            depth += 1
            chain.append({"path": current.path(), "type": current.type().name(), "depth": depth})
            stack.extend(current.outputs())

    return {"start": node.path(), "direction": direction, "chain": chain}


def get_parameter_schema(params: dict) -> dict:
    node_path = params.get("node_path")
    parm_name = params.get("parm_name")
    if not node_path:
        raise ValueError("node_path is required")

    node = hou.node(node_path)
    if node is None:
        raise ValueError(f"Node not found: {node_path}")

    parms = []
    for parm in node.parms():
        if parm_name and parm.name() != parm_name:
            continue
        template = parm.parmTemplate()
        entry = {
            "name": parm.name(),
            "label": template.label(),
            "type": template.type().name(),
            "value": _safe_parm_eval(parm),
        }
        if template.type() == hou.parmTemplateType.Menu:
            try:
                entry["menu_items"] = list(template.menuItems())
            except Exception:
                pass
        parms.append(entry)

    return {"node_path": node.path(), "parms": parms}


def _safe_parm_eval(parm: hou.Parm):
    try:
        return parm.eval()
    except Exception:
        return None
