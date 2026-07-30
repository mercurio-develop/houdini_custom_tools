"""
FastAPI read-only + publish API wrapping integrations (Phase 2 web dashboard).

Run:
    uvicorn integrations.http_api:app --reload --port 8765

Set PYTHONPATH to scripts/python and configure integrations.json / env vars.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from integrations.ftrack.queries import FtrackQueries
from integrations.iconik.assets import IconikAssets
from integrations.workflows.publish_usd_deliverable import PublishRequest, publish_usd_deliverable

app = FastAPI(title="Production Hub API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PublishBody(BaseModel):
    ftrack_task_id: str
    asset_name: str
    usd_path: str
    hip_path: Optional[str] = None
    comment: str = "Published from Production Hub API"
    ftrack_task_name: Optional[str] = None
    ftrack_parent_name: Optional[str] = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ftrack/projects")
def list_projects(limit: int = 50) -> list[dict[str, str]]:
    try:
        return [{"id": p.id, "name": p.name} for p in FtrackQueries().list_projects(limit=limit)]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/ftrack/projects/{project_id}/tasks")
def list_tasks(project_id: str, limit: int = 100, q: str = "") -> list[dict[str, Any]]:
    try:
        tasks = FtrackQueries().list_tasks_for_project(
            project_id, limit=limit, name_contains=q or None
        )
        return [
            {
                "id": t.id,
                "name": t.name,
                "link": t.link,
                "status": t.status,
                "parent_name": t.parent_name,
            }
            for t in tasks
        ]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/ftrack/tasks/{task_id}")
def task_context(task_id: str) -> dict[str, Any]:
    try:
        return FtrackQueries().get_task_context(task_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/iconik/search")
def iconik_search(q: str, page_size: int = 25) -> list[dict[str, Any]]:
    try:
        hits = IconikAssets().search(q, page_size=page_size)
        return [{"id": h.id, "title": h.title, "created": h.created} for h in hits]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/publish")
def publish(body: PublishBody) -> dict[str, Any]:
    try:
        result = publish_usd_deliverable(
            PublishRequest(
                ftrack_task_id=body.ftrack_task_id,
                asset_name=body.asset_name,
                usd_path=body.usd_path,
                hip_path=body.hip_path,
                comment=body.comment,
                ftrack_task_name=body.ftrack_task_name,
                ftrack_parent_name=body.ftrack_parent_name,
            )
        )
        return {
            "success": result.success,
            "message": result.message,
            "ftrack_asset_version_id": result.ftrack_asset_version_id,
            "ftrack_asset_id": result.ftrack_asset_id,
            "iconik_asset_id": result.iconik_asset_id,
            "errors": result.errors,
            "details": result.details,
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
