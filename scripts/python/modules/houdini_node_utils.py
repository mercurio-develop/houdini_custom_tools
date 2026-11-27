"""Safe helpers for Houdini node/parm setup (H21→H22 compatibility)."""

import gc
from contextlib import contextmanager

import hou


@contextmanager
def suppress_gc_during_cook():
    """Prevent Python GC from destroying Qt wrappers while Houdini cooks LOP/VOP nodes."""
    was_enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if was_enabled:
            gc.enable()


def safe_parm(node, name):
    if node is None:
        return None
    return node.parm(name)


def set_parm(node, name, value, required=False):
    """Set a node parm when present; optionally raise if missing."""
    if node is None:
        if required:
            raise hou.Error(f"Cannot set parm '{name}': node is None")
        return False
    parm = node.parm(name)
    if parm is None:
        if required:
            raise hou.Error(f"Node {node.path()} missing parm '{name}'")
        return False
    parm.set(value)
    return True


def safe_parm_tuple(node, name):
    if node is None:
        return None
    return node.parmTuple(name)


def unlock_parm(parm):
    if parm is not None:
        parm.lock(False)


def unlock_parm_tuple(parm_tuple, locks):
    if parm_tuple is not None:
        parm_tuple.lock(locks)


def reset_parm(parm, value, autoscope=None, unlock=True):
    if parm is None:
        return
    if unlock:
        parm.lock(False)
    parm.deleteAllKeyframes()
    parm.set(value)
    if autoscope is not None:
        parm.setAutoscope(autoscope)


def reset_parm_tuple(parm_tuple, value, autoscope=None, locks=None):
    if parm_tuple is None:
        return
    if locks is not None:
        parm_tuple.lock(locks)
    else:
        parm_tuple.lock(False)
    parm_tuple.deleteAllKeyframes()
    parm_tuple.set(value)
    if autoscope is not None:
        parm_tuple.setAutoscope(autoscope)


def is_inside_locked_library_hda(node) -> bool:
    """Return True if *node* lives inside a locked non-Embedded library HDA."""
    cur = node.parent() if node is not None else None
    while cur is not None:
        try:
            if cur.isLockedHDA():
                defn = cur.type().definition()
                if defn is not None and defn.libraryFilePath() != "Embedded":
                    return True
        except Exception:
            pass
        cur = cur.parent()
    return False


def iter_author_nodes(root):
    """Yield descendant nodes under *root*, skipping locked SideFX/library HDA internals."""
    if root is None:
        return
    for child in root.allSubChildren():
        if not is_inside_locked_library_hda(child):
            yield child


def set_karma_resolution(karma_node, width: int, height: int) -> tuple[int, int] | None:
    """Set Karma render resolution safely in Houdini 22 (unlocks & strips autoheight expression on resolutiony)."""
    if karma_node is None:
        return None
    res_mode = karma_node.parm("res_mode")
    if res_mode is not None:
        try:
            res_mode.set("manual")
        except Exception:
            pass
    for pname in ("resolutionx", "resolutiony"):
        p = karma_node.parm(pname)
        if p is not None:
            if p.isLocked():
                p.lock(False)
            p.deleteAllKeyframes()
    res_tuple = karma_node.parmTuple("resolution")
    if res_tuple is not None:
        res_tuple.set((int(width), int(height)))
        return tuple(int(v) for v in res_tuple.eval())
    px = karma_node.parm("resolutionx") or karma_node.parm("resolutionX")
    py = karma_node.parm("resolutiony") or karma_node.parm("resolutionY")
    if px is not None and py is not None:
        px.set(int(width))
        py.set(int(height))
        return (int(px.eval()), int(py.eval()))
    return None
