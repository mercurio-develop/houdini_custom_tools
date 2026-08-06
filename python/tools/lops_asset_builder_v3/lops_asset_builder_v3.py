"""
Interactive entry point and backward-compatible re-exports for LOPS Asset Builder v3.

Core logic lives in focused modules:
- asset_builder_config   — shared configuration
- asset_builder_engine   — unified build pipeline
- geo_mtl_builder        — geometry + material variants
- material_builder       — texture → MaterialX
- asset_builder_graph    — lookdev / Karma wiring
- network_layout         — network boxes
- asset_builder_ui       — dialogs and Qt progress
"""

from __future__ import annotations

import os

import hou
from PySide6 import QtCore, QtWidgets

from modules.misc_utils import MaterialNamingConfig
from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from tools.lops_asset_builder_v3.asset_builder_engine import run_asset_build
from tools.lops_asset_builder_v3.asset_builder_graph import create_karma_nodes
from tools.lops_asset_builder_v3.asset_builder_progress import log_validation_result
from tools.lops_asset_builder_v3.asset_builder_ui import AssetMaterialVariantsDialog, ProgressReporter
from tools.lops_asset_builder_v3.geo_mtl_builder import build_geo_and_mtl_variants
from tools.lops_asset_builder_v3.material_builder import (
    estimate_materials_in_folder,
    extract_material_names as extract_material_names_from_assets,
)
from tools.lops_asset_builder_v3.network_layout import create_organized_net_note

__all__ = [
    "create_component_builder",
    "build_geo_and_mtl_variants",
    "create_organized_net_note",
    "create_karma_nodes",
    "create_camera_lookdev",
    "extract_material_names_from_assets",
    "estimate_materials_in_folder",
]


def create_component_builder(selected_directory=None):
    """Show the asset builder dialog and run the unified build pipeline."""
    try:
        main_window = hou.qt.mainWindow()
    except Exception:
        main_window = None

    dialog = AssetMaterialVariantsDialog(default_asset="", default_maps="", parent=main_window)
    if dialog.exec_() != QtWidgets.QDialog.DialogCode.Accepted:
        return
    dialog.hide()
    try:
        QtWidgets.QApplication.processEvents(QtCore.QEventLoop.ProcessEventsFlag.AllEvents, 50)
    except Exception:
        pass

    cfg = AssetBuilderConfig.from_dialog(dialog.data())

    progress = ProgressReporter("LOPs Asset Builder v3")
    progress.set_total(1000)
    progress.log("Validating inputs and materials…")
    progress.flush_ui(full=True)

    hou.ui.setStatusMessage("LOPS Asset Builder: validating inputs and materials…")
    try:
        from tools.lops_asset_builder_v3.material_validator import validate_and_warn_user

        naming_config = MaterialNamingConfig.from_ui(lowercase=cfg.lowercase_material_names)
        all_asset_paths = [cfg.main_asset_file_path] + cfg.asset_variants
        _validation_result, user_continues = validate_and_warn_user(
            asset_paths=all_asset_paths,
            texture_folder=cfg.folder_textures,
            texture_variants=[os.path.basename(v) for v in cfg.mtl_variants] if cfg.mtl_variants else None,
            show_dialog=True,
            naming_config=naming_config,
            skip_geometry_scan=False,
            progress=progress,
        )
        progress.flush_ui()
        if not user_continues:
            progress.mark_finished("Cancelled.")
            return
        cfg.validate_materials = False
        cfg.expected_material_names = sorted(_validation_result.materials_expected)
    finally:
        hou.ui.setStatusMessage("")

    try:
        progress.log("Input paths validated.")
        log_validation_result(progress, _validation_result)
        progress.flush_ui()
        result = run_asset_build(cfg, progress=progress)
        if not result.success:
            if result.error:
                raise result.error
            raise RuntimeError(result.message)
    except KeyboardInterrupt as exc:
        progress.log(str(exc))
        progress.mark_finished("Cancelled.")
    except Exception as exc:
        err = f"Error: An error happened in create component builder: {exc}"
        print(err)
        progress.log(err)
        progress.mark_finished("Error.")
        try:
            hou.ui.displayMessage(
                str(exc),
                severity=hou.severityType.Error,
                title="LOPS Asset Builder — Build Failed",
            )
        except Exception:
            pass
        try:
            if progress._use_qt and progress._dialog is not None:
                progress._dialog.present()
        except Exception:
            pass


def create_camera_lookdev(parent, asset_name: str):
    """Create the python SOP used to spawn a lookdev camera (legacy helper)."""
    python_sop = parent.createNode("pythonscript", "lookdev_camera")
    python_sop.parm("python").set(
        f'from tools import lops_lookdev_camera\nlops_lookdev_camera.create_lookdev_camera("{asset_name}")\n'
    )
    return python_sop
