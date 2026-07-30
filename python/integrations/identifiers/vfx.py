"""VFX asset identity helpers for ftrack + Iconik metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

KB3D_CODE_RE = re.compile(r"(KB3D_[A-Za-z0-9_]+)", re.IGNORECASE)


@dataclass(frozen=True)
class VfxAssetRef:
    ftrack_task_id: str
    asset_name: str
    usd_path: str
    ftrack_task_name: Optional[str] = None
    parent_name: Optional[str] = None
    kb3d_asset_code: Optional[str] = None
    vfx_shot_code: Optional[str] = None


def infer_kb3d_asset_code(asset_name: str, usd_path: str = "") -> Optional[str]:
    for source in (asset_name, Path(usd_path).stem if usd_path else "", usd_path):
        if not source:
            continue
        match = KB3D_CODE_RE.search(source)
        if match:
            return match.group(1)
    return None


def infer_vfx_shot_code(parent_name: Optional[str]) -> Optional[str]:
    if parent_name and parent_name.strip():
        return parent_name.strip()
    return None


def build_vfx_asset_ref(
    *,
    ftrack_task_id: str,
    asset_name: str,
    usd_path: str,
    ftrack_task_name: Optional[str] = None,
    parent_name: Optional[str] = None,
) -> VfxAssetRef:
    kb3d = infer_kb3d_asset_code(asset_name, usd_path)
    shot = infer_vfx_shot_code(parent_name)
    return VfxAssetRef(
        ftrack_task_id=ftrack_task_id,
        asset_name=asset_name,
        usd_path=usd_path,
        ftrack_task_name=ftrack_task_name,
        parent_name=parent_name,
        kb3d_asset_code=kb3d,
        vfx_shot_code=shot,
    )


def iconik_metadata_for(
    ref: VfxAssetRef,
    *,
    ftrack_version_id: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, str]:
    meta: dict[str, str] = {
        "ftrack_task_id": ref.ftrack_task_id,
        "asset_name": ref.asset_name,
        "usd_path": ref.usd_path,
        "pipeline_tool": "production_hub",
        "pipeline_domain": "vfx",
    }
    if ftrack_version_id:
        meta["ftrack_asset_version_id"] = ftrack_version_id
    if ref.ftrack_task_name:
        meta["ftrack_task_name"] = ref.ftrack_task_name
    if ref.parent_name:
        meta["ftrack_parent_name"] = ref.parent_name
    if ref.vfx_shot_code:
        meta["vfx_shot_code"] = ref.vfx_shot_code
    if ref.kb3d_asset_code:
        meta["kb3d_asset_code"] = ref.kb3d_asset_code
    if extra:
        for key, value in extra.items():
            if value is not None and str(value).strip():
                meta[str(key)] = str(value)
    return meta
