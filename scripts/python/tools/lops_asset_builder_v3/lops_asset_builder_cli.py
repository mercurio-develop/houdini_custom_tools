"""
Command-line interface for LOPS Asset Builder v3.

All builds go through asset_builder_engine.run_asset_build().
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from tools.lops_asset_builder_v3.asset_builder_engine import BuildResult, run_asset_build
from tools.lops_asset_builder_v3.asset_builder_progress import ConsoleProgressReporter

# Backward-compatible alias — config and result types moved to dedicated modules.
__all__ = [
    "AssetBuilderConfig",
    "BuildResult",
    "ConsoleProgressReporter",
    "build_asset",
    "build_asset_from_file",
    "build_assets_batch",
    "create_example_config",
    "quick_build",
]


def build_asset(
    config: Dict[str, Any] | AssetBuilderConfig,
    progress: Optional[ConsoleProgressReporter] = None,
) -> BuildResult:
    return run_asset_build(config, progress=progress)


def build_asset_from_file(config_filepath: str, verbose: bool = True) -> BuildResult:
    try:
        cfg = AssetBuilderConfig.from_json_file(config_filepath)
        cfg.verbose = verbose
        return build_asset(cfg)
    except Exception as exc:
        return BuildResult(
            success=False,
            message=f"Failed to load config file: {exc}",
            error=exc,
        )


def build_assets_batch(
    configs: List[Dict[str, Any] | AssetBuilderConfig],
    verbose: bool = True,
) -> List[BuildResult]:
    results: List[BuildResult] = []
    total = len(configs)
    print(f"\n{'=' * 60}\nBATCH BUILD: Processing {total} assets\n{'=' * 60}\n")

    for i, config in enumerate(configs, 1):
        print(f"\n[BATCH {i}/{total}] Starting build...")
        result = build_asset(config, progress=ConsoleProgressReporter(verbose=verbose))
        results.append(result)
        status = "SUCCESS" if result.success else "FAILED"
        print(f"[BATCH {i}/{total}] {status} - {result.message}")

    print(f"\n{'=' * 60}\nBATCH BUILD SUMMARY\n{'=' * 60}")
    success_count = sum(1 for r in results if r.success)
    print(f"Total: {total} | Success: {success_count} | Failed: {total - success_count}")
    print(f"Total duration: {sum(r.duration for r in results):.2f}s\n{'=' * 60}\n")
    return results


def create_example_config(output_path: str | None = None) -> str:
    example_config = {
        "main_asset_file_path": "/path/to/your/model.abc",
        "folder_textures": "/path/to/your/textures",
        "asset_name": "MyAsset",
        "asset_variants": ["/path/to/variant1.abc"],
        "asset_vset_name": "geo_variant",
        "mtl_variants": ["/path/to/material_variant1"],
        "mtl_vset_name": "mtl_variant",
        "create_lookdev": True,
        "create_light_rig": True,
        "enable_env_lights": True,
        "env_light_paths": ["/path/to/hdri1.exr"],
        "stage_context_path": "/stage",
        "verbose": True,
    }
    if output_path is None:
        output_path = "asset_builder_config_example.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(example_config, f, indent=2)
    print(f"Example config created: {output_path}")
    return output_path


def quick_build(asset_path: str, textures_path: str, **kwargs) -> BuildResult:
    return build_asset(
        {
            "main_asset_file_path": asset_path,
            "folder_textures": textures_path,
            **kwargs,
        }
    )
