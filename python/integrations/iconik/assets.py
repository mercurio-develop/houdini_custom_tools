"""Iconik asset search and metadata updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from integrations.iconik.client import IconikClient, IconikError


@dataclass(frozen=True)
class IconikAssetSummary:
    id: str
    title: str
    created: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass
class IconikLinkResult:
    success: bool
    message: str
    asset_id: Optional[str] = None


class IconikAssets:
    def __init__(self, client: Optional[IconikClient] = None):
        self.client = client or IconikClient()

    def search(self, query: str, *, page_size: int = 25) -> list[IconikAssetSummary]:
        body = {
            "query": query,
            "page": 1,
            "per_page": int(page_size),
        }
        data = self.client.request("POST", "search/v1/search/", json_body=body)
        objects = data.get("objects") or data.get("results") or []
        out: list[IconikAssetSummary] = []
        for obj in objects:
            asset_id = obj.get("id") or obj.get("object_id")
            if not asset_id:
                continue
            title = obj.get("title") or obj.get("name") or str(asset_id)
            out.append(
                IconikAssetSummary(
                    id=str(asset_id),
                    title=str(title),
                    created=obj.get("date_created"),
                    metadata=obj.get("metadata") if isinstance(obj.get("metadata"), dict) else None,
                )
            )
        return out

    def upsert_ftrack_link(
        self,
        *,
        title: str,
        ftrack_task_id: str,
        ftrack_version_id: Optional[str] = None,
        usd_path: Optional[str] = None,
        extra_metadata: Optional[dict[str, str]] = None,
        metadata: Optional[dict[str, str]] = None,
    ) -> IconikLinkResult:
        """Create a collection asset or patch metadata linking ftrack ids (v1: metadata-first)."""
        if metadata is not None:
            merged = {k: str(v) for k, v in metadata.items()}
        else:
            merged = {
                "ftrack_task_id": ftrack_task_id,
                "pipeline_tool": "production_hub",
            }
            if ftrack_version_id:
                merged["ftrack_asset_version_id"] = ftrack_version_id
            if usd_path:
                merged["usd_path"] = usd_path
            if extra_metadata:
                merged.update({k: str(v) for k, v in extra_metadata.items()})
        metadata = merged

        search_hits = self.search(f"ftrack_task_id:{ftrack_task_id}", page_size=5)
        if search_hits:
            asset_id = search_hits[0].id
            try:
                self.client.request(
                    "PATCH",
                    f"files/v1/assets/{asset_id}/",
                    json_body={"title": title, "metadata": metadata},
                )
                return IconikLinkResult(True, f"Updated Iconik asset {asset_id}", asset_id=asset_id)
            except IconikError as exc:
                return IconikLinkResult(False, str(exc))

        try:
            created = self.client.request(
                "POST",
                "files/v1/assets/",
                json_body={
                    "title": title,
                    "type": "ASSET",
                    "metadata": metadata,
                },
            )
            asset_id = str(created.get("id", ""))
            if not asset_id:
                return IconikLinkResult(False, "Iconik create returned no asset id")
            return IconikLinkResult(True, f"Created Iconik asset {asset_id}", asset_id=asset_id)
        except IconikError as exc:
            return IconikLinkResult(False, str(exc))
