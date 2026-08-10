"""
USD Library Toolkit — KB3D-style USD authoring, BGEO conversion, and assembly UI.

Primary UI::

    from tools.kb3d_tools import show_assembly_ui
    show_assembly_ui()

Canonical parts → assembly API::

    from tools.asset_library_builder.asset_builder import build_from_parts
"""

from tools.kb3d_tools.kb3d_proper_assembly_builder_ui import show_ui as show_assembly_ui

__all__ = ["show_assembly_ui"]
