"""Bridge PSX preprocessing with LOPs Asset Builder v3."""

from __future__ import annotations

import os

import hou

from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from tools.lops_asset_builder_v3.asset_builder_engine import run_asset_build
from tools.lops_asset_builder_v3.asset_builder_progress import ConsoleProgressReporter, ProgressLike
from tools.psx_tools.karma_presets import apply_psx_karma_settings
from tools.psx_tools.psx_config import PSXBuildConfig
from tools.psx_tools.psx_sop_pipeline import patch_geo_import_with_psx
from tools.psx_tools.texture_process import process_texture_folder, resolve_psx_texture_folder


def run_psx_asset_build(build: PSXBuildConfig, progress: ProgressLike | None = None) -> bool:
    """
    Full PSX asset pipeline:
    1. Dither/downscale textures (optional)
    2. Run LOPs Asset Builder
    3. Patch component geometry SOPs with PSX effects
    4. Apply Karma PSX render preset (optional)
    """
    if progress is None:
        if hou.isUIAvailable():
            from tools.lops_asset_builder_v3.asset_builder_ui import ProgressReporter

            progress = ProgressReporter("PSX Asset Builder")
        else:
            progress = ConsoleProgressReporter(verbose=True)

    texture_folder = build.folder_textures
    if build.psx.process_textures and texture_folder and os.path.isdir(texture_folder):
        progress.log("Processing textures for PSX look…")
        process_texture_folder(
            texture_folder,
            palette_size=build.psx.palette_size,
            dither_method=build.psx.dither_method,
            dither_scale=build.psx.dither_scale,
            max_size=build.psx.texture_size,
            progress=progress.log,
        )
        texture_folder = resolve_psx_texture_folder(texture_folder)

    if not build.run_lops_asset_builder:
        progress.mark_finished("PSX texture pass complete.")
        return True

    cfg = AssetBuilderConfig(
        main_asset_file_path=build.main_asset_file_path,
        folder_textures=texture_folder,
        asset_name=build.asset_name,
        stage_context_path=build.stage_context_path,
        create_lookdev=True,
    )

    progress.log("Running LOPs Asset Builder…")
    result = run_asset_build(cfg, progress=progress)
    if not result.success:
        progress.mark_finished("Asset build failed.")
        return False

    comp_out = result.output_node
    if comp_out is not None:
        _patch_psx_on_built_asset(comp_out, build.psx, progress)

    apply_psx_karma_settings(config=build.psx)
    progress.mark_finished("PSX asset build complete.")
    return True


def _patch_psx_on_built_asset(comp_out: hou.Node, psx_cfg, progress: ProgressLike) -> None:
    """Walk upstream componentgeometry nodes and insert PSX SOP chains."""
    visited: set[str] = set()
    stack = list(comp_out.inputs())
    while stack:
        node = stack.pop()
        if node is None or node.path() in visited:
            continue
        visited.add(node.path())
        if node.type().name() == "componentgeometry":
            progress.log(f"Applying PSX SOP chain: {node.path()}")
            patch_geo_import_with_psx(node, psx_cfg)
        stack.extend(node.inputs())


def apply_psx_to_selected_geo(config=None) -> None:
    """Shelf helper: apply PSX SOP chain to selected SOP node output."""
    from tools.psx_tools.psx_config import PSXAssetConfig
    from tools.psx_tools.psx_sop_pipeline import apply_psx_sop_chain

    cfg = config or PSXAssetConfig()
    sel = hou.selectedNodes()
    if not sel:
        hou.ui.displayMessage("Select a SOP node.", severity=hou.severityType.Warning)
        return
    node = sel[0]
    parent = node.parent()
    apply_psx_sop_chain(parent, node, cfg)
    hou.ui.displayMessage("PSX SOP chain applied.", title="PSX Tools")
