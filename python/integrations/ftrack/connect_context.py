"""
ftrack Connect launch context (FTRACK_TASKID, FS, FE, …).

Compatible with variables set by ftrack-connect-houdini when launched from
ftrack Connect. See projects/production_hub/FTRACK_CONNECT.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from integrations.ftrack.queries import FtrackQueries


@dataclass(frozen=True)
class ConnectLaunchContext:
    task_id: Optional[str]
    shot_id: Optional[str]
    frame_start: Optional[int]
    frame_end: Optional[int]
    source: str

    @property
    def has_task(self) -> bool:
        return bool(self.task_id)


def read_task_id_sidecar(job_dir: str) -> Optional[str]:
    """Read ftrack task id written by Production Hub ($JOB/ftrack_task_id.json)."""
    if not job_dir or job_dir.startswith("$"):
        return None
    path = Path(job_dir) / "ftrack_task_id.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    task_id = data.get("ftrack_task_id") if isinstance(data, dict) else None
    if task_id is None:
        return None
    text = str(task_id).strip()
    return text or None


def resolve_prefill_task_id(job_dir: Optional[str] = None) -> tuple[Optional[str], str]:
    """
    Task id to bind when opening Production Hub.

    Priority: FTRACK_TASKID (Connect launch) → $JOB/ftrack_task_id.json sidecar.
    """
    ctx = read_connect_env()
    if ctx.task_id:
        return ctx.task_id, "FTRACK_TASKID"
    if job_dir:
        sidecar = read_task_id_sidecar(job_dir)
        if sidecar:
            return sidecar, "ftrack_task_id.json"
    return None, "manual"


def read_connect_env() -> ConnectLaunchContext:
    task_id = os.environ.get("FTRACK_TASKID", "").strip() or None
    shot_id = os.environ.get("FTRACK_SHOTID", "").strip() or None
    fs = _parse_int(os.environ.get("FS"))
    fe = _parse_int(os.environ.get("FE"))
    source = "ftrack_connect" if task_id or shot_id else "manual"
    return ConnectLaunchContext(
        task_id=task_id,
        shot_id=shot_id,
        frame_start=fs,
        frame_end=fe,
        source=source,
    )


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def frame_range_from_ftrack(task_id: str) -> dict[str, Any]:
    """Resolve frame range and fps from task parent (shot/sequence) via ftrack_api."""
    ctx = FtrackQueries().get_task_context(task_id)
    session = FtrackQueries().session
    parent_id = ctx.get("parent_id")
    frame_start = None
    frame_end = None
    fps = None
    handles = None

    if parent_id:
        parent = session.get(ctx.get("parent_type") or "TypedContext", parent_id)
        if parent is None:
            parent = session.get("Folder", parent_id)
        if parent is not None:
            for key in ("frame_start", "frameStart", "fstart"):
                if parent.get(key) is not None:
                    frame_start = int(parent[key])
                    break
            for key in ("frame_end", "frameEnd", "fend"):
                if parent.get(key) is not None:
                    frame_end = int(parent[key])
                    break
            if parent.get("fps") is not None:
                fps = float(parent["fps"])
            if parent.get("custom_attributes") and isinstance(parent["custom_attributes"], dict):
                ca = parent["custom_attributes"]
                if ca.get("handles") is not None:
                    try:
                        handles = float(ca["handles"])
                    except (TypeError, ValueError):
                        pass

    return {
        "task": ctx,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "fps": fps,
        "handles": handles,
    }


def list_task_status_names(limit: int = 50) -> list[str]:
    session = FtrackQueries().session
    statuses = session.query(f"Status order by name asc limit {int(limit)}")
    return [s["name"] for s in statuses]
