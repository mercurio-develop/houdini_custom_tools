"""
Asset Library Builder - USD Asset Library Pipeline

Canonical **parts → assembly** API: ``asset_builder.build_from_parts``.

For the primary KB3D assembly shelf UI, use::

    from tools.kb3d_tools import show_assembly_ui
"""

__version__ = "1.1.0"  # Now uses mesh names directly as material names (no conversion)
__author__ = "Custom Tools"

# Convenience imports
from .asset_builder_ui import show_ui

__all__ = ["show_ui"]
