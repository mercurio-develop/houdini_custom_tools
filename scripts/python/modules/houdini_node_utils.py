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
