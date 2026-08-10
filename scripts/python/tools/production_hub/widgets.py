"""Reusable widgets for Production Hub."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class LogTextEdit(QtWidgets.QPlainTextEdit):
    """Append-only log view."""

    def append_line(self, text: str) -> None:
        self.appendPlainText(text)
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class ApiWorker(QtCore.QObject):
    """Run a callable on a background thread (network / non-hou work)."""

    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = self._fn()
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


def run_in_thread(parent: QtWidgets.QWidget, fn, on_ok, on_err) -> QtCore.QThread:
    thread = QtCore.QThread(parent)
    worker = ApiWorker(fn)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_ok)
    worker.failed.connect(on_err)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.start()
    return thread
