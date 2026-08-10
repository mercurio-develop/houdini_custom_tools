"""
PySide6 dialog for selecting asset/material variants for the LOPS asset builder.
Pure UI: no LOP logic inside. Returns a dict via .data().

Fields:
- Main Asset File Path (file picker, Geometry)
- Asset Name (auto-filled from Main Asset File Path; editable)
- Asset Variant Set name (default: geo_variant)
- Asset Variant Files list (multi select, Geometry)
- Main Textures Folder (folder picker)
- Material Variant Set name (default: mtl_variant)
- Material Variant Folders list (multi select, folders)

Buttons: OK / Cancel, Add/Remove for both lists.

Python 3.11, PySide6.
"""
from __future__ import annotations

from typing import List, Dict
import os

import hou
from PySide6 import QtWidgets, QtCore, QtGui

from ui.houdini_theme import HoudiniTheme

# Keep strong references to active progress reporters to prevent dialogs
# from being garbage-collected (and auto-closing) when build functions return.
_LIVE_REPORTERS: list["ProgressReporter"] = []


def _basename_variant(name: str) -> str:
    base = os.path.basename(name.rstrip("/\\"))
    # Replace spaces with underscores and limit length
    base = base.replace(" ", "_")[:64] if base else "item"
    return base


class _PathLineEdit(QtWidgets.QLineEdit):
    """Path field that keeps the filename / trailing folder visible when blurred."""

    def setText(self, text: str) -> None:
        super().setText(text)
        self._sync_path_display()

    def _sync_path_display(self) -> None:
        text = self.text()
        if text:
            self.setToolTip(text)
            if not self.hasFocus():
                self.setCursorPosition(len(text))
        else:
            self.setToolTip("")

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        if not self.hasFocus():
            self._sync_path_display()

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        super().focusOutEvent(event)
        self._sync_path_display()


def _make_path_list_item(path: str) -> QtWidgets.QListWidgetItem:
    """List row for a full path; tooltip holds the complete string."""
    item = QtWidgets.QListWidgetItem(path)
    item.setToolTip(path)
    return item


def _section_subtitle(text: str, parent: QtWidgets.QWidget | None = None) -> QtWidgets.QLabel:
    label = QtWidgets.QLabel(text, parent)
    try:
        c = HoudiniTheme.colors()
        label.setStyleSheet(
            f"color: {c['text_secondary']}; font-size: {HoudiniTheme.FONTS['default_size']}px; "
            "padding: 0; margin: 0 0 2px 0;"
        )
        label.setWordWrap(True)
    except Exception:
        pass
    return label


def _compact_primary_button_style() -> str:
    try:
        c = HoudiniTheme.colors()
        # Dark dialog background on accent fill — matches Houdini highlight button contrast.
        text_color = c["background"]
        return (
            f"QPushButton {{ background-color: {c['accent_primary']}; color: {text_color}; "
            f"border: 1px solid {c['accent_primary']}; font-weight: 600; font-size: 11px; "
            f"padding: 3px 8px; min-height: 20px; }}"
            f"QPushButton:hover {{ background-color: {c['accent_secondary']}; "
            f"border-color: {c['accent_secondary']}; color: {text_color}; }}"
            f"QPushButton:disabled {{ background-color: {c['disabled']}; "
            f"color: {c['disabled_text']}; border-color: {c['disabled']}; }}"
        )
    except Exception:
        return ""


def _compact_secondary_button_style() -> str:
    try:
        c = HoudiniTheme.colors()
        return (
            f"QPushButton {{ background-color: {c['surface']}; color: {c['text']}; "
            f"border: 1px solid {c['border']}; font-weight: normal; font-size: 11px; "
            f"padding: 3px 8px; min-height: 20px; }}"
            f"QPushButton:hover {{ background-color: {c['hover']}; border-color: {c['accent_primary']}; "
            f"color: {c['text']}; }}"
            f"QPushButton:disabled {{ color: {c['disabled_text']}; border-color: {c['disabled']}; }}"
        )
    except Exception:
        return ""


