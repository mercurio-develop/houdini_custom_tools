"""Safe helpers for Houdini node/parm setup (H21→H22 compatibility)."""


def safe_parm(node, name):
    if node is None:
        return None
    return node.parm(name)


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
