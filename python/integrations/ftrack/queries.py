"""Read-only ftrack queries for UI and MCP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from integrations.ftrack.session import FtrackService, create_session, create_service
from integrations.settings import load_settings


@dataclass(frozen=True)
class FtrackProjectSummary:
    id: str
    name: str
    full_name: str


@dataclass(frozen=True)
class FtrackTaskSummary:
    id: str
    name: str
    link: str
    project_id: str
    project_name: str
    parent_name: str
    status: str


class FtrackQueries:
    def __init__(self, service: Optional[FtrackService] = None):
        session = create_session() if service is None else service.session
        if service is None:
            settings = load_settings()
            self._service = FtrackService(session, api_user=settings.ftrack.api_user)
        else:
            self._service = service

    @property
    def session(self):
        return self._service.session

    def list_projects(self, limit: int = 50) -> list[FtrackProjectSummary]:
        projects = self.session.query(f"Project where status is active order by name asc limit {int(limit)}")
        out: list[FtrackProjectSummary] = []
        for proj in projects:
            out.append(
                FtrackProjectSummary(
                    id=proj["id"],
                    name=proj["name"],
                    full_name=proj["name"],
                )
            )
        return out

    def list_tasks_for_project(
        self,
        project_id: str,
        limit: int = 200,
        name_contains: Optional[str] = None,
    ) -> list[FtrackTaskSummary]:
        query = (
            f"Task where project.id is '{project_id}' "
            f"order by name asc limit {int(limit)}"
        )
        tasks = self.session.query(query)
        results: list[FtrackTaskSummary] = []
        needle = (name_contains or "").lower()
        for task in tasks:
            if needle and needle not in task["name"].lower():
                continue
            parent = task["parent"]
            project = task["project"]
            results.append(
                FtrackTaskSummary(
                    id=task["id"],
                    name=task["name"],
                    link=task["link"],
                    project_id=project["id"],
                    project_name=project["name"],
                    parent_name=parent["name"] if parent else "",
                    status=task["status"]["name"] if task.get("status") else "",
                )
            )
        return results

    def get_task_context(self, task_id: str) -> dict[str, Any]:
        task = self.session.get("Task", task_id)
        if task is None:
            raise ValueError(f"Task not found: {task_id}")
        project = task["project"]
        parent = task["parent"]
        return {
            "id": task["id"],
            "name": task["name"],
            "link": task["link"],
            "status": task["status"]["name"] if task.get("status") else "",
            "project_id": project["id"],
            "project_name": project["name"],
            "parent_id": parent["id"] if parent else None,
            "parent_name": parent["name"] if parent else "",
            "parent_type": parent.entity_type if parent else None,
        }