class _PathPickerRow(QtWidgets.QWidget):
    """Single-line path field with a browse button."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        placeholder: str = "",
        browse_label: str = "Browse…",
        browse_tooltip: str = "",
    ) -> None:
        super().__init__(parent)
        self.line_edit = _PathLineEdit()
        if placeholder:
            self.line_edit.setPlaceholderText(placeholder)
        self.btn_browse = QtWidgets.QPushButton(browse_label)
        self.btn_browse.setMinimumWidth(68)
        self.btn_browse.setMaximumWidth(84)
        if browse_tooltip:
            self.btn_browse.setToolTip(browse_tooltip)
        style = _compact_secondary_button_style()
        if style:
            self.btn_browse.setStyleSheet(style)

        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.line_edit, 1)
        row.addWidget(self.btn_browse, 0)

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, value: str) -> None:
        self.line_edit.setText(value)
        self.line_edit._sync_path_display()

    def textChanged(self):
        return self.line_edit.textChanged


class _ListEditor(QtWidgets.QWidget):
    """Reusable list editor with Add/Remove buttons inside a panel frame."""

    def __init__(
        self,
        parent: QtWidgets.QWidget | None,
        mode: str = "file",
        file_filter: str | None = None,
        *,
        add_label: str = "Add…",
        remove_label: str = "Remove",
        list_min_height: int = 96,
    ) -> None:
        super().__init__(parent)
        self.mode = mode  # "file" or "dir"
        self.file_filter = file_filter
        self._add_label = add_label
        self._remove_label = remove_label
        self._list_min_height = list_min_height
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        panel = QtWidgets.QFrame()
        panel.setObjectName("listEditorPanel")
        try:
            c = HoudiniTheme.colors()
            panel.setStyleSheet(
                f"#listEditorPanel {{"
                f"  background-color: {c['surface']};"
                f"  border: 1px solid {c['border']};"
                f"  border-radius: {HoudiniTheme.LAYOUT['border_radius']}px;"
                f"  padding: 4px;"
                f"}}"
                f"#listEditorPanel QListWidget {{"
                f"  background-color: {c['input_background']};"
                f"  border: 1px solid {c['border']};"
                f"  border-radius: {HoudiniTheme.LAYOUT['border_radius']}px;"
                f"  min-height: 0;"
                f"}}"
            )
        except Exception:
            pass

        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.setContentsMargins(8, 8, 8, 8)
        panel_layout.setSpacing(6)

        self.listw = QtWidgets.QListWidget(panel)
        self.listw.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # Elide the prefix so the added file/folder name stays visible on the right.
        self.listw.setTextElideMode(QtCore.Qt.TextElideMode.ElideLeft)
        self.listw.setUniformItemSizes(True)
        self.listw.setWordWrap(False)
        self.listw.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listw.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.listw.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        panel_layout.addWidget(self.listw)
        outer.addWidget(panel)

        model = self.listw.model()
        if model is not None:
            model.rowsInserted.connect(lambda *_args: self._sync_list_height())
            model.rowsRemoved.connect(lambda *_args: self._sync_list_height())
        self._sync_list_height()

        btns = QtWidgets.QHBoxLayout()
        btns.setContentsMargins(0, 0, 0, 0)
        btns.setSpacing(8)
        self.btn_add = QtWidgets.QPushButton(self._add_label)
        self.btn_remove = QtWidgets.QPushButton(self._remove_label)
        self.btn_add.setMinimumWidth(92)
        self.btn_remove.setMinimumWidth(76)
        self.btn_add.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        add_style = _compact_primary_button_style()
        remove_style = _compact_secondary_button_style()
        if add_style:
            self.btn_add.setStyleSheet(add_style)
        if remove_style:
            self.btn_remove.setStyleSheet(remove_style)
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_remove)
        btns.addStretch(1)
        outer.addLayout(btns)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)

    def _sync_list_height(self) -> None:
        """Grow list to fit items; outer dialog scroll area handles overflow."""
        count = self.listw.count()
        row_h = self.listw.sizeHintForRow(0) if count else 0
        if row_h <= 0:
            row_h = 22
        rows = max(3, count)
        height = max(self._list_min_height, rows * row_h + 6)
        self.listw.setFixedHeight(height)

    def items(self) -> List[str]:
        return [self.listw.item(i).text() for i in range(self.listw.count())]

    def set_items(self, values: List[str]) -> None:
        self.listw.clear()
        for v in values:
            if not v:
                continue
            self.listw.addItem(_make_path_list_item(v))
        self._sync_list_height()

    def append_item(self, path: str) -> None:
        if not path:
            return
        self.listw.addItem(_make_path_list_item(path))
        self._sync_list_height()

    def _on_add(self) -> None:
        if self.mode == "file":
            title = "Select files"
            flt = self.file_filter or "Geometry (*.usd *.usda *.usdc *.abc *.obj *.bgeo *.bgeo.sc);;All Files (*)"
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(
                self,
                title,
                "",
                flt,
            )
            for f in files or []:
                if f:
                    self.listw.addItem(_make_path_list_item(f))
        else:
            dir_ = QtWidgets.QFileDialog.getExistingDirectory(self, "Select folder")
            if dir_:
                self.listw.addItem(_make_path_list_item(dir_))
        self._sync_list_height()

    def _on_remove(self) -> None:
        for it in self.listw.selectedItems():
            row = self.listw.row(it)
            self.listw.takeItem(row)
        self._sync_list_height()


class AssetMaterialVariantsDialog(QtWidgets.QDialog):
    """Small dialog to collect asset/material variant authoring data.

    Accept returns True when OK is pressed and data is valid, False otherwise.
    Use data() to retrieve a dictionary with all fields.
    """

    def __init__(self, default_asset: str = "", default_maps: str = "", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        HoudiniTheme.setup_modal_dialog(
            self,
            title="LOPS Asset Builder",
            min_width=620,
            min_height=520,
            resizable=True,
        )
        self.setModal(True)
        self._build_ui(default_asset, default_maps)
        self._apply_contrast_layers()

    def _apply_contrast_layers(self) -> None:
        """Extra layering so sections, panels, and inputs read clearly apart."""
        try:
            c = HoudiniTheme.colors()
            self.setObjectName("assetBuilderDialog")
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                #assetBuilderDialog {{
                    background-color: {c["background"]};
                }}
                #assetBuilderDialog QScrollArea QWidget {{
                    background-color: transparent;
                }}
                #assetBuilderDialog QGroupBox {{
                    background-color: {c["surface"]};
                    border: 1px solid {c["border"]};
                }}
                #assetBuilderDialog QGroupBox::title {{
                    font-size: {HoudiniTheme.FONTS["header_size"]}px;
                    font-weight: bold;
                    color: {c["accent_primary"]};
                }}
                #assetBuilderDialog QLineEdit {{
                    background-color: {c["input_background"]};
                    border: 1px solid {c["border"]};
                }}
                #assetBuilderDialog QLineEdit:focus {{
                    border: 1px solid {c["border_focus"]};
                }}
                #assetBuilderDialog QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                #assetBuilderDialog QScrollBar:vertical {{
                    background: transparent;
                    width: 10px;
                    margin: 2px 0 2px 2px;
                }}
                #assetBuilderDialog QScrollBar::handle:vertical {{
                    background: {c["border"]};
                    border-radius: 5px;
                    min-height: 28px;
                }}
                #assetBuilderDialog QScrollBar::handle:vertical:hover {{
                    background: {c["accent_primary"]};
                }}
                #assetBuilderDialog QScrollBar::add-line:vertical,
                #assetBuilderDialog QScrollBar::sub-line:vertical,
                #assetBuilderDialog QScrollBar::add-page:vertical,
                #assetBuilderDialog QScrollBar::sub-page:vertical {{
                    height: 0;
                    background: none;
                }}
                """
            )
        except Exception:
            pass

    @staticmethod
    def _apply_button_styles(btn_box: QtWidgets.QDialogButtonBox) -> None:
        """Compact, softer buttons for OK/Cancel only in this dialog."""
        ok_btn = btn_box.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        cancel_btn = btn_box.button(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        primary = _compact_primary_button_style()
        secondary = _compact_secondary_button_style()
        if ok_btn and primary:
            ok_btn.setStyleSheet(primary)
        if cancel_btn and secondary:
            cancel_btn.setStyleSheet(secondary)

    @staticmethod
    def _make_section(title: str, subtitle: str | None = None) -> tuple[QtWidgets.QGroupBox, QtWidgets.QVBoxLayout]:
        group = QtWidgets.QGroupBox(title)
        inner = QtWidgets.QVBoxLayout(group)
        inner.setContentsMargins(12, 14, 12, 12)
        inner.setSpacing(10)
        if subtitle:
            inner.addWidget(_section_subtitle(subtitle))
        return group, inner

    @staticmethod
    def _form_field(label: str, widget: QtWidgets.QWidget, *, tooltip: str = "") -> tuple[QtWidgets.QLabel, QtWidgets.QWidget]:
        lbl = QtWidgets.QLabel(label)
        lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignTop)
        lbl.setMinimumWidth(HoudiniTheme.LAYOUT["form_label_min_width"])
        if tooltip:
            lbl.setToolTip(tooltip)
            widget.setToolTip(tooltip)
        return lbl, widget

    def _build_ui(self, default_asset: str, default_maps: str) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        # ── Geometry ──────────────────────────────────────────────────────
        geo_group, geo_layout = self._make_section(
            "Geometry",
            "Main asset file, optional geo variants, and naming options.",
        )
        geo_form = QtWidgets.QFormLayout()
        HoudiniTheme.apply_form_layout(geo_form)
        geo_form.setVerticalSpacing(10)
        geo_form.setHorizontalSpacing(12)

        self.ed_main_asset = _PathPickerRow(
            placeholder="Select main geometry file…",
            browse_label="Browse…",
            browse_tooltip="Pick the primary geometry file (USD, ABC, BGEO, OBJ…)",
        )
        self.ed_main_asset.setText(default_asset or "")
        self.ed_main_asset.btn_browse.clicked.connect(self._pick_asset)
        lbl, w = self._form_field("Main Asset File", self.ed_main_asset)
        geo_form.addRow(lbl, w)

        self.ed_asset_name = QtWidgets.QLineEdit("")
        self.ed_asset_name.setPlaceholderText("Auto-filled from file name")
        lbl, w = self._form_field("Asset Name", self.ed_asset_name)
        geo_form.addRow(lbl, w)
        self._user_edited_asset_name = False
        self.ed_asset_name.textEdited.connect(self._on_asset_name_edited)
        self.ed_main_asset.textChanged().connect(self._on_main_asset_changed)
        self._on_main_asset_changed(self.ed_main_asset.text())

        self.ed_asset_vset = QtWidgets.QLineEdit("geo_variant")
        lbl, w = self._form_field("Asset Variant Set", self.ed_asset_vset)
        geo_form.addRow(lbl, w)

        self.asset_list = _ListEditor(
            self,
            mode="file",
            add_label="Add Files…",
            remove_label="Remove",
            list_min_height=88,
        )
        lbl, w = self._form_field(
            "Asset Variant Files",
            self.asset_list,
            tooltip="Optional extra geometry files included as USD variants.",
        )
        geo_form.addRow(lbl, w)

        options_box = QtWidgets.QWidget()
        options_layout = QtWidgets.QVBoxLayout(options_box)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(6)
        self.cb_create_geo_variants = QtWidgets.QCheckBox("Create Geometry Variants")
        self.cb_create_geo_variants.setChecked(True)
        self.cb_create_geo_variants.setToolTip(
            "Include geometry variants if provided (disable to use only main geometry file)"
        )
        self.cb_lowercase_material_names = QtWidgets.QCheckBox("Lowercase Material Names")
        self.cb_lowercase_material_names.setChecked(False)
        self.cb_lowercase_material_names.setToolTip(
            "Convert material names to lowercase (enable for legacy compatibility)"
        )
        options_layout.addWidget(self.cb_create_geo_variants)
        options_layout.addWidget(self.cb_lowercase_material_names)
        lbl, w = self._form_field("Options", options_box)
        geo_form.addRow(lbl, w)

        geo_layout.addLayout(geo_form)
        content_layout.addWidget(geo_group)

        # ── Textures & Materials ──────────────────────────────────────────
        tex_group, tex_layout = self._make_section(
            "Textures & Materials",
            "Texture root folder and optional material variant folders.",
        )
        tex_form = QtWidgets.QFormLayout()
        HoudiniTheme.apply_form_layout(tex_form)
        tex_form.setVerticalSpacing(10)
        tex_form.setHorizontalSpacing(12)

        self.ed_main_maps = _PathPickerRow(
            placeholder="Select textures root folder…",
            browse_label="Browse…",
            browse_tooltip="Folder containing texture sets (or KB3D Textures subfolder)",
        )
        self.ed_main_maps.setText(default_maps or "")
        self.ed_main_maps.btn_browse.clicked.connect(self._pick_folder)
        lbl, w = self._form_field("Main Textures Folder", self.ed_main_maps)
        tex_form.addRow(lbl, w)

        self.ed_look_vset = QtWidgets.QLineEdit("mtl_variant")
        lbl, w = self._form_field("Material Variant Set", self.ed_look_vset)
        tex_form.addRow(lbl, w)

        self.maps_list = _ListEditor(
            self,
            mode="dir",
            add_label="Add Folders…",
            remove_label="Remove",
            list_min_height=88,
        )
        maps_tip = "Optional. Leave empty to auto-detect material variant folders from the main textures folder."
        self.maps_list.setToolTip(maps_tip)
        lbl, w = self._form_field("Material Variant Folders", self.maps_list, tooltip=maps_tip)
        tex_form.addRow(lbl, w)
        try:
            self.maps_list.btn_add.clicked.disconnect()
        except Exception:
            pass
        self.maps_list.btn_add.clicked.connect(self._on_add_multiple_material_folders)

        tex_layout.addLayout(tex_form)
        content_layout.addWidget(tex_group)

        # ── Lookdev & Rendering ───────────────────────────────────────────
        look_group, look_layout = self._make_section(
            "Lookdev & Rendering",
            "Turntable setup, lighting, and optional HDRI environment maps.",
        )
        look_form = QtWidgets.QFormLayout()
        HoudiniTheme.apply_form_layout(look_form)
        look_form.setVerticalSpacing(10)
        look_form.setHorizontalSpacing(12)

        look_opts = QtWidgets.QWidget()
        look_opts_layout = QtWidgets.QVBoxLayout(look_opts)
        look_opts_layout.setContentsMargins(0, 0, 0, 0)
        look_opts_layout.setSpacing(6)
        self.cb_create_lookdev = QtWidgets.QCheckBox("Create Lookdev Setup")
        self.cb_create_lookdev.setChecked(True)
        self.cb_create_light_rig = QtWidgets.QCheckBox("Setup Light Rig")
        self.cb_create_light_rig.setChecked(True)
        self.cb_enable_env_lights = QtWidgets.QCheckBox("Enable Environment Lights")
        self.cb_enable_env_lights.setChecked(True)
        look_opts_layout.addWidget(self.cb_create_lookdev)
        look_opts_layout.addWidget(self.cb_create_light_rig)
        look_opts_layout.addWidget(self.cb_enable_env_lights)
        lbl, w = self._form_field("Pipeline", look_opts)
        look_form.addRow(lbl, w)

        image_filter = "Images (*.exr *.hdr *.rat *.jpg *.jpeg *.png *.tif *.tiff);;All Files (*)"
        self.env_lights_list = _ListEditor(
            self,
            mode="file",
            file_filter=image_filter,
            add_label="Add HDRI…",
            remove_label="Remove",
            list_min_height=72,
        )
        lbl, w = self._form_field(
            "Env Light HDRI Paths",
            self.env_lights_list,
            tooltip="Optional HDRI files used when environment lights are enabled.",
        )
        look_form.addRow(lbl, w)

        look_layout.addLayout(look_form)
        content_layout.addWidget(look_group)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        self.cb_create_lookdev.toggled.connect(self._on_lookdev_toggled)
        self.cb_enable_env_lights.toggled.connect(self._update_env_lights_enabled)
        self._on_lookdev_toggled(self.cb_create_lookdev.isChecked())

        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
            | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.setContentsMargins(0, 4, 0, 0)
        root.addWidget(btn_box)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        self._apply_button_styles(btn_box)

        self.resize(640, 720)

    def _pick_multiple_directories(self) -> List[str]:
        """Open a non-native QFileDialog that allows selecting multiple directories.
        Returns a list of absolute folder paths, or an empty list if cancelled.
        """
        dlg = QtWidgets.QFileDialog(self, "Select folders")
        dlg.setFileMode(QtWidgets.QFileDialog.Directory)
        dlg.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, True)
        dlg.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
        # Enable multi-selection in the views inside the non-native dialog
        try:
            # PySide does not support passing a tuple to findChildren, query each type separately
            for cls in (QtWidgets.QListView, QtWidgets.QTreeView):
                for view in dlg.findChildren(cls):
                    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        except Exception:
            # Fallback: try all child widgets and set where applicable
            for view in dlg.findChildren(QtWidgets.QWidget):
                if isinstance(view, (QtWidgets.QListView, QtWidgets.QTreeView)):
                    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # Support both Qt5/PySide2 (exec_) and Qt6/PySide6 (exec)
        exec_fn = getattr(dlg, "exec", None) or getattr(dlg, "exec_", None)
        if exec_fn and exec_fn():
            # selectedFiles returns directories when in Directory mode
            return [os.path.normpath(p) for p in dlg.selectedFiles() if p]
        return []

    def _on_add_multiple_material_folders(self) -> None:
        """Handler for the 'Add Folders…' button under Material Variant Folders."""
        folders = self._pick_multiple_directories()
        if not folders:
            return
        # Avoid duplicates by checking existing items
        existing = set(self.maps_list.items())
        for d in folders:
            if not d or d in existing:
                continue
            self.maps_list.append_item(d)
            existing.add(d)

    def _pick_asset(self) -> None:
        val, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select main geometry file",
            self.ed_main_asset.text() or "",
            "Geometry (*.usd *.usda *.usdc *.abc *.obj *.bgeo *.bgeo.sc);;All Files (*)",
        )
        if val:
            self.ed_main_asset.setText(val)

    def _pick_folder(self) -> None:
        start_dir = self.ed_main_maps.text() or ""
        val = QtWidgets.QFileDialog.getExistingDirectory(self, "Select texture folder", start_dir)
        if val:
            self.ed_main_maps.setText(val)

    # Helpers for Asset Name auto-fill
    def _derive_asset_name(self, path: str) -> str:
        base = os.path.basename(path) if path else ""
        if not base:
            return ""
        # Strip .bgeo.sc specially, otherwise strip last extension
        if base.endswith(".bgeo.sc"):
            base = base[:-len(".bgeo.sc")]
        else:
            if "." in base:
                base = base.split(".")[0]
        return base

    def _on_asset_name_edited(self, _text: str) -> None:
        # Mark that user manually edited; stop auto-updating
        self._user_edited_asset_name = True

    def _on_main_asset_changed(self, text: str) -> None:
        if not self._user_edited_asset_name:
            derived = self._derive_asset_name(text)
            self.ed_asset_name.setText(derived)

    def _on_lookdev_toggled(self, enabled: bool) -> None:
        # Enable/disable dependent widgets when Lookdev is toggled
        self.cb_create_light_rig.setEnabled(bool(enabled))
        # The env lights list is enabled only if lookdev is on AND the env lights checkbox is checked
        self.cb_enable_env_lights.setEnabled(bool(enabled))
        self._update_env_lights_enabled()

    def _update_env_lights_enabled(self) -> None:
        # Called when either lookdev toggle or env checkbox changes
        enabled = bool(self.cb_create_lookdev.isChecked()) and bool(self.cb_enable_env_lights.isChecked())
        self.env_lights_list.setEnabled(enabled)

    def data(self) -> Dict[str, object]:
        return {
            "main_asset_file_path": self.ed_main_asset.text().strip(),
            "asset_name_input": self.ed_asset_name.text().strip(),
            "asset_variant_set": (self.ed_asset_vset.text().strip() or "geo_variant"),
            "asset_variants": [s for s in self.asset_list.items() if s],
            "create_geo_variants": bool(self.cb_create_geo_variants.isChecked()),
            "lowercase_material_names": bool(self.cb_lowercase_material_names.isChecked()),
            "material_variant_set": (self.ed_look_vset.text().strip() or "mtl_variant"),
            "main_textures": self.ed_main_maps.text().strip(),
            "material_variants": [s for s in self.maps_list.items() if s],
            "create_lookdev_setup": bool(self.cb_create_lookdev.isChecked()),
            "create_light_rig": bool(self.cb_create_light_rig.isChecked()),
            "enable_env_lights": bool(self.cb_enable_env_lights.isChecked()),
            "env_light_paths": [s for s in self.env_lights_list.items() if s],
        }


