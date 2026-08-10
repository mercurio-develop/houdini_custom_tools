"""Material creation from textures and MaterialX templates."""

from __future__ import annotations

import os
import time
from typing import TYPE_CHECKING

import hou
import voptoolutils
from pxr import UsdGeom

from modules.houdini_node_utils import suppress_gc_during_cook
from modules.misc_utils import MaterialNamingConfig
from tools.lops_asset_builder_v3.network_layout import find_prims_by_attribute
from tools.lops_asset_builder_v3.texture_scan_utils import (
    resolve_texture_search_roots,
    walk_texture_dirs,
)

if TYPE_CHECKING:
    from tools.lops_asset_builder_v3.asset_builder_progress import ProgressLike


def make_texture_scanner(naming_config: MaterialNamingConfig | None = None):
    from tools.material_tools.TexToMtlX_V2.tex_to_mtlx import TextureFolderScanner

    return TextureFolderScanner(naming_config)


def create_mtlx_templates(parent, material_lib) -> None:
    stage = parent.stage()
    prims_name = find_prims_by_attribute(stage, UsdGeom.Mesh)
    for name in prims_name:
        voptoolutils._setupMtlXBuilderSubnet(
            subnet_node=None,
            destination_node=material_lib,
            name=name,
            mask=voptoolutils.MTLX_TAB_MASK,
            folder_label="MaterialX Builder",
            render_context="mtlx",
        )
    material_lib.layoutChildren()


def extract_material_names(asset_paths, lowercase: bool = False) -> list[str]:
    from tools.lops_asset_builder_v3.material_validator import extract_material_names_from_geometry

    return sorted(extract_material_names_from_geometry(asset_paths, lowercase=lowercase))


def estimate_materials_in_folder(folder_textures: str, expected_names=None) -> int:
    try:
        folder_textures_check = os.path.normpath(folder_textures or "")
        if not folder_textures_check or not os.path.exists(folder_textures_check):
            return 0
        material_handler = make_texture_scanner()
        combined_texture_list = {}
        for search_root in resolve_texture_search_roots(folder_textures_check):
            if not search_root or not os.path.isdir(search_root):
                continue
            for root, _dirs, _files in walk_texture_dirs(search_root):
                current_folder = root.replace(os.sep, "/")
                if material_handler.folder_with_textures(current_folder):
                    folder_texture_list = material_handler.get_texture_details(current_folder)
                    if folder_texture_list and isinstance(folder_texture_list, dict):
                        combined_texture_list.update(folder_texture_list)
        if not combined_texture_list:
            return 0
        if expected_names:
            expected_set = set(expected_names)
            return sum(1 for n in combined_texture_list if n in expected_set)
        return len(combined_texture_list)
    except Exception:
        return 0


def _run_with_optional_suspend(progress: "ProgressLike | None", fn) -> None:
    if progress and hasattr(progress, "suspend_events"):
        with progress.suspend_events(), suppress_gc_during_cook():
            fn()
        if hasattr(progress, "flush_ui"):
            progress.flush_ui()
    else:
        with suppress_gc_during_cook():
            fn()


