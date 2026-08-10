"""Karma / Solaris render presets for PSX-style output."""

from __future__ import annotations

import hou

from tools.psx_tools.psx_config import PSXAssetConfig


def apply_psx_karma_settings(
    karma_node: hou.Node | None = None,
    config: PSXAssetConfig | None = None,
) -> hou.Node | None:
    """
    Apply low-res, no-AA, low-shadow PSX render defaults to a karmarenderproperties node.

    Creates one under /stage if not provided.
    """
    cfg = config or PSXAssetConfig()
    node = karma_node
    if node is None:
        stage = hou.node("/stage")
        if stage is None:
            return None
        node = stage.createNode("karmarenderproperties", "psx_karma_settings")

    res_x, res_y = cfg.render_resolution
    for parm_name, value in (
        ("resolution", (res_x, res_y)),
        ("resolutionX", res_x),
        ("resolutionY", res_y),
    ):
        p = node.parm(parm_name) or node.parmTuple(parm_name)
        if p is not None:
            try:
                p.set(value)
            except Exception:
                pass

    if cfg.disable_aa:
        for name in ("pixelfilter", "filter", "xfilter", "yfilter"):
            p = node.parm(name)
            if p is not None and p.parmTemplate().type() == hou.parmTemplateType.String:
                try:
                    p.set("box")
                except Exception:
                    pass
        for name in ("xfilterwidth", "yfilterwidth", "filterwidth"):
            p = node.parm(name)
            if p is not None:
                try:
                    p.set(0.01)
                except Exception:
                    pass

    if cfg.disable_denoising:
        for name in ("denoise", "enabledenoise", "denoiseenable"):
            p = node.parm(name)
            if p is not None:
                try:
                    p.set(0)
                except Exception:
                    pass

    if cfg.lowres_shadows:
        for name in ("shadowquality", "shadowmapsize"):
            p = node.parm(name)
            if p is not None:
                try:
                    p.set(128)
                except Exception:
                    pass

    return node
