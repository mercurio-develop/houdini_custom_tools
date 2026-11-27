"""PSX / PS1-style retro asset tools for Houdini Solaris (lazy UI imports for headless safety)."""

from __future__ import annotations

from tools.psx_tools.psx_config import PSXAssetConfig, PSXBuildConfig


def apply_psx_sop_chain(*args, **kwargs):
    from tools.psx_tools.psx_sop_pipeline import apply_psx_sop_chain as _fn

    return _fn(*args, **kwargs)


def show_psx_tools_dialog(*args, **kwargs):
    from tools.psx_tools.psx_tools_ui import show_psx_tools_dialog as _fn

    return _fn(*args, **kwargs)


__all__ = [
    "PSXAssetConfig",
    "PSXBuildConfig",
    "apply_psx_sop_chain",
    "show_psx_tools_dialog",
]
