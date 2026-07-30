"""
Production Hub — Houdini UI for ftrack tasks, LOPS USD builds, and Iconik linking.

Usage:
    from tools.production_hub import show_ui
    show_ui()
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import hou
from PySide6 import QtCore, QtWidgets
from integrations.ftrack.connect_context import (
    frame_range_from_ftrack,
    list_task_status_names,
    read_connect_env,
    resolve_prefill_task_id,
)
from integrations.ftrack.queries import FtrackQueries, FtrackTaskSummary
from integrations.ftrack.session import create_service
from integrations.iconik.assets import IconikAssets
from integrations.iconik.client import IconikClient
from integrations.settings import load_settings
from integrations.ftrack.publish import ComponentSpec
from integrations.workflows.publish_connect_deliverable import (
    ConnectPublishRequest,
    publish_connect_deliverable,
)
from integrations.workflows.publish_usd_deliverable import PublishRequest, publish_usd_deliverable
from tools.lops_asset_builder_v3 import lops_asset_builder_cli
from tools.production_hub.connect_exports import ConnectAssetKind, ConnectExportOptions, export_connect_asset
from tools.production_hub.ftrack_connect_bridge import (
    apply_timeline_from_env_or_ftrack,
    connect_plugin_root,
    viewport_screenshot,
)
from tools.production_hub.widgets import LogTextEdit, run_in_thread


class ProductionHubDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Production Hub — Iconik · ftrack · Houdini")
        self.setMinimumSize(920, 640)
        self.setStyleSheet(hou.qt.styleSheet())

        self._settings = load_settings()
        self._projects: list[Any] = []
        self._tasks: list[FtrackTaskSummary] = []
        self._selected_task: Optional[FtrackTaskSummary] = None
        self._last_build_result: Optional[Any] = None
        self._active_threads: list[QtCore.QThread] = []

        self._build_ui()
        self._wire_signals()
        self._refresh_connect_banner()
        QtCore.QTimer.singleShot(0, self._maybe_prefill_connect_task)

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        tabs = QtWidgets.QTabWidget()
        root.addWidget(tabs)

        tabs.addTab(self._connection_tab(), "Connection")
        tabs.addTab(self._task_tab(), "Task")
        tabs.addTab(self._build_tab(), "Build")
        tabs.addTab(self._publish_tab(), "Publish")

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        root.addWidget(self.status_label)

    def _connection_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        intro = QtWidgets.QLabel(
            "<h3>Sandbox connections</h3>"
            "<p>Configure <code>$CUSTOM_TOOLS/config/integrations.json</code> "
            "or environment variables (see Production Hub README).</p>"
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.ftrack_summary = QtWidgets.QLabel("")
        self.iconik_summary = QtWidgets.QLabel("")
        layout.addWidget(self.ftrack_summary)
        layout.addWidget(self.iconik_summary)

        btn_row = QtWidgets.QHBoxLayout()
        self.btn_test_ftrack = QtWidgets.QPushButton("Test ftrack")
        self.btn_test_iconik = QtWidgets.QPushButton("Test Iconik")
        btn_row.addWidget(self.btn_test_ftrack)
        btn_row.addWidget(self.btn_test_iconik)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.conn_log = LogTextEdit()
        self.conn_log.setReadOnly(True)
        self.conn_log.setMaximumHeight(180)
        layout.addWidget(self.conn_log)
        layout.addStretch()

        self._refresh_connection_labels()
        return w

    def _task_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        root = connect_plugin_root()
        plug_note = (
            f"<small>ftrack Connect Houdini plugin: <code>{root}</code></small>"
            if root
            else "<small>Install ftrack-connect-houdini under $CUSTOM_TOOLS for Connect launch + legacy publish menus.</small>"
        )
        self.connect_env_label = QtWidgets.QLabel("")
        self.connect_env_label.setWordWrap(True)
        layout.addWidget(self.connect_env_label)
        layout.addWidget(QtWidgets.QLabel(plug_note))

        connect_row = QtWidgets.QHBoxLayout()
        self.btn_use_connect_task = QtWidgets.QPushButton("Use FTRACK_TASKID")
        self.btn_apply_frames = QtWidgets.QPushButton("Apply frame range (FS/FE or ftrack)")
        connect_row.addWidget(self.btn_use_connect_task)
        connect_row.addWidget(self.btn_apply_frames)
        connect_row.addStretch()
        layout.addLayout(connect_row)

        row = QtWidgets.QHBoxLayout()
        self.project_combo = QtWidgets.QComboBox()
        self.project_combo.setMinimumWidth(280)
        self.btn_load_projects = QtWidgets.QPushButton("Load projects")
        self.btn_load_tasks = QtWidgets.QPushButton("Load tasks")
        row.addWidget(QtWidgets.QLabel("Project:"))
        row.addWidget(self.project_combo)
        row.addWidget(self.btn_load_projects)
        row.addWidget(self.btn_load_tasks)
        layout.addLayout(row)

        self.task_list = QtWidgets.QListWidget()
        self.task_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        layout.addWidget(self.task_list)

        self.task_detail = QtWidgets.QLabel("Select a task to bind publish metadata.")
        self.task_detail.setWordWrap(True)
        layout.addWidget(self.task_detail)
        return w

    def _build_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        form = QtWidgets.QFormLayout()
        self.config_path_edit = QtWidgets.QLineEdit()
        browse = QtWidgets.QPushButton("Browse…")
        cfg_row = QtWidgets.QHBoxLayout()
        cfg_row.addWidget(self.config_path_edit)
        cfg_row.addWidget(browse)
        form.addRow("Builder JSON:", cfg_row)
        browse.clicked.connect(self._browse_config)

        self.asset_name_edit = QtWidgets.QLineEdit()
        self.asset_name_edit.setPlaceholderText("Defaults to selected ftrack task name")
        form.addRow("Asset name:", self.asset_name_edit)

        self.usd_out_edit = QtWidgets.QLineEdit()
        self.usd_out_edit.setPlaceholderText("Optional USD path for publish (after build)")
        usd_row = QtWidgets.QHBoxLayout()
        usd_row.addWidget(self.usd_out_edit)
        usd_browse = QtWidgets.QPushButton("Browse…")
        usd_browse.clicked.connect(self._browse_usd)
        usd_row.addWidget(usd_browse)
        form.addRow("USD output:", usd_row)

        layout.addLayout(form)

        self.btn_build = QtWidgets.QPushButton("Run LOPS Asset Builder (CLI)")
        layout.addWidget(self.btn_build)

        self.build_log = LogTextEdit()
        self.build_log.setReadOnly(True)
        layout.addWidget(self.build_log)
        return w

    def _publish_tab(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)

        self.publish_info = QtWidgets.QLabel(
            "Publish registers the USD on the selected ftrack task and links metadata in Iconik."
        )
        self.publish_info.setWordWrap(True)
        layout.addWidget(self.publish_info)

        pub_form = QtWidgets.QFormLayout()
        self.comment_edit = QtWidgets.QLineEdit()
        self.comment_edit.setPlaceholderText("Publish comment (Connect-style)")
        pub_form.addRow("Comment:", self.comment_edit)

        thumb_row = QtWidgets.QHBoxLayout()
        self.thumbnail_edit = QtWidgets.QLineEdit()
        thumb_browse = QtWidgets.QPushButton("Browse…")
        thumb_browse.clicked.connect(self._browse_thumbnail)
        self.btn_viewport_thumb = QtWidgets.QPushButton("Viewport JPG")
        self.btn_viewport_thumb.clicked.connect(self._on_viewport_thumbnail)
        thumb_row.addWidget(self.thumbnail_edit)
        thumb_row.addWidget(thumb_browse)
        thumb_row.addWidget(self.btn_viewport_thumb)
        pub_form.addRow("Thumbnail:", thumb_row)

        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.setEditable(False)
        self.status_combo.addItem("(no status change)", "")
        pub_form.addRow("Task status:", self.status_combo)
        self.btn_load_statuses = QtWidgets.QPushButton("Load statuses from ftrack")
        pub_form.addRow("", self.btn_load_statuses)

        layout.addLayout(pub_form)

        connect_box = QtWidgets.QGroupBox("Connect-style export (geo / scene / cam)")
        connect_layout = QtWidgets.QFormLayout(connect_box)

        self.connect_kind_combo = QtWidgets.QComboBox()
        self.connect_kind_combo.addItem("Geometry (geo)", "geo")
        self.connect_kind_combo.addItem("Scene (scene)", "scene")
        self.connect_kind_combo.addItem("Camera (cam)", "cam")
        connect_layout.addRow("Asset type:", self.connect_kind_combo)

        self.chk_houdini_nodes = QtWidgets.QCheckBox("Houdini nodes (.hip subnet)")
        self.chk_houdini_nodes.setChecked(True)
        self.chk_alembic = QtWidgets.QCheckBox("Alembic (.abc)")
        self.chk_alembic.setChecked(True)
        self.chk_attach_scene = QtWidgets.QCheckBox("Attach full scene (.hip)")
        self.chk_sel_nodes = QtWidgets.QCheckBox("Selection only (nodes)")
        self.chk_sel_nodes.setChecked(True)
        self.chk_sel_abc = QtWidgets.QCheckBox("Selection only (Alembic)")
        self.chk_sel_abc.setChecked(True)
        self.chk_abc_anim = QtWidgets.QCheckBox("Alembic animation")

        connect_layout.addRow("", self.chk_houdini_nodes)
        connect_layout.addRow("", self.chk_alembic)
        connect_layout.addRow("", self.chk_attach_scene)
        connect_layout.addRow("", self.chk_sel_nodes)
        connect_layout.addRow("", self.chk_sel_abc)
        connect_layout.addRow("", self.chk_abc_anim)

        frame_row = QtWidgets.QHBoxLayout()
        self.frame_start_spin = QtWidgets.QDoubleSpinBox()
        self.frame_end_spin = QtWidgets.QDoubleSpinBox()
        for sp in (self.frame_start_spin, self.frame_end_spin):
            sp.setRange(-100000, 1000000)
            sp.setDecimals(1)
        self.frame_start_spin.setValue(hou.playbar.playbackRange()[0])
        self.frame_end_spin.setValue(hou.playbar.playbackRange()[1])
        frame_row.addWidget(self.frame_start_spin)
        frame_row.addWidget(QtWidgets.QLabel("–"))
        frame_row.addWidget(self.frame_end_spin)
        connect_layout.addRow("Frame range:", frame_row)

        self.btn_publish_connect = QtWidgets.QPushButton("Export & publish Connect components")
        connect_layout.addRow("", self.btn_publish_connect)

        self.connect_kind_combo.currentIndexChanged.connect(self._on_connect_kind_changed)
        layout.addWidget(connect_box)
        self._on_connect_kind_changed()

        self.btn_publish = QtWidgets.QPushButton("Publish USD deliverable")
        layout.addWidget(self.btn_publish)

        pub_btn_row = QtWidgets.QHBoxLayout()
        self.btn_verify_iconik = QtWidgets.QPushButton("Search Iconik for task")
        self.btn_copy_ids = QtWidgets.QPushButton("Copy last IDs to clipboard")
        pub_btn_row.addWidget(self.btn_verify_iconik)
        pub_btn_row.addWidget(self.btn_copy_ids)
        pub_btn_row.addStretch()
        layout.addLayout(pub_btn_row)

        self.publish_log = LogTextEdit()
        self.publish_log.setReadOnly(True)
        layout.addWidget(self.publish_log)

        self._last_publish_ids: dict[str, str] = {}
        return w

    def _wire_signals(self) -> None:
        self.btn_test_ftrack.clicked.connect(self._on_test_ftrack)
        self.btn_test_iconik.clicked.connect(self._on_test_iconik)
        self.btn_load_projects.clicked.connect(self._on_load_projects)
        self.btn_load_tasks.clicked.connect(self._on_load_tasks)
        self.task_list.itemSelectionChanged.connect(self._on_task_selected)
        self.btn_build.clicked.connect(self._on_build)
        self.btn_publish.clicked.connect(self._on_publish)
        self.btn_publish_connect.clicked.connect(self._on_publish_connect)
        self.btn_verify_iconik.clicked.connect(self._on_verify_iconik)
        self.btn_copy_ids.clicked.connect(self._on_copy_ids)
        self.btn_use_connect_task.clicked.connect(self._on_use_connect_task)
        self.btn_apply_frames.clicked.connect(self._on_apply_frame_range)
        self.btn_load_statuses.clicked.connect(self._on_load_statuses)

    def _refresh_connection_labels(self) -> None:
        self._settings = load_settings()
        ft = self._settings.ftrack
        ik = self._settings.iconik
        self.ftrack_summary.setText(f"<b>ftrack:</b> {ft.masked_summary() if ft.server_url else 'not configured'}")
        self.iconik_summary.setText(f"<b>Iconik:</b> {ik.masked_summary() if ik.app_id else 'not configured'}")

    def _log_conn(self, msg: str) -> None:
        self.conn_log.append_line(msg)

    def _set_busy(self, busy: bool) -> None:
        self.setEnabled(not busy)
        if busy:
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        else:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _on_test_ftrack(self) -> None:
        def work():
            svc = create_service(self._settings)
            return svc.ping()

        def ok(data):
            self._set_busy(False)
            self._log_conn(f"ftrack OK — user {data.get('username')} ({data.get('id')})")
            self.status_label.setText("ftrack connection OK")

        def err(msg):
            self._set_busy(False)
            self._log_conn(f"ftrack FAILED — {msg}")
            self.status_label.setText("ftrack connection failed")

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_test_iconik(self) -> None:
        def work():
            return IconikClient(self._settings).ping()

        def ok(data):
            self._set_busy(False)
            self._log_conn(f"Iconik OK — {data.get('email') or data.get('id')}")
            self.status_label.setText("Iconik connection OK")

        def err(msg):
            self._set_busy(False)
            self._log_conn(f"Iconik FAILED — {msg}")
            self.status_label.setText("Iconik connection failed")

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_load_projects(self) -> None:
        def work():
            return FtrackQueries().list_projects()

        def ok(projects):
            self._set_busy(False)
            self._projects = projects
            self.project_combo.clear()
            for p in projects:
                self.project_combo.addItem(p.name, p.id)
            self.status_label.setText(f"Loaded {len(projects)} project(s)")

        def err(msg):
            self._set_busy(False)
            QtWidgets.QMessageBox.warning(self, "ftrack", msg)

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_load_tasks(self) -> None:
        project_id = self.project_combo.currentData()
        if not project_id:
            QtWidgets.QMessageBox.information(self, "Task", "Load projects and select one first.")
            return

        def work():
            return FtrackQueries().list_tasks_for_project(str(project_id))

        def ok(tasks):
            self._set_busy(False)
            self._tasks = tasks
            self.task_list.clear()
            for t in tasks:
                item = QtWidgets.QListWidgetItem(f"{t.name}  [{t.status}]  — {t.parent_name}")
                item.setData(QtCore.Qt.UserRole, t.id)
                self.task_list.addItem(item)
            self.status_label.setText(f"Loaded {len(tasks)} task(s)")

        def err(msg):
            self._set_busy(False)
            QtWidgets.QMessageBox.warning(self, "ftrack", msg)

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_task_selected(self) -> None:
        items = self.task_list.selectedItems()
        if not items:
            self._selected_task = None
            return
        task_id = items[0].data(QtCore.Qt.UserRole)
        for t in self._tasks:
            if t.id == task_id:
                self._selected_task = t
                break
        if self._selected_task:
            t = self._selected_task
            self.task_detail.setText(
                f"<b>{t.name}</b><br>Project: {t.project_name}<br>Parent: {t.parent_name}<br>ID: {t.id}"
            )
            if not self.asset_name_edit.text().strip():
                self.asset_name_edit.setText(t.name)
            self._save_task_sidecar(t.id)

    def _save_task_sidecar(self, task_id: str) -> None:
        job = hou.expandString("$JOB")
        if not job or job == "$JOB":
            return
        path = os.path.join(job, "ftrack_task_id.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"ftrack_task_id": task_id}, fh, indent=2)
        except OSError:
            pass

    def _browse_config(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Asset builder JSON", hou.expandString("$HIP"), "JSON (*.json)"
        )
        if path:
            self.config_path_edit.setText(path)

    def _browse_usd(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "USD file", hou.expandString("$HIP"), "USD (*.usd *.usda *.usdc)"
        )
        if path:
            self.usd_out_edit.setText(path)

    def _on_build(self) -> None:
        config_path = self.config_path_edit.text().strip()
        if not config_path:
            QtWidgets.QMessageBox.warning(self, "Build", "Select a LOPS asset builder JSON config.")
            return
        config_path = hou.expandString(config_path)

        self.build_log.append_line(f"Building from {config_path} …")
        self._set_busy(True)
        try:
            result = lops_asset_builder_cli.build_asset_from_file(config_path, verbose=True)
            self._last_build_result = result
            if result.success:
                self.build_log.append_line(f"OK — {result.message}")
                if result.output_node:
                    self.build_log.append_line(f"Output node: {result.output_node.path()}")
                self.status_label.setText("Build succeeded")
            else:
                self.build_log.append_line(f"FAILED — {result.message}")
                self.status_label.setText("Build failed")
        except Exception as exc:
            self.build_log.append_line(f"ERROR — {exc}")
            self.status_label.setText("Build error")
        finally:
            self._set_busy(False)

    def _on_publish(self) -> None:
        if not self._selected_task:
            QtWidgets.QMessageBox.warning(self, "Publish", "Select an ftrack task first.")
            return
        usd_path = self.usd_out_edit.text().strip()
        if not usd_path:
            QtWidgets.QMessageBox.warning(self, "Publish", "Set the USD output path to publish.")
            return
        usd_path = hou.expandString(usd_path)
        asset_name = self.asset_name_edit.text().strip() or self._selected_task.name

        builder_dict = None
        if self._last_build_result is not None:
            builder_dict = {
                "success": getattr(self._last_build_result, "success", None),
                "message": getattr(self._last_build_result, "message", ""),
            }

        request = PublishRequest(
            ftrack_task_id=self._selected_task.id,
            asset_name=asset_name,
            usd_path=usd_path,
            hip_path=hou.hipFile.path(),
            builder_result=builder_dict,
            ftrack_task_name=self._selected_task.name,
            ftrack_parent_name=self._selected_task.parent_name,
            comment=self.comment_edit.text().strip() or "Published from Production Hub",
            thumbnail_path=self.thumbnail_edit.text().strip() or None,
            task_status_name=self.status_combo.currentData() or None,
        )

        def work():
            return publish_usd_deliverable(request, self._settings)

        def ok(result):
            self._set_busy(False)
            self.publish_log.append_line(result.message)
            if result.errors:
                for e in result.errors:
                    self.publish_log.append_line(f"  warning: {e}")
            self._last_publish_ids = {
                "ftrack_asset_version_id": result.ftrack_asset_version_id or "",
                "ftrack_asset_id": result.ftrack_asset_id or "",
                "iconik_asset_id": result.iconik_asset_id or "",
            }
            self.status_label.setText("Publish OK" if result.success else "Publish completed with warnings")

        def err(msg):
            self._set_busy(False)
            self.publish_log.append_line(f"FAILED — {msg}")
            self.status_label.setText("Publish failed")

        self.publish_log.append_line(f"Publishing {asset_name} → {usd_path}")
        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_connect_kind_changed(self) -> None:
        kind = self.connect_kind_combo.currentData()
        is_scene = kind == "scene"
        is_cam = kind == "cam"
        self.chk_houdini_nodes.setEnabled(not is_scene)
        self.chk_alembic.setEnabled(not is_scene)
        self.chk_attach_scene.setEnabled(not is_scene)
        self.chk_sel_abc.setEnabled(not is_scene and self.chk_alembic.isChecked())
        if is_scene:
            self.chk_houdini_nodes.setChecked(False)
            self.chk_alembic.setChecked(False)
            self.chk_attach_scene.setChecked(False)
        elif is_cam:
            self.chk_houdini_nodes.setChecked(False)
            self.chk_alembic.setChecked(True)

    def _connect_export_options(self) -> ConnectExportOptions:
        return ConnectExportOptions(
            export_mode_selection=self.chk_sel_nodes.isChecked(),
            alembic=self.chk_alembic.isChecked(),
            alembic_animation=self.chk_abc_anim.isChecked(),
            alembic_export_mode_selection=self.chk_sel_abc.isChecked(),
            houdini_nodes=self.chk_houdini_nodes.isChecked(),
            houdini_publish_scene=self.chk_attach_scene.isChecked(),
            frame_start=self.frame_start_spin.value(),
            frame_end=self.frame_end_spin.value(),
        )

    def _on_publish_connect(self) -> None:
        if not self._selected_task:
            QtWidgets.QMessageBox.warning(self, "Publish", "Select an ftrack task first.")
            return
        kind_str = self.connect_kind_combo.currentData()
        kind = ConnectAssetKind(kind_str)
        options = self._connect_export_options()
        asset_name = self.asset_name_edit.text().strip() or self._selected_task.name

        self.publish_log.append_line(f"Exporting Connect {kind.value} …")
        self._set_busy(True)
        try:
            exported = export_connect_asset(kind, options)
            for comp in exported:
                self.publish_log.append_line(f"  exported {comp.name}: {comp.path}")
        except Exception as exc:
            self._set_busy(False)
            self.publish_log.append_line(f"Export FAILED — {exc}")
            QtWidgets.QMessageBox.warning(self, "Export", str(exc))
            return

        specs = [
            ComponentSpec(name=c.name, path=c.path, file_type=c.file_type) for c in exported
        ]
        request = ConnectPublishRequest(
            ftrack_task_id=self._selected_task.id,
            asset_name=asset_name,
            asset_kind=kind.value,
            components=specs,
            hip_path=hou.hipFile.path(),
            thumbnail_path=self.thumbnail_edit.text().strip() or None,
            comment=self.comment_edit.text().strip()
            or "Published from Production Hub (Connect export)",
            task_status_name=self.status_combo.currentData() or None,
            ftrack_task_name=self._selected_task.name,
            ftrack_parent_name=self._selected_task.parent_name,
        )

        def work():
            return publish_connect_deliverable(request, self._settings)

        def ok(result):
            self._set_busy(False)
            self.publish_log.append_line(result.message)
            for e in result.errors:
                self.publish_log.append_line(f"  warning: {e}")
            self._last_publish_ids = {
                "ftrack_asset_version_id": result.ftrack_asset_version_id or "",
                "ftrack_asset_id": result.ftrack_asset_id or "",
                "iconik_asset_id": result.iconik_asset_id or "",
            }
            self.status_label.setText("Connect publish OK" if result.success else "Connect publish with warnings")

        def err(msg):
            self._set_busy(False)
            self.publish_log.append_line(f"Publish FAILED — {msg}")

        run_in_thread(self, work, ok, err)

    def _refresh_connect_banner(self) -> None:
        ctx = read_connect_env()
        parts = [
            f"<b>Connect env:</b> task={ctx.task_id or '—'}",
            f"shot={ctx.shot_id or '—'}",
            f"FS={ctx.frame_start if ctx.frame_start is not None else '—'}",
            f"FE={ctx.frame_end if ctx.frame_end is not None else '—'}",
        ]
        self.connect_env_label.setText(" · ".join(parts))

    def _maybe_prefill_connect_task(self) -> None:
        job = hou.expandString("$JOB")
        if job == "$JOB":
            job = ""
        task_id, source = resolve_prefill_task_id(job or None)
        if not task_id:
            return
        self._bind_task_by_id(task_id, source_label=source, apply_connect_frames=source == "FTRACK_TASKID")

    def _select_task_in_list(self, task_id: str) -> None:
        for index in range(self.task_list.count()):
            item = self.task_list.item(index)
            if item and item.data(QtCore.Qt.UserRole) == task_id:
                self.task_list.setCurrentItem(item)
                return

    def _bind_task_by_id(
        self,
        task_id: str,
        *,
        source_label: str = "Connect",
        apply_connect_frames: bool = False,
    ) -> None:
        def work():
            q = FtrackQueries()
            return q.get_task_context(task_id)

        def ok(data):
            self._set_busy(False)
            self._selected_task = FtrackTaskSummary(
                id=data["id"],
                name=data["name"],
                link=data.get("link", ""),
                project_id=data["project_id"],
                project_name=data["project_name"],
                parent_name=data.get("parent_name", ""),
                status=data.get("status", ""),
            )
            self.task_detail.setText(
                f"<b>{self._selected_task.name}</b> ({source_label})<br>"
                f"Project: {self._selected_task.project_name}<br>"
                f"Parent: {self._selected_task.parent_name}<br>"
                f"ID: {self._selected_task.id}"
            )
            self._select_task_in_list(task_id)
            if not self.asset_name_edit.text().strip():
                self.asset_name_edit.setText(self._selected_task.name)
            idx = self.project_combo.findData(self._selected_task.project_id)
            if idx >= 0:
                self.project_combo.setCurrentIndex(idx)
            self._save_task_sidecar(task_id)
            self.status_label.setText(f"Bound ftrack task from {source_label}")
            if apply_connect_frames:
                self._apply_connect_frame_range_silent()

        def err(msg):
            self._set_busy(False)
            QtWidgets.QMessageBox.warning(self, "ftrack", msg)

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_use_connect_task(self) -> None:
        ctx = read_connect_env()
        if not ctx.task_id:
            QtWidgets.QMessageBox.information(
                self,
                "Connect",
                "FTRACK_TASKID is not set. Launch Houdini from ftrack Connect or export the variable.",
            )
            return
        self._bind_task_by_id(ctx.task_id, source_label="FTRACK_TASKID", apply_connect_frames=True)

    def _apply_connect_frame_range_silent(self) -> None:
        ctx = read_connect_env()
        if ctx.frame_start is None and ctx.frame_end is None:
            return
        try:
            fs, fe = ctx.frame_start, ctx.frame_end
            fps = 24.0
            handles = 0.0
            if self._selected_task:
                data = frame_range_from_ftrack(self._selected_task.id)
                if fs is None and data.get("frame_start") is not None:
                    fs = data["frame_start"]
                if fe is None and data.get("frame_end") is not None:
                    fe = data["frame_end"]
                if data.get("fps") is not None:
                    fps = float(data["fps"])
                if data.get("handles") is not None:
                    handles = float(data["handles"])
            out = apply_timeline_from_env_or_ftrack(fs, fe, fps=fps, handles=handles)
            self.build_log.append_line(f"Timeline (Connect) {out[0]}–{out[1]} @ {fps} fps")
        except Exception as exc:
            self.build_log.append_line(f"Connect frame range skipped: {exc}")

    def _on_apply_frame_range(self) -> None:
        ctx = read_connect_env()
        fps = 24.0
        handles = 0.0
        fs, fe = ctx.frame_start, ctx.frame_end
        if self._selected_task:
            try:
                data = frame_range_from_ftrack(self._selected_task.id)
                if data.get("frame_start") is not None:
                    fs = data["frame_start"]
                if data.get("frame_end") is not None:
                    fe = data["frame_end"]
                if data.get("fps") is not None:
                    fps = float(data["fps"])
                if data.get("handles") is not None:
                    handles = float(data["handles"])
            except Exception as exc:
                self.build_log.append_line(f"Frame range from ftrack: {exc}")
        try:
            out = apply_timeline_from_env_or_ftrack(fs, fe, fps=fps, handles=handles)
            self.build_log.append_line(f"Timeline {out[0]}–{out[1]} @ {fps} fps")
            self.status_label.setText("Frame range applied")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Timeline", str(exc))

    def _browse_thumbnail(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Thumbnail", hou.expandString("$HIP"), "Images (*.jpg *.jpeg *.png)"
        )
        if path:
            self.thumbnail_edit.setText(path)

    def _on_viewport_thumbnail(self) -> None:
        try:
            path = viewport_screenshot()
            self.thumbnail_edit.setText(path)
            self.status_label.setText("Viewport thumbnail captured")
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self, "Screenshot", str(exc))

    def _on_load_statuses(self) -> None:
        def work():
            return list_task_status_names()

        def ok(names):
            self._set_busy(False)
            self.status_combo.clear()
            self.status_combo.addItem("(no status change)", "")
            for name in names:
                self.status_combo.addItem(name, name)
            self.status_label.setText(f"Loaded {len(names)} statuses")

        def err(msg):
            self._set_busy(False)
            QtWidgets.QMessageBox.warning(self, "ftrack", msg)

        self._set_busy(True)
        run_in_thread(self, work, ok, err)

    def _on_copy_ids(self) -> None:
        if not self._last_publish_ids:
            return
        text = json.dumps(self._last_publish_ids, indent=2)
        QtWidgets.QApplication.clipboard().setText(text)
        self.status_label.setText("IDs copied to clipboard")

    def _on_verify_iconik(self) -> None:
        if not self._selected_task:
            QtWidgets.QMessageBox.information(self, "Iconik", "Select an ftrack task first.")
            return
        query = f"ftrack_task_id:{self._selected_task.id}"

        def work():
            return IconikAssets().search(query, page_size=10)

        def ok(hits):
            self._set_busy(False)
            if not hits:
                self.publish_log.append_line(f"Iconik: no hits for {query}")
            else:
                self.publish_log.append_line(f"Iconik: {len(hits)} hit(s) for {query}")
                for hit in hits:
                    self.publish_log.append_line(f"  — {hit.title} ({hit.id})")
            self.status_label.setText("Iconik search done")

        def err(msg):
            self._set_busy(False)
            self.publish_log.append_line(f"Iconik search FAILED — {msg}")

        self._set_busy(True)
        run_in_thread(self, work, ok, err)


def show_ui():
    parent = hou.qt.mainWindow()
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(widget, ProductionHubDialog):
            widget.close()
    dialog = ProductionHubDialog(parent)
    dialog.show()
    return dialog


if __name__ == "__main__":
    show_ui()
