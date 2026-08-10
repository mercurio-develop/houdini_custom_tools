#!/usr/bin/env python3
"""
MCP server exposing Production Hub integrations (ftrack, Iconik, publish).

Run (from repo python root on PYTHONPATH):
    python mcp/production_hub_server.py

Cursor MCP config example in projects/production_hub/README.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure scripts/python is on path when launched directly
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as exc:
    raise SystemExit(
        "Install MCP dependencies: pip install -r requirements-integrations.txt"
    ) from exc

from integrations.ftrack.queries import FtrackQueries
from integrations.iconik.assets import IconikAssets
from integrations.workflows.publish_usd_deliverable import PublishRequest, publish_usd_deliverable

mcp = FastMCP("Production Hub")


@mcp.tool()
def ftrack_list_projects(limit: int = 25) -> str:
    """List active ftrack projects (id and name)."""
    projects = FtrackQueries().list_projects(limit=limit)
    return json.dumps([{"id": p.id, "name": p.name} for p in projects], indent=2)


@mcp.tool()
def ftrack_list_tasks(project_id: str, limit: int = 50, name_contains: str = "") -> str:
    """List ftrack tasks for a project."""
    tasks = FtrackQueries().list_tasks_for_project(
        project_id, limit=limit, name_contains=name_contains or None
    )
    return json.dumps(
        [
            {
                "id": t.id,
                "name": t.name,
                "link": t.link,
                "project_name": t.project_name,
                "parent_name": t.parent_name,
                "status": t.status,
            }
            for t in tasks
        ],
        indent=2,
    )


@mcp.tool()
def ftrack_get_task_context(task_id: str) -> str:
    """Return ftrack task metadata for agents."""
    ctx = FtrackQueries().get_task_context(task_id)
    return json.dumps(ctx, indent=2)


@mcp.tool()
def iconik_search_assets(query: str, page_size: int = 25) -> str:
    """Search Iconik assets by free text or metadata query."""
    hits = IconikAssets().search(query, page_size=page_size)
    return json.dumps(
        [{"id": h.id, "title": h.title, "created": h.created} for h in hits],
        indent=2,
    )


@mcp.tool()
def publish_usd_deliverable_tool(
    ftrack_task_id: str,
    asset_name: str,
    usd_path: str,
    hip_path: str = "",
    comment: str = "Published via MCP Production Hub",
    ftrack_task_name: str = "",
    ftrack_parent_name: str = "",
) -> str:
    """Register USD on ftrack and link Iconik metadata."""
    result = publish_usd_deliverable(
        PublishRequest(
            ftrack_task_id=ftrack_task_id,
            asset_name=asset_name,
            usd_path=usd_path,
            hip_path=hip_path or None,
            comment=comment,
            ftrack_task_name=ftrack_task_name or None,
            ftrack_parent_name=ftrack_parent_name or None,
        )
    )
    return json.dumps(
        {
            "success": result.success,
            "message": result.message,
            "ftrack_asset_version_id": result.ftrack_asset_version_id,
            "ftrack_asset_id": result.ftrack_asset_id,
            "iconik_asset_id": result.iconik_asset_id,
            "errors": result.errors,
        },
        indent=2,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
