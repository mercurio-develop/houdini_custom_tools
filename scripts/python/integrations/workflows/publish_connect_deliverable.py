"""Publish Connect-style multi-component exports to ftrack (+ optional Iconik)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from integrations.ftrack.publish import ComponentSpec, FtrackPublisher
from integrations.iconik.assets import IconikAssets
from integrations.identifiers.vfx import build_vfx_asset_ref, iconik_metadata_for
from integrations.settings import IntegrationSettings, load_settings


@dataclass
class ConnectPublishRequest:
    ftrack_task_id: str
    asset_name: str
    asset_kind: str
    components: list[ComponentSpec]
    hip_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    comment: str = "Published from Production Hub (Connect export)"
    task_status_name: Optional[str] = None
    ftrack_task_name: Optional[str] = None
    ftrack_parent_name: Optional[str] = None
    link_iconik: bool = True


@dataclass
class ConnectPublishResult:
    success: bool
    message: str
    ftrack_asset_version_id: Optional[str] = None
    ftrack_asset_id: Optional[str] = None
    iconik_asset_id: Optional[str] = None
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def publish_connect_deliverable(
    request: ConnectPublishRequest,
    settings: Optional[IntegrationSettings] = None,
) -> ConnectPublishResult:
    settings = settings or load_settings()
    errors: list[str] = []
    details: dict[str, Any] = {"asset_kind": request.asset_kind}

    ft_errors = settings.validate_ftrack()
    if ft_errors:
        return ConnectPublishResult(False, "Invalid ftrack settings", errors=ft_errors)

    primary_path = request.components[0].path if request.components else ""
    meta = {
        "asset_name": request.asset_name,
        "connect_asset_kind": request.asset_kind,
        "hip_path": request.hip_path or "",
    }

    publisher = FtrackPublisher(settings=settings)
    ft_result = publisher.publish_components(
        request.ftrack_task_id,
        request.components,
        asset_name=request.asset_name,
        asset_type_name=request.asset_kind,
        comment=request.comment,
        metadata=meta,
        thumbnail_path=request.thumbnail_path,
        task_status_name=request.task_status_name,
    )
    details["ftrack"] = {
        "success": ft_result.success,
        "message": ft_result.message,
        "component_ids": ft_result.component_ids,
    }
    if not ft_result.success:
        return ConnectPublishResult(
            False,
            ft_result.message,
            errors=[ft_result.message],
            details=details,
        )

    ik_result = None
    if request.link_iconik and not settings.validate_iconik():
        vfx_ref = build_vfx_asset_ref(
            ftrack_task_id=request.ftrack_task_id,
            asset_name=request.asset_name,
            usd_path=primary_path,
            ftrack_task_name=request.ftrack_task_name,
            parent_name=request.ftrack_parent_name,
        )
        iconik_meta = iconik_metadata_for(
            vfx_ref,
            ftrack_version_id=ft_result.asset_version_id,
            extra={
                "hip_path": request.hip_path or "",
                "connect_asset_kind": request.asset_kind,
                "primary_component": request.components[0].name if request.components else "",
            },
        )
        iconik = IconikAssets()
        ik_result = iconik.upsert_ftrack_link(
            title=request.asset_name,
            ftrack_task_id=request.ftrack_task_id,
            ftrack_version_id=ft_result.asset_version_id,
            usd_path=primary_path,
            metadata=iconik_meta,
        )
        details["iconik"] = {"success": ik_result.success, "message": ik_result.message}
        if not ik_result.success:
            errors.append(f"iconik: {ik_result.message}")
    elif settings.validate_iconik():
        details["iconik"] = {"skipped": True, "reason": "; ".join(settings.validate_iconik())}

    msg = ft_result.message
    if ik_result and ik_result.success:
        msg = f"{msg}; Iconik linked"

    return ConnectPublishResult(
        success=ft_result.success and (ik_result is None or ik_result.success),
        message=msg,
        ftrack_asset_version_id=ft_result.asset_version_id,
        ftrack_asset_id=ft_result.asset_id,
        iconik_asset_id=ik_result.asset_id if ik_result else None,
        errors=errors,
        details=details,
    )