class SimpleProgressDialog(QtWidgets.QDialog):
    def __init__(self, title="LOPs Asset Builder v3", parent=None):
        # Must stay top-level: parenting to hou.qt.mainWindow() hides the window on H22.
        super().__init__(None)
        self.setModal(False)
        HoudiniTheme.setup_tool_window(
            self,
            title=title,
            min_width=700,
            min_height=640,
        )
        try:
            self.resize(800, 640)
            self.setSizeGripEnabled(True)
        except Exception:
            pass
        layout = QtWidgets.QVBoxLayout(self)
        self.title_label = QtWidgets.QLabel(title)
        self.progress_bar = QtWidgets.QProgressBar()
        self.message_label = QtWidgets.QLabel("")
        self.log_edit = QtWidgets.QTextEdit()
        self.log_edit.setReadOnly(True)
        # Configure log appearance and behavior
        # Wrap long lines to the widget width to avoid horizontal growth and x-scroll during processing
        self.log_edit.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth)
        # Break even very long "words" (paths, code) so x-scrollbar never appears
        self.log_edit.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)
        # Keep horizontal scrollbar hidden to prevent accidental horizontal scrolling
        self.log_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.log_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.log_edit.setStyleSheet(
            "background-color: #111; color: #eee; font-family: Consolas, 'Courier New', monospace; font-size: 12px;"
        )
        layout.addWidget(self.title_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.message_label)
        layout.addWidget(self.log_edit)
        # Bottom help text: inform user about ESC
        self.help_label = QtWidgets.QLabel("*Press ESC to cancel. Press ESC again to request FORCE KILL (third press will exit the app). The Close button is enabled after completion.")
        try:
            self.help_label.setStyleSheet("color: #bbb; font-size: 11px; font-style: italic; margin-top: 6px;")
            self.help_label.setWordWrap(True)
        except Exception:
            pass
        layout.addWidget(self.help_label)
        # Bottom button row with Close button (disabled until finished)
        btn_row = QtWidgets.QHBoxLayout()
        btn_row.addStretch(1)
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.setEnabled(False)
        try:
            self.close_btn.clicked.connect(self.close)
        except Exception:
            pass
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)
        self._max = 100
        self.progress_bar.setRange(0, self._max)
        try:
            self.progress_bar.setFormat("%p%")
        except Exception:
            pass
        # Internal flags
        self.cancelled = False
        self.finished = False
        # Escalated kill support
        self._esc_presses = 0
        self.force_kill = False

    def present(self) -> None:
        """Show and bring the progress window to the front."""
        try:
            HoudiniTheme.center_on_houdini(self)
        except Exception:
            pass
        self.show()
        try:
            self.setWindowState(
                (self.windowState() & ~QtCore.Qt.WindowState.WindowMinimized)
                | QtCore.Qt.WindowState.WindowActive
            )
            self.raise_()
            self.activateWindow()
        except Exception:
            pass
        self.refresh()

    def _on_kill(self):
        # Increment ESC press count and escalate actions
        self._esc_presses += 1
        if self._esc_presses == 1:
            # Soft cancel: let the builder stop gracefully
            self.cancelled = True
            self.log_edit.append("User requested cancel (ESC). Stopping after current step…")
        elif self._esc_presses == 2:
            # Force kill requested: try to abort ASAP
            self.cancelled = True
            self.force_kill = True
            self.log_edit.append("User requested FORCE KILL (ESC x2). Attempting immediate abort… Press ESC again to exit application.")
        else:
            # Third time: exit the application event loop (last resort)
            self.cancelled = True
            self.force_kill = True
            self.log_edit.append("ESC pressed 3 times — exiting application event loop now.")
            try:
                QtCore.QCoreApplication.exit(1)
            except Exception:
                pass
        QtWidgets.QApplication.processEvents()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        # Use ESC to kill the process instead of buttons
        if event.key() == QtCore.Qt.Key_Escape:
            self._on_kill()
            # Do not pass to base to avoid default QDialog reject/close
            return
        return super().keyPressEvent(event)

    def set_total(self, total: int):
        self._max = max(1, int(total))
        self.progress_bar.setRange(0, self._max)

    def set_value(self, value: int):
        self.progress_bar.setValue(max(0, min(int(value), self._max)))

    def set_message(self, msg: str):
        self.message_label.setText(msg)

    def log(self, msg: str):
        self.log_edit.append(msg)
        try:
            self.log_edit.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        except Exception:
            self.log_edit.ensureCursorVisible()

    def refresh(self) -> None:
        try:
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents, 50
            )
        except Exception:
            pass

    def repaint_widgets(self) -> None:
        """Force immediate paint without pumping Qt events (safe during LOP/VOP cooks)."""
        try:
            self.log_edit.viewport().repaint()
            self.log_edit.repaint()
            self.progress_bar.repaint()
            self.message_label.repaint()
            self.title_label.repaint()
            self.repaint()
        except Exception:
            pass

    def mark_finished(self):
        self.finished = True
        try:
            self.close_btn.setEnabled(True)
            self.close_btn.setFocus()
        except Exception:
            pass
        self.message_label.setText("Finished.")
        self.refresh()


