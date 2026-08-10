"""Progress reporting protocol and shared helpers for all builder entry points."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from tools.lops_asset_builder_v3.material_validator import ValidationResult


@runtime_checkable
class ProgressLike(Protocol):
    def step(self, message: str = None) -> None: ...
    def log(self, message: str) -> None: ...
    def is_cancelled(self) -> bool: ...
    def set_total(self, total: int) -> None: ...
    def ensure_total(self, minimum: int) -> None: ...
    def mark_finished(self, message: str | None = None) -> None: ...


def log_validation_result(progress: ProgressLike | None, validation_result: "ValidationResult") -> None:
    """Log material validation outcome once (shared by GUI engine path and CLI)."""
    if progress is None:
        return
    if validation_result.materials_missing:
        progress.log(
            f"Warning: {len(validation_result.materials_missing)} material(s) have no matching textures"
        )
        for mat in sorted(validation_result.materials_missing):
            progress.log(f"  Missing: {mat}")
        progress.log("Missing materials will use fallback template shaders")
    elif validation_result.materials_expected:
        progress.log(
            f"All {len(validation_result.materials_expected)} material(s) validated successfully"
        )
    else:
        progress.log("No material assignments in geometry; template materials will be used.")


class ConsoleProgressReporter:
    """Console / pipeline progress reporter (no Qt)."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._cancelled = False
        self._step = 0
        self._total = 100
        self._start_time = time.time()

    def set_total(self, total: int) -> None:
        self._total = max(1, int(total))

    def ensure_total(self, minimum: int) -> None:
        minimum = max(1, int(minimum))
        if self._total < minimum:
            self.set_total(minimum)

    def step(self, message: str = None) -> None:
        self._step += 1
        if self._cancelled:
            raise KeyboardInterrupt("Cancelled by user")
        if message and self.verbose:
            elapsed = time.time() - self._start_time
            print(f"[{self._step}/{self._total}] ({elapsed:.1f}s) {message}")

    def log(self, message: str) -> None:
        if self.verbose:
            print(f"  → {message}")

    def is_cancelled(self) -> bool:
        return self._cancelled

    def request_cancel(self) -> None:
        self._cancelled = True

    def mark_finished(self, message: str = None) -> None:
        elapsed = time.time() - self._start_time
        if message and self.verbose:
            print(f"[FINISHED] ({elapsed:.1f}s) {message}")

    class _SuspendEvents:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

    def suspend_events(self) -> _SuspendEvents:
        return ConsoleProgressReporter._SuspendEvents()
