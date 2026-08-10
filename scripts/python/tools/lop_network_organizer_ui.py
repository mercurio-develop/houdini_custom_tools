"""
LOP Network Organizer - UI Dialog

Provides a simple UI for organizing LOP networks.
"""

import hou
from PySide6 import QtWidgets, QtCore

from tools.lop_network_organizer import LOPNetworkOrganizer
from ui.houdini_theme import HoudiniTheme


class LOPOrganizerDialog(QtWidgets.QDialog):
    """Simple dialog for LOP network organization"""

    def __init__(self, parent=None):
        super().__init__(parent)
        HoudiniTheme.setup_dialog(self, title="LOP Network Organizer", min_width=400, min_height=300)
        self.resize(400, 300)

        self.organizer = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Header
        header = QtWidgets.QLabel("Organize and merge LOP network nodes")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        layout.addSpacing(10)

        # Stage selection
        stage_group = QtWidgets.QGroupBox("Stage Network")
        stage_layout = QtWidgets.QHBoxLayout(stage_group)

        self.stage_path_edit = QtWidgets.QLineEdit("/stage")
        stage_layout.addWidget(QtWidgets.QLabel("Path:"))
        stage_layout.addWidget(self.stage_path_edit)

        self.btn_detect = QtWidgets.QPushButton("Auto-Detect")
        self.btn_detect.clicked.connect(self._auto_detect_stage)
        stage_layout.addWidget(self.btn_detect)

        layout.addWidget(stage_group)

        # Options
        options_group = QtWidgets.QGroupBox("Organization Options")
        options_layout = QtWidgets.QVBoxLayout(options_group)

        self.cb_merge = QtWidgets.QCheckBox("Merge all component outputs")
        self.cb_merge.setChecked(True)
        options_layout.addWidget(self.cb_merge)

        self.cb_layout = QtWidgets.QCheckBox("Organize in grid layout")
        self.cb_layout.setChecked(True)
        options_layout.addWidget(self.cb_layout)

        self.cb_boxes = QtWidgets.QCheckBox("Create network boxes (groups)")
        self.cb_boxes.setChecked(False)
        options_layout.addWidget(self.cb_boxes)

        # Grid settings
        grid_layout = QtWidgets.QHBoxLayout()
        grid_layout.addWidget(QtWidgets.QLabel("Grid columns:"))
        self.spin_columns = QtWidgets.QSpinBox()
        self.spin_columns.setRange(2, 10)
        self.spin_columns.setValue(4)
        grid_layout.addWidget(self.spin_columns)
        grid_layout.addStretch()
        options_layout.addLayout(grid_layout)

        layout.addWidget(options_group)

        # Info display
        self.info_text = QtWidgets.QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        layout.addWidget(self.info_text)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.btn_analyze = QtWidgets.QPushButton("Analyze")
        self.btn_analyze.clicked.connect(self._analyze)
        button_layout.addWidget(self.btn_analyze)

        self.btn_organize = QtWidgets.QPushButton("Organize!")
        self.btn_organize.setStyleSheet("background-color: #4a7c59; font-weight: bold;")
        self.btn_organize.clicked.connect(self._organize)
        button_layout.addWidget(self.btn_organize)

        self.btn_close = QtWidgets.QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)

    def _auto_detect_stage(self):
        """Auto-detect stage network"""
        stage = hou.node("/stage")
        if not stage:
            # Look for any lopnet
            for node in hou.node("/obj").children():
                if node.type().name() == "lopnet":
                    stage = node
                    break

        if stage:
            self.stage_path_edit.setText(stage.path())
            self.info_text.append(f"Found stage: {stage.path()}")
        else:
            self.info_text.append("ERROR: No LOP network found!")

    def _analyze(self):
        """Analyze the network"""
        stage_path = self.stage_path_edit.text().strip()

        try:
            self.organizer = LOPNetworkOrganizer(stage_path)
            self.info_text.clear()
            self.info_text.append(f"Stage: {stage_path}")
            self.info_text.append(f"Total nodes: {len(self.organizer.stage_context.children())}")

            component_outputs = self.organizer.find_component_outputs()
            subnets = self.organizer.find_subnet_outputs()

            self.info_text.append(f"Component outputs: {len(component_outputs)}")
            self.info_text.append(f"Subnets: {len(subnets)}")
            self.info_text.append(f"\nReady to organize {len(component_outputs) + len(subnets)} nodes!")

        except Exception as e:
            self.info_text.append(f"\nERROR: {str(e)}")

    def _organize(self):
        """Organize the network"""
        stage_path = self.stage_path_edit.text().strip()

        try:
            if not self.organizer:
                self.organizer = LOPNetworkOrganizer(stage_path)

            self.info_text.clear()
            self.info_text.append("Organizing network...\n")

            # Capture print output
            import sys
            from io import StringIO

            old_stdout = sys.stdout
            sys.stdout = captured = StringIO()

            self.organizer.organize_network(
                merge_outputs=self.cb_merge.isChecked(),
                layout_grid=self.cb_layout.isChecked(),
                create_boxes=self.cb_boxes.isChecked()
            )

            sys.stdout = old_stdout
            output = captured.getvalue()

            self.info_text.append(output)
            self.info_text.append("\nOrganization complete!")

            # Frame network
            self.organizer.stage_context.layoutChildren()

        except Exception as e:
            self.info_text.append(f"\nERROR: {str(e)}")
            import traceback
            self.info_text.append(traceback.format_exc())


def show_organizer_dialog():
    """Show the LOP organizer dialog"""
    dialog = LOPOrganizerDialog(hou.qt.mainWindow())
    dialog.show()
    return dialog


if __name__ == "__main__":
    show_organizer_dialog()