class ProgressReporter:
    def __init__(self, title="LOPs Asset Builder v3"):
        self._use_qt = False
        self._step = 0
        self._total = 100
        self._dialog = None
        self._cancelled = False
        self._suspend_events = False
        self._title = title
        try:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                self._dialog = SimpleProgressDialog(title)
                try:
                    self._dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
                except Exception:
                    pass
                self._dialog.present()
                self._use_qt = True
                self._register_self()
                try:
                    self._dialog.destroyed.connect(lambda _obj=None: self._on_dialog_destroyed())
                except Exception:
                    pass
                print(f"[{title}] Progress window opened.")
                self.flush_ui(full=True)
            else:
                print(f"[{title}] No Qt application — logging to console / status bar.")
        except Exception as exc:
            print(f"[{title}] Progress window unavailable ({exc}) — logging to console / status bar.")
            self._use_qt = False

    def flush_ui(self, *, full: bool = False) -> None:
        """Show the progress window and pump Qt so logs/bar paint before heavy work."""
        if not self._use_qt or self._dialog is None:
            return
        try:
            self._dialog.present()
            flags = (
                QtCore.QEventLoop.ProcessEventsFlag.AllEvents
                if full
                else QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents
            )
            QtWidgets.QApplication.processEvents(flags, 80)
            self._dialog.repaint_widgets()
        except Exception:
            pass

    def set_total(self, total: int):
        self._total = max(1, int(total))
        if self._use_qt:
            self._dialog.set_total(self._total)

    def ensure_total(self, minimum: int) -> None:
        """Raise the step budget if the caller set it too low (e.g. before material creation)."""
        minimum = max(1, int(minimum))
        if self._total < minimum:
            self.set_total(minimum)

    def step(self, message: str = None):
        self._step += 1
        if self.is_cancelled():
            raise KeyboardInterrupt("Cancelled by user")
        if self._use_qt:
            if message:
                self._dialog.set_message(message)
                self._dialog.log(message)
            self._dialog.set_value(self._step)
            if self._suspend_events:
                self._dialog.repaint_widgets()
            else:
                self.flush_ui()
        else:
            if message:
                print(f"[Progress] {self._step}/{self._total}: {message}")

    def log(self, message: str):
        print(message)
        try:
            hou.ui.setStatusMessage(f"{self._title}: {message[:120]}")
        except Exception:
            pass
        if self._use_qt:
            self._dialog.log(message)
            if self._suspend_events:
                self._dialog.repaint_widgets()
            else:
                self.flush_ui()

    def request_cancel(self):
        self._cancelled = True

    class _SuspendEvents:
        def __init__(self, reporter: "ProgressReporter") -> None:
            self._reporter = reporter
            self._previous = False

        def __enter__(self) -> "ProgressReporter._SuspendEvents":
            self._previous = self._reporter._suspend_events
            self._reporter._suspend_events = True
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            self._reporter._suspend_events = self._previous
            if self._reporter._use_qt and self._reporter._dialog is not None:
                try:
                    self._reporter._dialog.repaint_widgets()
                except Exception:
                    pass
                if not self._reporter._suspend_events:
                    self._reporter.flush_ui()

    def suspend_events(self) -> _SuspendEvents:
        """Disable Qt event pumping while running Houdini ops that crash if UI repaints."""
        return ProgressReporter._SuspendEvents(self)

    def is_cancelled(self) -> bool:
        if self._use_qt and not self._suspend_events:
            # Pump lightly between build steps; never during LOP/VOP cooks.
            try:
                QtWidgets.QApplication.processEvents(
                    QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents, 25
                )
            except Exception:
                pass
            if self._dialog is not None:
                # sync from dialog
                if getattr(self._dialog, 'cancelled', False):
                    self._cancelled = True
        return self._cancelled

    def mark_finished(self, message: str | None = None):
        # Ensure final logs and force the progress bar to 100%
        if message:
            # Log the completion message exactly once
            self.log(message)
        # Force progress bar to 100%
        try:
            if self._use_qt and self._dialog is not None:
                # Set value to total to ensure full bar, regardless of step mismatches
                self._dialog.set_total(self._total)
                self._dialog.set_value(self._total)
        except Exception:
            pass
        if self._use_qt and self._dialog is not None:
            try:
                self._dialog.mark_finished()
            except Exception:
                pass

    def close(self):
        # Keep the dialog open to allow log review; user can close manually.
        if self._use_qt and self._dialog is not None:
            # Do not close here; just enable close if not already
            try:
                self._dialog.mark_finished()
            except Exception:
                pass

    def _register_self(self):
        # Keep a strong reference to this reporter so its dialog does not get GC'd
        try:
            if self not in _LIVE_REPORTERS:
                _LIVE_REPORTERS.append(self)
        except Exception:
            pass

    def _on_dialog_destroyed(self):
        # Qt dialog has been destroyed by the user; cleanup references
        self._cleanup()

    def _cleanup(self):
        try:
            if self in _LIVE_REPORTERS:
                _LIVE_REPORTERS.remove(self)
        except Exception:
            pass
        self._dialog = None
        self._use_qt = False

# Override accept to validate inputs before closing the dialog
def _validate_path_exists(path: str) -> bool:
    return bool(path and os.path.exists(path))


def _is_file(path: str) -> bool:
    return os.path.isfile(path) if path else False


def _is_dir(path: str) -> bool:
    return os.path.isdir(path) if path else False


# Patch the dialog class with an accept override adding validation
orig_accept = AssetMaterialVariantsDialog.accept

def _validated_accept(self: AssetMaterialVariantsDialog):
    data = self.data()
    main_asset = data.get("main_asset_file_path") or ""
    maps_folder = data.get("main_textures") or ""
    # Validate required entries
    if not _is_file(main_asset):
        QtWidgets.QMessageBox.critical(self, "Invalid input", "Main asset file is invalid or not selected.")
        return
    if not _is_dir(maps_folder):
        QtWidgets.QMessageBox.critical(self, "Invalid input", "Main texture folder is invalid or not selected.")
        return
    # If OK
    return orig_accept(self)

# Monkey-patch the method so callers don't need to change usage
AssetMaterialVariantsDialog.accept = _validated_accept
