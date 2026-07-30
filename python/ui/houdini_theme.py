"""
Shared Houdini 22 UI theme for custom tool dialogs.

Uses native Qt palette colors when running inside Houdini, with sensible
fallbacks for standalone hython testing.
"""

from __future__ import annotations

from typing import Optional

import hou
from PySide6 import QtCore, QtGui, QtWidgets


class HoudiniTheme:
    """Centralized theme for custom tool dialogs."""

    FONTS = {
        "default_size": 12,
        "small_size": 10,
        "large_size": 14,
        "header_size": 16,
        "monospace": "'Consolas', 'Monaco', monospace",
    }

    LAYOUT = {
        "border_radius": 4,
        "dialog_min_width": 520,
        "dialog_min_height": 360,
        "list_min_height": 140,
        "progress_height": 18,
        "form_label_min_width": 160,
        "margin": 8,
        "spacing": 8,
    }

    _COLORS: dict[str, str] | None = None

    @classmethod
    def colors(cls) -> dict[str, str]:
        if cls._COLORS is not None:
            return cls._COLORS

        defaults = {
            "background": "#2b2b2b",
            "text": "#e6e6e6",
            "text_secondary": "#c8c8c8",
            "text_muted": "#909090",
            "accent_primary": "#5dade2",
            "accent_secondary": "#85c1e9",
            "accent_dark": "#3498db",
            "border": "#444444",
            "border_focus": "#5dade2",
            "hover": "#3a3a3a",
            "disabled": "#555555",
            "disabled_text": "#888888",
            "success": "#4caf50",
            "error": "#e74c3c",
            "warning": "#f39c12",
        }

        try:
            app = QtWidgets.QApplication.instance()
            if app is not None:
                pal = app.palette()
                defaults["background"] = pal.color(QtGui.QPalette.ColorRole.Window).name()
                defaults["text"] = pal.color(QtGui.QPalette.ColorRole.WindowText).name()
                defaults["text_secondary"] = pal.color(QtGui.QPalette.ColorRole.Text).name()
                defaults["border"] = pal.color(QtGui.QPalette.ColorRole.Mid).name()
                defaults["accent_primary"] = pal.color(QtGui.QPalette.ColorRole.Highlight).name()
        except Exception:
            pass

        cls._COLORS = defaults
        return cls._COLORS

    @classmethod
    def parent_to_houdini(cls, widget: QtWidgets.QWidget) -> None:
        """Parent tool windows to the Houdini main window safely (H22-compatible)."""
        try:
            main = hou.qt.mainWindow()
            if main is not None and widget.parent() is None:
                widget.setParent(main)
            widget.setWindowFlags(
                widget.windowFlags() | QtCore.Qt.WindowStaysOnTopHint
            )
        except Exception:
            pass

    @classmethod
    def setup_dialog(
        cls,
        widget: QtWidgets.QWidget,
        *,
        title: str | None = None,
        min_width: int | None = None,
        min_height: int | None = None,
    ) -> None:
        cls.parent_to_houdini(widget)
        if title:
            widget.setWindowTitle(title)
        widget.setMinimumWidth(min_width or cls.LAYOUT["dialog_min_width"])
        widget.setMinimumHeight(min_height or cls.LAYOUT["dialog_min_height"])
        cls.apply(widget)

    @classmethod
    def apply(cls, widget: QtWidgets.QWidget) -> None:
        c = cls.colors()
        widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: {c["background"]};
                color: {c["text"]};
                font-size: {cls.FONTS["default_size"]}px;
            }}
            QLabel {{
                color: {c["text"]};
            }}
            QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {c["background"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: {cls.LAYOUT["border_radius"]}px;
                padding: 4px 6px;
                min-height: 22px;
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
                border: 1px solid {c["border_focus"]};
            }}
            QListWidget, QTreeWidget, QTableWidget {{
                background-color: {c["background"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: {cls.LAYOUT["border_radius"]}px;
                min-height: {cls.LAYOUT["list_min_height"]}px;
            }}
            QPushButton {{
                background-color: {c["accent_primary"]};
                color: {c["background"]};
                border: 1px solid {c["accent_primary"]};
                border-radius: {cls.LAYOUT["border_radius"]}px;
                padding: 4px 12px;
                min-height: 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c["accent_secondary"]};
            }}
            QPushButton:pressed {{
                background-color: {c["accent_dark"]};
            }}
            QPushButton:disabled {{
                background-color: {c["disabled"]};
                color: {c["disabled_text"]};
                border-color: {c["disabled"]};
            }}
            QCheckBox, QRadioButton {{
                color: {c["text"]};
                spacing: 6px;
            }}
            QGroupBox {{
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: {cls.LAYOUT["border_radius"]}px;
                margin-top: 10px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                color: {c["accent_primary"]};
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
            QProgressBar {{
                background-color: {c["border"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: {cls.LAYOUT["border_radius"]}px;
                text-align: center;
                min-height: {cls.LAYOUT["progress_height"]}px;
            }}
            QProgressBar::chunk {{
                background-color: {c["accent_primary"]};
            }}
            QScrollArea {{
                background-color: {c["background"]};
                border: 1px solid {c["border"]};
            }}
            """
        )

    @classmethod
    def style_message_box(cls, msg_box: QtWidgets.QMessageBox) -> None:
        cls.parent_to_houdini(msg_box)
        cls.apply(msg_box)

    @classmethod
    def themed_message_box(
        cls,
        *,
        title: str,
        text: str,
        icon: QtWidgets.QMessageBox.Icon = QtWidgets.QMessageBox.Information,
        buttons: QtWidgets.QMessageBox.StandardButton = QtWidgets.QMessageBox.Ok,
        informative_text: str = "",
        detailed_text: str = "",
    ) -> int:
        box = QtWidgets.QMessageBox()
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)
        box.setStandardButtons(buttons)
        if informative_text:
            box.setInformativeText(informative_text)
        if detailed_text:
            box.setDetailedText(detailed_text)
        cls.style_message_box(box)
        return box.exec()

    @classmethod
    def apply_form_layout(cls, form: QtWidgets.QFormLayout) -> None:
        form.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        form.setHorizontalSpacing(cls.LAYOUT["spacing"])
        form.setVerticalSpacing(max(4, cls.LAYOUT["spacing"] // 2))
        form.setFieldGrowthPolicy(QtWidgets.QFormLayout.ExpandingFieldsGrow)
        # Keep long label text from stretching the dialog width
        form.setRowWrapPolicy(QtWidgets.QFormLayout.WrapLongRows)