def create_materials(
    parent,
    folder_textures: str,
    material_lib,
    expected_names=None,
    progress: "ProgressLike | None" = None,
    naming_config: MaterialNamingConfig | None = None,
) -> bool:
    """Create MaterialX shaders from textures or fall back to template materials."""
    if naming_config is None:
        naming_config = MaterialNamingConfig()
    try:
        from tools.material_tools import MtlxMaterial

        if progress:
            progress.ensure_total(1000)

        folder_textures_check = os.path.normpath(folder_textures)
        if progress:
            progress.log(f"Scanning texture folder: {folder_textures_check}")
            try:
                progress.step("Scanning texture folders…")
            except Exception:
                pass

        if not os.path.exists(folder_textures_check):
            warn1 = f"Warning: Texture folder does not exist: {folder_textures_check}"
            warn2 = (
                f"Warning: Texture folder not found: {folder_textures}. "
                "Creating template materials instead."
            )
            if progress:
                progress.log(warn1)
                progress.log(warn2)
                try:
                    for _ in range(3):
                        progress.step("Texture folder missing; creating template materials…")
                except Exception:
                    pass
            else:
                print(warn1)
                print(warn2)
            _run_with_optional_suspend(progress, lambda: create_mtlx_templates(parent, material_lib))
            return True

        material_handler = make_texture_scanner(naming_config)
        combined_texture_list: dict = {}
        valid_folders_found = False

        search_roots = resolve_texture_search_roots(folder_textures_check)
        if progress and len(search_roots) == 1 and search_roots[0] != folder_textures_check:
            progress.log(f"Resolved texture scan root: {search_roots[0]}")

        for search_root in search_roots:
            if not search_root or not os.path.isdir(search_root):
                continue
            for root, _dirs, _files in walk_texture_dirs(search_root):
                if progress and progress.is_cancelled():
                    raise KeyboardInterrupt("Cancelled by user")
                current_folder = root.replace(os.sep, "/")
                if material_handler.folder_with_textures(current_folder):
                    valid_folders_found = True
                    folder_texture_list = material_handler.get_texture_details(current_folder)
                    if folder_texture_list and isinstance(folder_texture_list, dict):
                        combined_texture_list.update(folder_texture_list)
                    if progress:
                        try:
                            progress.step(f"Found textures in: {os.path.basename(current_folder)}")
                        except Exception:
                            pass

        if valid_folders_found and combined_texture_list:
            start_time = time.perf_counter()
            common_data = {
                "mtlTX": False,
                "path": material_lib.path(),
                "node": material_lib,
            }
            total_to_create = sum(
                1
                for material_name in combined_texture_list
                if not expected_names or material_name in expected_names
            )
            created_so_far = 0
            if progress:
                progress.log(f"Creating up to {total_to_create} materials in {material_lib.path()}")
                try:
                    for _ in range(min(5, max(1, total_to_create // 10))):
                        progress.step("Preparing material creation…")
                except Exception:
                    pass

            per_mat_steps = max(1, 800 // total_to_create) if total_to_create > 0 else 1

            for material_name in combined_texture_list:
                if progress and progress.is_cancelled():
                    raise KeyboardInterrupt("Cancelled by user")
                if expected_names and material_name not in expected_names:
                    continue

                path = combined_texture_list[material_name]["FOLDER_PATH"]
                if not path.endswith("/"):
                    combined_texture_list[material_name]["FOLDER_PATH"] = path + "/"

                create_material = MtlxMaterial(
                    material_name,
                    **common_data,
                    folder_path=path,
                    texture_list=combined_texture_list,
                    naming_config=naming_config,
                )
                _run_with_optional_suspend(progress, create_material.create_materialx)

                created_so_far += 1
                if progress:
                    try:
                        progress.step(
                            f"Created material {created_so_far}/{total_to_create}: {material_name}"
                        )
                        for _ in range(per_mat_steps - 1):
                            progress.step()
                    except Exception:
                        pass
                    if created_so_far % 5 == 0 or created_so_far == total_to_create:
                        progress.log(f"Created {created_so_far}/{total_to_create} materials…")

            elapsed = time.perf_counter() - start_time
            msg = f"Created {created_so_far} materials in {material_lib.path()} in {elapsed:.2f}s"
            if progress:
                progress.log(msg)
                try:
                    for _ in range(5):
                        progress.step()
                except Exception:
                    pass
            else:
                print(msg)
            return True

        _run_with_optional_suspend(progress, lambda: create_mtlx_templates(parent, material_lib))
        msg = "No valid textures sets found in folder or subfolders"
        if progress:
            progress.log(msg)
            try:
                for _ in range(5):
                    progress.step("No textures found; using template materials…")
            except Exception:
                pass
        else:
            print(msg)
        return True
    except Exception as exc:
        err = f"Error creating materials: {exc}"
        if progress:
            progress.log(err)
        else:
            print(err)
        return False
