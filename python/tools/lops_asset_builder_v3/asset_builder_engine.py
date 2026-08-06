"""Unified asset build orchestration for GUI, CLI, and batch paths."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import hou

from modules.houdini_node_utils import suppress_gc_during_cook
from modules.misc_utils import MaterialNamingConfig
from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from tools.lops_asset_builder_v3.asset_builder_graph import LookdevBuildOptions, build_lookdev_setup
from tools.lops_asset_builder_v3.asset_builder_progress import (
    ConsoleProgressReporter,
    ProgressLike,
    log_validation_result,
)
from tools.lops_asset_builder_v3.geo_mtl_builder import build_geo_and_mtl_variants
from tools.lops_asset_builder_v3.material_validator import validate_materials
from tools.lops_asset_builder_v3.network_layout import create_organized_net_note


class BuildResult:
    def __init__(
        self,
        success: bool,
        message: str,
        output_node: Optional[hou.Node] = None,
        error: Optional[Exception] = None,
        duration: float = 0.0,
    ):
        self.success = success
        self.message = message
        self.output_node = output_node
        self.error = error
        self.duration = duration

    def __repr__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"BuildResult({status}: {self.message}, duration={self.duration:.2f}s)"


def run_asset_build(
    config: Dict[str, Any] | AssetBuilderConfig,
    progress: ProgressLike | None = None,
) -> BuildResult:
    """Single build pipeline used by interactive, CLI, and batch entry points."""
    start_time = time.time()
    cfg = config if isinstance(config, AssetBuilderConfig) else AssetBuilderConfig.from_dict(config)

    if progress is None:
        progress = ConsoleProgressReporter(verbose=cfg.verbose)

    try:
        with suppress_gc_during_cook():
            progress.set_total(1000)
            if hasattr(progress, "flush_ui"):
                progress.flush_ui()
            progress.step("Validating stage context")
            stage_context = hou.node(cfg.stage_context_path)
            if stage_context is None:
                raise ValueError(f"Stage context not found: {cfg.stage_context_path}")

            if progress.is_cancelled():
                raise KeyboardInterrupt("Cancelled by user")

            expected_material_names = None
            if cfg.validate_materials:
                progress.step("Validating materials")
                naming_config = MaterialNamingConfig.from_ui(lowercase=cfg.lowercase_material_names)
                all_asset_paths = [cfg.main_asset_file_path] + list(cfg.asset_variants)
                texture_variants = (
                    [os.path.basename(v) for v in cfg.mtl_variants] if cfg.mtl_variants else None
                )
                validation_result = validate_materials(
                    asset_paths=all_asset_paths,
                    texture_folder=cfg.folder_textures,
                    texture_variants=texture_variants,
                    naming_config=naming_config,
                    skip_geometry_scan=cfg.skip_geometry_scan,
                    progress=progress,
                )
                for line in validation_result.info:
                    progress.log(line)
                for line in validation_result.warnings:
                    progress.log(f"Warning: {line}")
                log_validation_result(progress, validation_result)
                expected_material_names = sorted(validation_result.materials_expected)
            elif cfg.expected_material_names is not None:
                expected_material_names = list(cfg.expected_material_names)

            if progress.is_cancelled():
                raise KeyboardInterrupt("Cancelled by user")

            progress.step("Building geometry and material variants")
            _geometry_node, comp_out, nodes_to_layout, _comp_material_last = build_geo_and_mtl_variants(
                stage_context=stage_context,
                node_name=cfg.asset_name,
                main_asset_file_path=cfg.main_asset_file_path,
                asset_variants=cfg.asset_variants,
                create_geo_variants=cfg.create_geo_variants,
                asset_vset_name=cfg.asset_vset_name,
                mtl_variants=cfg.mtl_variants,
                folder_textures=cfg.folder_textures,
                mtl_vset_name=cfg.mtl_vset_name,
                skip_matchsize=cfg.skip_matchsize,
                progress=progress,
                lowercase_material_names=cfg.lowercase_material_names,
                use_custom_component_output=cfg.use_custom_component_output,
                expected_material_names=expected_material_names,
            )

            if progress.is_cancelled():
                raise KeyboardInterrupt("Cancelled by user")

            if hasattr(progress, "flush_ui"):
                progress.flush_ui()

            progress.step("Organizing network layout")
            stage_context.layoutChildren(nodes_to_layout)
            create_organized_net_note(
                f"Asset {cfg.asset_name.upper()}",
                nodes_to_layout,
                hou.Vector2(-4, 18),
                create_network_boxes=cfg.create_network_boxes,
            )
            comp_out.setSelected(True, clear_all_selected=True)

            if not cfg.create_lookdev:
                progress.log(
                    "Lookdev setup was not created (disabled in config). "
                    "Enable 'Create Lookdev Setup' to build turntable, camera, and Karma nodes."
                )
                progress.mark_finished("Done (asset only, no lookdev)")
                duration = time.time() - start_time
                return BuildResult(
                    success=True,
                    message=f"Asset built successfully (no lookdev): {comp_out.path()}",
                    output_node=comp_out,
                    duration=duration,
                )

            progress.step("Creating lookdev setup")
            build_lookdev_setup(
                stage_context=stage_context,
                comp_out=comp_out,
                options=LookdevBuildOptions(
                    node_name=cfg.asset_name,
                    create_light_rig=cfg.create_light_rig,
                    enable_env_lights=cfg.enable_env_lights,
                    env_light_paths=cfg.env_light_paths,
                    create_network_boxes=cfg.create_network_boxes,
                ),
                progress=progress,
            )
            comp_out.setSelected(True, clear_all_selected=True)
            progress.mark_finished("Done")
            duration = time.time() - start_time
            return BuildResult(
                success=True,
                message=f"Asset built successfully: {comp_out.path()}",
                output_node=comp_out,
                duration=duration,
            )

    except KeyboardInterrupt as exc:
        duration = time.time() - start_time
        return BuildResult(
            success=False,
            message=f"Build cancelled: {exc}",
            error=exc,
            duration=duration,
        )
    except Exception as exc:
        duration = time.time() - start_time
        return BuildResult(
            success=False,
            message=f"Build failed: {exc}",
            error=exc,
            duration=duration,
        )
