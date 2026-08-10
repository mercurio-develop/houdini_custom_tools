"""Orchestrate ftrack + Iconik publish after USD delivery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from integrations.ftrack.publish import FtrackPublisher
from integrations.iconik.assets import IconikAssets
from integrations.identifiers.vfx import build_vfx_asset_ref, iconik_metadata_for
from integrations.settings import IntegrationSettings, load_settings


@dataclass
class PublishRequest:
    ftrack_task_id: str
    asset_name: str
    usd_path: str
    hip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    comment: str = "Published from Production Hub"
    builder_result: Optional[dict[str, Any]] = None
    ftrack_task_name: Optional[str] = None
    ftrack_parent_name: Optional[str] = None
    task_status_name: Optional[str] = None


@dataclass
class PublishResult:
    success: bool
    message: str
    ftrack_asset_version_id: Optional[str] = None
    ftrack_asset_id: Optional[str] = None
    iconik_asset_id: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def publish_usd_deliverable(
    request: PublishRequest,
    settings: Optional[IntegrationSettings] = None,
) -> PublishResult:
    settings = settings or load_settings()
    errors: list[str] = []
    details: dict[str, Any] = {}

    ft_errors = settings.validate_ftrack()
    if ft_errors:
        return PublishResult(False, "Invalid ftrack settings", errors=ft_errors)

    meta: dict[str, Any] = {"asset_name": request.asset_name}
    if request.hip_path:
        meta["hip_path"] = request.hip_path
    if request.builder_result:
        meta["builder_success"] = request.builder_result.get("success")
        if request.builder_result.get("message"):
            meta["builder_message"] = str(request.builder_result["message"])

    publisher = FtrackPublisher(settings=settings)
    ft_result = publisher.publish_usd(
        request.ftrack_task_id,
        request.usd_path,
        asset_name=request.asset_name,
        comment=request.comment,
        metadata=meta,
        thumbnail_path=request.thumbnail_path,
        task_status_name=request.task_status_name,
    )
    details["ftrack"] = {
        "success": ft_result.success,
        "message": ft_result.message,
        "asset_version_id": ft_result.asset_version_id,
    }
    if not ft_result.success:
        errors.append(f"ftrack: {ft_result.message}")
        return PublishResult(
            False,
            "ftrack publish failed",
            errors=errors,
            details=details,
        )

    ik_result = None
    ik_errors = settings.validate_iconik()
    if not ik_errors:
        vfx_ref = build_vfx_asset_ref(
            ftrack_task_id=request.ftrack_task_id,
            asset_name=request.asset_name,
            usd_path=request.usd_path,
            ftrack_task_name=request.ftrack_task_name,
            parent_name=request.ftrack_parent_name,
        )
        details["vfx_ref"] = {
            "kb3d_asset_code": vfx_ref.kb3d_asset_code,
            "vfx_shot_code": vfx_ref.vfx_shot_code,
        }
        iconik_meta = iconik_metadata_for(
            vfx_ref,
            ftrack_version_id=ft_result.asset_version_id,
            extra={
                "hip_path": request.hip_path or "",
                "thumbnail_path": request.thumbnail_path or "",
            },
        )
        iconik = IconikAssets()
        ik_result = iconik.upsert_ftrack_link(
            title=request.asset_name,
            ftrack_task_id=request.ftrack_task_id,
            ftrack_version_id=ft_result.asset_version_id,
            usd_path=request.usd_path,
            metadata=iconik_meta,
        )
        details["iconik"] = {"success": ik_result.success, "message": ik_result.message}
        if not ik_result.success:
            errors.append(f"iconik: {ik_result.message}")
    else:
        details["iconik"] = {"skipped": True, "reason": "; ".join(ik_errors)}

    success = ft_result.success and (ik_result is None or ik_result.success)
    msg = ft_result.message
    if ik_result and ik_result.success:
        msg = f"{msg}; Iconik linked"

    return PublishResult(
        success=success,
        message=msg,
        ftrack_asset_version_id=ft_result.asset_version_id,
        ftrack_asset_id=ft_result.asset_id,
        iconik_asset_id=ik_result.asset_id if ik_result else None,
        errors=errors,
        details=details,
    )
