"""Iconik file upload (asset → format → file_set → file → storage PUT → close)."""

from __future__ import annotations

import datetime
import mimetypes
import os
import time
from typing import Any, Literal, Optional

from integrations.iconik.assets import IconikAssets
from integrations.iconik.client import IconikClient, IconikError
from integrations.iconik.models import IconikUploadResult
from integrations.settings import IntegrationSettings, load_settings

OnExistsMode = Literal["skip", "update", "new_version"]

_USD_MEDIA_TYPES = {
    ".usd": "model/vnd.usd",
    ".usda": "model/vnd.usda",
    ".usdc": "application/octet-stream",
}


def _media_type_for_path(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in _USD_MEDIA_TYPES:
        return _USD_MEDIA_TYPES[ext]
    guessed, _enc = mimetypes.guess_type(path)
    return guessed or "application/octet-stream"


class IconikUploader:
    """Upload local files to Iconik storage via the official REST sequence."""

    def __init__(
        self,
        client: Optional[IconikClient] = None,
        assets: Optional[IconikAssets] = None,
        settings: Optional[IntegrationSettings] = None,
    ):
        self.settings = settings or load_settings()
        self.client = client or IconikClient(self.settings)
        self.assets = assets or IconikAssets(self.client)

    def resolve_storage_id(self, storage_id: Optional[str] = None) -> str:
        configured = (storage_id or self.settings.iconik.storage_id or "").strip()
        if configured:
            return configured
        data = self.client.request("GET", "files/v1/storages/matching/FILES/")
        resolved = str(data.get("id", "")).strip()
        if not resolved:
            raise IconikError("No FILES storage found; set iconik.storage_id in integrations.json")
        return resolved

    def find_asset_by_metadata(self, key: str, value: str) -> Optional[str]:
        query = f'{key}:"{value}"'
        hits = self.assets.search(query, page_size=5)
        if hits:
            return hits[0].id
        return None

    def ingest_usd_file(
        self,
        *,
        local_path: str,
        title: str,
        metadata: dict[str, str],
        storage_id: str | None = None,
        dry_run: bool = False,
        on_exists: OnExistsMode = "update",
        content_hash: str | None = None,
    ) -> IconikUploadResult:
        local_path = os.path.normpath(os.path.expanduser(local_path))
        if not os.path.isfile(local_path):
            return IconikUploadResult(False, f"File not found: {local_path}")

        file_name = os.path.basename(local_path)
        file_size = os.path.getsize(local_path)
        meta = {k: str(v) for k, v in metadata.items()}
        meta.setdefault("usd_path", local_path)
        meta.setdefault("pipeline_tool", "iconik_tops")
        if content_hash:
            meta["content_hash"] = content_hash

        if dry_run:
            return IconikUploadResult(
                True,
                f"Dry run: would upload {local_path} ({file_size} bytes) as '{title}'",
                details={"metadata": meta, "file_size": file_size},
            )

        existing_id = self.find_asset_by_metadata("usd_path", local_path)
        if not existing_id and content_hash:
            existing_id = self.find_asset_by_metadata("content_hash", content_hash)

        if existing_id and on_exists == "skip":
            return IconikUploadResult(
                True,
                f"Skipped existing Iconik asset {existing_id}",
                asset_id=existing_id,
                skipped=True,
            )

        try:
            if existing_id and on_exists == "update":
                self.client.request(
                    "PATCH",
                    f"files/v1/assets/{existing_id}/",
                    json_body={"title": title, "metadata": meta},
                )
                upload_result = self._upload_file_to_asset(
                    asset_id=existing_id,
                    local_path=local_path,
                    file_name=file_name,
                    file_size=file_size,
                    storage_id=self.resolve_storage_id(storage_id),
                )
                if upload_result.success:
                    upload_result.message = f"Updated asset {existing_id} and uploaded {file_name}"
                return upload_result

            asset_id = self._create_asset(title)
            self.client.request(
                "PATCH",
                f"files/v1/assets/{asset_id}/",
                json_body={"metadata": meta},
            )
            result = self._upload_file_to_asset(
                asset_id=asset_id,
                local_path=local_path,
                file_name=file_name,
                file_size=file_size,
                storage_id=self.resolve_storage_id(storage_id),
            )
            if result.success:
                result.message = f"Created asset {asset_id} and uploaded {file_name}"
            return result
        except IconikError as exc:
            return IconikUploadResult(False, str(exc))
        except Exception as exc:
            return IconikUploadResult(False, f"Upload failed: {exc}")

    def _create_asset(self, title: str) -> str:
        created = self.client.request(
            "POST",
            "assets/v1/assets/",
            json_body={
                "title": title,
                "type": "ASSET",
                "status": "ACTIVE",
                "analyze_status": "N/A",
                "archive_status": "NOT_ARCHIVED",
                "is_online": True,
            },
        )
        asset_id = str(created.get("id", "")).strip()
        if not asset_id:
            raise IconikError("Iconik asset create returned no id")
        return asset_id

    def _upload_file_to_asset(
        self,
        *,
        asset_id: str,
        local_path: str,
        file_name: str,
        file_size: int,
        storage_id: str,
    ) -> IconikUploadResult:
        asset_meta = self.client.request("GET", f"assets/v1/assets/{asset_id}/")
        user_id = asset_meta.get("created_by_user") or asset_meta.get("created_by")
        if not user_id:
            user_id = self._current_user_id()

        media_type = _media_type_for_path(local_path)
        format_payload = {
            "user_id": user_id,
            "name": "ORIGINAL",
            "metadata": [{"internet_media_type": media_type}],
            "storage_methods": ["GCS"],
        }
        fmt = self.client.request(
            "POST",
            f"files/v1/assets/{asset_id}/formats/",
            json_body=format_payload,
        )
        format_id = str(fmt.get("id", ""))
        if not format_id:
            raise IconikError("Iconik format create returned no id")

        fileset = self.client.request(
            "POST",
            f"files/v1/assets/{asset_id}/file_sets/",
            json_body={
                "format_id": format_id,
                "storage_id": storage_id,
                "base_dir": "/",
                "name": file_name,
                "component_ids": [],
            },
        )
        fileset_id = str(fileset.get("id", ""))
        if not fileset_id:
            raise IconikError("Iconik file_set create returned no id")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        file_info = {
            "original_name": file_name,
            "directory_path": "",
            "size": file_size,
            "type": "FILE",
            "metadata": {},
            "format_id": format_id,
            "file_set_id": fileset_id,
            "storage_id": storage_id,
            "file_date_created": now,
            "file_date_modified": now,
        }
        file_rec = self.client.request(
            "POST",
            f"files/v1/assets/{asset_id}/files/",
            json_body=file_info,
        )
        upload_url = file_rec.get("upload_url")
        file_id = str(file_rec.get("id", ""))
        if not upload_url or not file_id:
            raise IconikError("Iconik file create returned no upload_url or file id")

        job_id = self._start_transfer_job(asset_id, file_name)
        self._put_file_to_storage(upload_url, local_path, file_size, asset_id, file_id)
        self._close_file(asset_id, file_id)
        if job_id:
            self._finish_job(job_id)

        try:
            self.client.request(
                "POST",
                f"files/v1/assets/{asset_id}/files/{file_id}/keyframes/",
            )
        except IconikError:
            pass

        return IconikUploadResult(
            True,
            f"Uploaded {file_name} to asset {asset_id}",
            asset_id=asset_id,
            file_id=file_id,
            job_id=job_id,
            details={"file_size": file_size, "storage_id": storage_id},
        )

    def _current_user_id(self) -> str:
        data = self.client.ping()
        user_id = str(data.get("id", "")).strip()
        if not user_id:
            raise IconikError("Could not resolve Iconik user id for format creation")
        return user_id

    def _start_transfer_job(self, asset_id: str, file_name: str) -> Optional[str]:
        try:
            job = self.client.request(
                "POST",
                "jobs/v1/jobs/",
                json_body={
                    "object_type": "assets",
                    "object_id": asset_id,
                    "type": "TRANSFER",
                    "status": "STARTED",
                    "title": f"Upload {file_name}",
                },
            )
            return str(job.get("id", "")) or None
        except IconikError:
            return None

    def _finish_job(self, job_id: str) -> None:
        try:
            self.client.request(
                "PATCH",
                f"jobs/v1/jobs/{job_id}/",
                json_body={"progress_processed": 100, "status": "FINISHED"},
            )
        except IconikError:
            pass

    def _put_file_to_storage(
        self,
        upload_url: str,
        local_path: str,
        file_size: int,
        asset_id: str,
        file_id: str,
    ) -> None:
        import httpx

        retries = max(1, int(self.settings.iconik.max_upload_retries))
        last_error: Optional[Exception] = None
        domain = self.settings.iconik.base_url.rstrip("/")

        for attempt in range(retries):
            try:
                if "googleapis.com" in upload_url or "storage.googleapis.com" in upload_url:
                    self._gcs_resumable_upload(upload_url, local_path, file_size, domain)
                else:
                    with open(local_path, "rb") as fh:
                        with httpx.Client(timeout=600.0) as http:
                            response = http.put(
                                upload_url,
                                content=fh.read(),
                                headers={
                                    "Content-Length": str(file_size),
                                    "Content-Type": "application/octet-stream",
                                },
                            )
                            if response.status_code >= 400:
                                raise IconikError(
                                    f"Storage PUT failed ({response.status_code}): {response.text[:300]}"
                                )

                try:
                    self.client.request(
                        "POST",
                        f"files/v1/assets/{asset_id}/files/{file_id}/multipart/gcs/compose_url/",
                        json_body={"parts_group": None, "content_type": "application/octet-stream"},
                    )
                except IconikError:
                    pass
                return
            except Exception as exc:
                last_error = exc
                if attempt + 1 < retries:
                    time.sleep(1.5 * (attempt + 1))
        raise IconikError(f"Storage upload failed after {retries} attempts: {last_error}")

    def _gcs_resumable_upload(
        self, upload_url: str, local_path: str, file_size: int, domain: str
    ) -> None:
        import httpx

        start_headers = {
            "Content-Length": "0",
            "x-goog-resumable": "start",
            "Origin": domain,
            "Referer": f"{domain}/upload",
        }
        with httpx.Client(timeout=120.0) as http:
            start_resp = http.post(upload_url, headers=start_headers)
            if start_resp.status_code >= 400:
                raise IconikError(f"GCS resumable start failed ({start_resp.status_code})")
            upload_id = start_resp.headers.get("X-GUploader-UploadID") or start_resp.headers.get(
                "x-guploader-uploadid"
            )
            if not upload_id:
                raise IconikError("GCS resumable upload did not return X-GUploader-UploadID")

            put_headers = {
                "Content-Length": str(file_size),
                "Content-Type": "application/x-www-form-urlencoded",
                "x-goog-resumable": "start",
                "Origin": domain,
                "Referer": f"{domain}/upload",
            }
            full_url = f"{upload_url}&upload_id={upload_id}"
            with open(local_path, "rb") as fh:
                put_resp = http.put(full_url, headers=put_headers, content=fh.read())
            if put_resp.status_code >= 400:
                raise IconikError(f"GCS upload PUT failed ({put_resp.status_code}): {put_resp.text[:300]}")

    def _close_file(self, asset_id: str, file_id: str) -> None:
        self.client.request(
            "PATCH",
            f"files/v1/assets/{asset_id}/files/{file_id}/",
            json_body={"status": "CLOSED", "progress_processed": 100},
        )
