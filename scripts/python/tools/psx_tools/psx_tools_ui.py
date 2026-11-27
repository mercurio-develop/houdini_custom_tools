"""Simple UI for PSX asset tools."""

from __future__ import annotations

import os

import hou
from PySide6 import QtWidgets

from tools.psx_tools.psx_asset_builder import apply_psx_to_selected_geo, run_psx_asset_build
from tools.psx_tools.psx_config import PSXAssetConfig, PSXBuildConfig
from tools.psx_tools.texture_process import process_texture_folder


class PSXToolsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PSX Retro Tools for Houdini")
        self.setMinimumWidth(480)

        layout = QtWidgets.QFormLayout(self)

        self.asset_path = QtWidgets.QLineEdit()
        self.texture_folder = QtWidgets.QLineEdit()
        self.decimate = QtWidgets.QDoubleSpinBox()
        self.decimate.setRange(0.05, 1.0)
        self.decimate.setSingleStep(0.05)
        self.decimate.setValue(0.5)
        self.palette = QtWidgets.QSpinBox()
        self.palette.setRange(2, 256)
        self.palette.setValue(16)
        self.tex_size = QtWidgets.QComboBox()
        self.tex_size.addItems(["64", "128", "256", "512"])
        self.tex_size.setCurrentText("128")
        self.dither = QtWidgets.QComboBox()
        self.dither.addItems(["BAYER", "FLOYD_STEINBERG", "ATKINSON", "STUCKI"])
        self.wobble = QtWidgets.QCheckBox("Vertex Wobble")
        self.triangulate = QtWidgets.QCheckBox("Triangulate")
        self.triangulate.setChecked(True)
        self.process_tex = QtWidgets.QCheckBox("Dither Textures")
        self.process_tex.setChecked(True)
        self.run_builder = QtWidgets.QCheckBox("Run LOPs Asset Builder")
        self.run_builder.setChecked(True)

        btn_asset = QtWidgets.QPushButton("Browse…")
        btn_asset.clicked.connect(self._browse_asset)
        btn_tex = QtWidgets.QPushButton("Browse…")
        btn_tex.clicked.connect(self._browse_textures)

        asset_row = QtWidgets.QHBoxLayout()
        asset_row.addWidget(self.asset_path)
        asset_row.addWidget(btn_asset)
        tex_row = QtWidgets.QHBoxLayout()
        tex_row.addWidget(self.texture_folder)
        tex_row.addWidget(btn_tex)

        layout.addRow("Asset File", asset_row)
        layout.addRow("Texture Folder", tex_row)
        layout.addRow("Decimate Ratio", self.decimate)
        layout.addRow("Triangulate", self.triangulate)
        layout.addRow("Vertex Wobble", self.wobble)
        layout.addRow("Texture Size", self.tex_size)
        layout.addRow("Palette Size", self.palette)
        layout.addRow("Dither Method", self.dither)
        layout.addRow("", self.process_tex)
        layout.addRow("", self.run_builder)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        sop_only = QtWidgets.QPushButton("SOP Only (Selection)")
        sop_only.clicked.connect(self._sop_only)
        buttons.addButton(sop_only, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        buttons.accepted.connect(self._run)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _browse_asset(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select Asset", "", "Geometry (*.fbx *.obj *.abc *.bgeo *.bgeo.sc)"
        )
        if path:
            self.asset_path.setText(path)

    def _browse_textures(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Texture Folder")
        if path:
            self.texture_folder.setText(path)

    def _psx_config(self) -> PSXAssetConfig:
        return PSXAssetConfig(
            decimate_ratio=self.decimate.value(),
            triangulate=self.triangulate.isChecked(),
            apply_vertex_wobble=self.wobble.isChecked(),
            texture_size=int(self.tex_size.currentText()),
            palette_size=self.palette.value(),
            dither_method=self.dither.currentText(),
            process_textures=self.process_tex.isChecked(),
        )

    def _sop_only(self) -> None:
        apply_psx_to_selected_geo(self._psx_config())
        self.accept()

    def _run(self) -> None:
        asset = self.asset_path.text().strip()
        textures = self.texture_folder.text().strip()
        if self.run_builder.isChecked() and (not asset or not textures):
            hou.ui.displayMessage(
                "Asset file and texture folder are required for full build.",
                severity=hou.severityType.Warning,
            )
            return

        if self.process_tex.isChecked() and textures and os.path.isdir(textures):
            process_texture_folder(
                textures,
                palette_size=self.palette.value(),
                dither_method=self.dither.currentText(),
                max_size=int(self.tex_size.currentText()),
            )

        if self.run_builder.isChecked():
            build = PSXBuildConfig(
                main_asset_file_path=asset,
                folder_textures=textures,
                asset_name=os.path.splitext(os.path.basename(asset))[0],
                psx=self._psx_config(),
            )
            run_psx_asset_build(build)

        self.accept()


def show_psx_tools_dialog() -> None:
    try:
        parent = hou.qt.mainWindow()
    except Exception:
        parent = None
    dlg = PSXToolsDialog(parent=parent)
    dlg.exec_()
