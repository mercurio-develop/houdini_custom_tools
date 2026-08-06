"""
LOPS Asset Builder v3

Modular USD/Solaris asset builder with geometry variants, materials, lookdev, and Karma.

Architecture:
- asset_builder_config    — shared AssetBuilderConfig
- asset_builder_engine    — unified run_asset_build() pipeline
- asset_builder_progress  — ProgressLike protocol + console reporter
- geo_mtl_builder         — geometry import + variant wiring
- material_builder        — texture scan + MaterialX creation
- asset_builder_graph     — lookdev / light rig / Karma LOP graph
- network_layout          — network box organization
- asset_builder_ui        — dialogs + Qt progress
- lops_asset_builder_v3   — interactive shelf entry
- lops_asset_builder_cli  — headless / batch JSON builds
- batch_asset_builder     — batch scanner UI
"""

from .lops_asset_builder_v3 import create_component_builder
from .batch_asset_builder import show_batch_asset_builder

__all__ = ["create_component_builder", "show_batch_asset_builder"]
