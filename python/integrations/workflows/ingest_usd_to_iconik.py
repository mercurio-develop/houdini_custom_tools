"""Orchestrate USD file ingest to Iconik (used by TOPs, CLI, and MCP)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

from integrations.iconik.upload import IconikUploader
from integrations.identifiers.vfx import build_vfx_asset_ref, iconik_metadata_for
from integrations.settings import IntegrationSettings, load_settings
from integrations.usd_discovery import content_hash

OnExistsModeLiteral = Literal["skip", "update", "new_version"]


@dataclass
class IngestRequest:
    usd_path: str
    asset_name: str | None = None
    discovery_mode: str = "primary"
    dry_run: bool = False
    extra_metadata: dict[str, str] = field(default_factory=dict)
    ftrack_task_id: str | None = None
    ftrack_task_name: str | None = None
    ftrack_parent_name: str | None = None
    on_exists: OnExistsModeLiteral = "update"
    storage_id: str | None = None


@dataclass
class IngestResult:
    success: bool
    message: str
    iconik_asset_id: str | None = None
    iconik_file_id: str | None = None
    skipped: bool = False
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


def ingest_usd_to_iconik(
    request: IngestRequest,
    settings: Optional[IntegrationSettings] = None,
) -> IngestResult:
    settings = settings or load_settings()
    errors: list[str] = []

    ik_errors = settings.validate_iconik()
    if ik_errors and not request.dry_run:
        return IngestResult(False, "Invalid Iconik settings", errors=ik_errors)

    usd_path = request.usd_path
    asset_name = request.asset_name or _basename_no_ext(usd_path)
    title = asset_name

    digest = ""
    try:
        digest = content_hash(usd_path)
    except OSError as exc:
        if not request.dry_run:
            return IngestResult(False, f"Cannot read file: {exc}", errors=[str(exc)])

    meta: dict[str, str] = dict(request.extra_metadata)
    meta["asset_name"] = asset_name
    meta["discovery_mode"] = request.discovery_mode
    if digest:
        meta["content_hash"] = digest

    if request.ftrack_task_id:
        ref = build_vfx_asset_ref(
            ftrack_task_id=request.ftrack_task_id,
            asset_name=asset_name,
            usd_path=usd_path,
            ftrack_task_name=request.ftrack_task_name,
            parent_name=request.ftrack_parent_name,
        )
        meta.update(iconik_metadata_for(ref))
    else:
        from integrations.identifiers.vfx import infer_kb3d_asset_code

        meta["usd_path"] = usd_path
        meta["pipeline_tool"] = "iconik_tops"
        meta["pipeline_domain"] = "vfx"
        kb3d = infer_kb3d_asset_code(asset_name, usd_path)
        if kb3d:
            meta["kb3d_asset_code"] = kb3d

    uploader = IconikUploader(settings=settings)
    upload = uploader.ingest_usd_file(
        local_path=usd_path,
        title=title,
        metadata=meta,
        storage_id=request.storage_id,
        dry_run=request.dry_run,
        on_exists=request.on_exists,
        content_hash=digest or None,
    )

    if not upload.success:
        errors.append(upload.message)
        return IngestResult(
            False,
            upload.message,
            errors=errors,
            details=upload.details,
        )

    return IngestResult(
        True,
        upload.message,
        iconik_asset_id=upload.asset_id,
        iconik_file_id=upload.file_id,
        skipped=upload.skipped,
        details={
            **upload.details,
            "metadata": meta,
            "dry_run": request.dry_run,
        },
    )


def _basename_no_ext(path: str) -> str:
    import os

    return os.path.splitext(os.path.basename(path))[0]
