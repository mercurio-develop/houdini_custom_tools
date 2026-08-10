"""Publish asset versions to ftrack from local USD paths."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Optional

from integrations.ftrack.session import FtrackService, create_session, create_service
from integrations.settings import IntegrationSettings, load_settings


@dataclass
class FtrackPublishResult:
    success: bool
    message: str
    asset_id: Optional[str] = None
    asset_version_id: Optional[str] = None
    component_id: Optional[str] = None
    component_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComponentSpec:
    name: str
    path: str
    file_type: Optional[str] = None


class FtrackPublisher:
    def __init__(
        self,
        service: Optional[FtrackService] = None,
        settings: Optional[IntegrationSettings] = None,
    ):
        self.settings = settings or load_settings()
        self._service = service or create_service(self.settings)

    @property
    def session(self):
        return self._service.session

    def _resolve_location(self):
        name = self.settings.publish_location_name
        if name and name.lower() != "auto":
            loc = self.session.query(f"Location where name is '{name}'").first()
            if loc:
                return loc
        loc = self.session.query('Location where name is "auto"').first()
        if loc is None:
            loc = self.session.query("Location").first()
        if loc is None:
            raise RuntimeError("No ftrack location available for component registration")
        return loc

    def _get_or_create_asset(self, task, asset_name: str):
        session = self.session
        parent = task["parent"]
        asset_type = session.query("AssetType where name is 'Production'").first()
        if asset_type is None:
            asset_type = session.query("AssetType").first()
        if asset_type is None:
            raise RuntimeError("No AssetType found in ftrack")

        existing = session.query(
            f"Asset where name is '{asset_name}' and parent.id is '{parent['id']}'"
        ).first()
        if existing:
            return existing

        return session.create(
            "Asset",
            {
                "name": asset_name,
                "type": asset_type,
                "parent": parent,
            },
        )

    def _resolve_asset_type(self, type_name: Optional[str]):
        session = self.session
        if type_name:
            for query_name in (type_name, type_name.capitalize(), "Production"):
                found = session.query(f"AssetType where name is '{query_name}'").first()
                if found:
                    return found
        found = session.query("AssetType where name is 'Production'").first()
        return found or session.query("AssetType").first()

    def _get_or_create_asset_typed(self, task, asset_name: str, asset_type_name: Optional[str]):
        session = self.session
        parent = task["parent"]
        asset_type = self._resolve_asset_type(asset_type_name)
        if asset_type is None:
            raise RuntimeError("No AssetType found in ftrack")

        existing = session.query(
            f"Asset where name is '{asset_name}' and parent.id is '{parent['id']}'"
        ).first()
        if existing:
            return existing

        return session.create(
            "Asset",
            {
                "name": asset_name,
                "type": asset_type,
                "parent": parent,
            },
        )

    def publish_components(
        self,
        task_id: str,
        components: list[ComponentSpec],
        *,
        asset_name: Optional[str] = None,
        asset_type_name: Optional[str] = None,
        comment: str = "Published from Production Hub",
        metadata: Optional[dict[str, Any]] = None,
        thumbnail_path: Optional[str] = None,
        task_status_name: Optional[str] = None,
    ) -> FtrackPublishResult:
        if not components:
            return FtrackPublishResult(False, "No components to publish")

        session = self.session
        task = session.get("Task", task_id)
        if task is None:
            return FtrackPublishResult(False, f"Task not found: {task_id}")

        asset_name = asset_name or task["name"]
        meta = dict(metadata or {})
        meta.setdefault("tool", "production_hub_connect")

        for spec in components:
            path = os.path.abspath(os.path.expanduser(spec.path))
            if not os.path.isfile(path):
                return FtrackPublishResult(False, f"Missing file: {path}")

        try:
            asset = self._get_or_create_asset_typed(task, asset_name, asset_type_name)
            asset_version = session.create(
                "AssetVersion",
                {"asset": asset, "comment": comment, "task": task},
            )
            for key, value in meta.items():
                asset_version["metadata"][key] = str(value)

            location = self._resolve_location()
            component_ids: list[str] = []
            first_id: Optional[str] = None

            for spec in components:
                path = os.path.abspath(os.path.expanduser(spec.path))
                ft = spec.file_type or os.path.splitext(path)[1].lstrip(".") or "bin"
                component = session.create(
                    "Component",
                    {"name": spec.name, "file_type": ft},
                )
                component["component_locations"] = [
                    session.create(
                        "ComponentLocation",
                        {"location": location, "resource_identifier": path},
                    )
                ]
                asset_version.components.append(component)
                component_ids.append(component["id"])
                if first_id is None:
                    first_id = component["id"]

            self._attach_thumbnail(asset_version, thumbnail_path)
            self._maybe_set_task_status(task, task_status_name)
            session.commit()

            return FtrackPublishResult(
                success=True,
                message=f"Published {asset_name} v{asset_version['version']} ({len(components)} component(s))",
                asset_id=asset["id"],
                asset_version_id=asset_version["id"],
                component_id=first_id,
                component_ids=component_ids,
                metadata=meta,
            )
        except Exception as exc:
            session.rollback()
            return FtrackPublishResult(False, str(exc))

    def publish_usd(
        self,
        task_id: str,
        usd_path: str,
        *,
        asset_name: Optional[str] = None,
        comment: str = "Published from Production Hub",
        metadata: Optional[dict[str, Any]] = None,
        thumbnail_path: Optional[str] = None,
        task_status_name: Optional[str] = None,
    ) -> FtrackPublishResult:
        usd_path = os.path.abspath(os.path.expanduser(usd_path))
        if not os.path.isfile(usd_path):
            return FtrackPublishResult(False, f"USD file not found: {usd_path}")

        session = self.session
        task = session.get("Task", task_id)
        if task is None:
            return FtrackPublishResult(False, f"Task not found: {task_id}")

        asset_name = asset_name or task["name"]
        meta = dict(metadata or {})
        meta.setdefault("tool", "production_hub")
        meta.setdefault("usd_path", usd_path)

        try:
            asset = self._get_or_create_asset(task, asset_name)
            asset_version = session.create(
                "AssetVersion",
                {
                    "asset": asset,
                    "comment": comment,
                    "task": task,
                },
            )
            for key, value in meta.items():
                asset_version["metadata"][key] = str(value)

            location = self._resolve_location()
            component = session.create(
                "Component",
                {
                    "name": "main",
                    "file_type": os.path.splitext(usd_path)[1].lstrip(".") or "usd",
                },
            )
            component["component_locations"] = [
                session.create(
                    "ComponentLocation",
                    {"location": location, "resource_identifier": usd_path},
                )
            ]
            asset_version.components.append(component)
            self._attach_thumbnail(asset_version, thumbnail_path)
            self._maybe_set_task_status(task, task_status_name)
            session.commit()

            return FtrackPublishResult(
                success=True,
                message=f"Published {asset_name} v{asset_version['version']}",
                asset_id=asset["id"],
                asset_version_id=asset_version["id"],
                component_id=component["id"],
                metadata=meta,
            )
        except Exception as exc:
            session.rollback()
            return FtrackPublishResult(False, str(exc))

    def _attach_thumbnail(self, asset_version, thumbnail_path: Optional[str]) -> None:
        if not thumbnail_path:
            return
        path = os.path.abspath(os.path.expanduser(thumbnail_path))
        if not os.path.isfile(path):
            return
        session = self.session
        try:
            location = self._resolve_location()
            thumb = session.create(
                "Component",
                {"name": "thumbnail", "file_type": os.path.splitext(path)[1].lstrip(".") or "jpg"},
            )
            thumb["component_locations"] = [
                session.create(
                    "ComponentLocation",
                    {"location": location, "resource_identifier": path},
                )
            ]
            asset_version.components.append(thumb)
        except Exception:
            asset_version["metadata"]["thumbnail_path"] = path

    def _maybe_set_task_status(self, task, status_name: Optional[str]) -> None:
        if not status_name:
            return
        session = self.session
        status = session.query(f"Status where name is '{status_name}'").first()
        if status is None:
            return
        if task.get("status") and task["status"]["id"] == status["id"]:
            return
        task["status"] = status
