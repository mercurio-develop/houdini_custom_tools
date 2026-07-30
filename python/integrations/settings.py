"""Load ftrack / Iconik credentials from environment and optional JSON config."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Optional


def _expand_path(path: str) -> str:
    custom = os.environ.get("CUSTOM_TOOLS", "")
    if custom and "$CUSTOM_TOOLS" in path:
        path = path.replace("$CUSTOM_TOOLS", custom)
    return os.path.expanduser(os.path.expandvars(path))


def _config_search_paths() -> list[str]:
    paths: list[str] = []
    custom = os.environ.get("CUSTOM_TOOLS", "")
    if custom:
        paths.append(os.path.join(custom, "config", "integrations.json"))
    env_path = os.environ.get("PRODUCTION_HUB_CONFIG", "")
    if env_path:
        paths.append(_expand_path(env_path))
    repo_fallback = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "config",
        "integrations.json",
    )
    paths.append(_expand_path(repo_fallback))
    return paths


@dataclass(frozen=True)
class FtrackSettings:
    server_url: str
    api_user: str
    api_key: str

    def masked_summary(self) -> str:
        key = self.api_key
        masked = (key[:4] + "…" + key[-4:]) if len(key) > 8 else "****"
        return f"{self.api_user} @ {self.server_url} (key {masked})"


@dataclass(frozen=True)
class IconikSettings:
    base_url: str
    app_id: str
    auth_token: str

    def api_base(self) -> str:
        base = self.base_url.rstrip("/")
        if not base.endswith("/API"):
            base = f"{base}/API"
        return base

    def masked_summary(self) -> str:
        tok = self.auth_token
        masked = (tok[:4] + "…" + tok[-4:]) if len(tok) > 8 else "****"
        return f"app {self.app_id} @ {self.base_url} (token {masked})"


@dataclass(frozen=True)
class IntegrationSettings:
    ftrack: FtrackSettings
    iconik: IconikSettings
    publish_location_name: str = "auto"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "IntegrationSettings":
        ft = data.get("ftrack") or {}
        ik = data.get("iconik") or {}
        return cls(
            ftrack=FtrackSettings(
                server_url=_env_or(ft, "server_url", "FTRACK_SERVER_URL", ""),
                api_user=_env_or(ft, "api_user", "FTRACK_API_USER", ""),
                api_key=_env_or(ft, "api_key", "FTRACK_API_KEY", ""),
            ),
            iconik=IconikSettings(
                base_url=_env_or(ik, "base_url", "ICONIK_BASE_URL", "https://app.iconik.io"),
                app_id=_env_or(ik, "app_id", "ICONIK_APP_ID", ""),
                auth_token=_env_or(
                    ik,
                    "auth_token",
                    "ICONIK_AUTH_TOKEN",
                    _env_or(ik, "api_key", "ICONIK_API_KEY", ""),
                ),
            ),
            publish_location_name=str(data.get("publish_location_name", "auto")),
        )

    def validate_ftrack(self) -> list[str]:
        errors: list[str] = []
        if not self.ftrack.server_url:
            errors.append("ftrack.server_url (or FTRACK_SERVER_URL) is required")
        if not self.ftrack.api_user:
            errors.append("ftrack.api_user (or FTRACK_API_USER) is required")
        if not self.ftrack.api_key:
            errors.append("ftrack.api_key (or FTRACK_API_KEY) is required")
        return errors

    def validate_iconik(self) -> list[str]:
        errors: list[str] = []
        if not self.iconik.app_id:
            errors.append("iconik.app_id (or ICONIK_APP_ID) is required")
        if not self.iconik.auth_token:
            errors.append("iconik.auth_token (or ICONIK_AUTH_TOKEN) is required")
        return errors


def _env_or(section: dict[str, Any], json_key: str, env_key: str, default: str) -> str:
    env_val = os.environ.get(env_key, "").strip()
    if env_val:
        return env_val
    val = section.get(json_key, default)
    return str(val).strip() if val is not None else default


def load_settings(config_path: Optional[str] = None) -> IntegrationSettings:
    """Merge JSON config (if present) with environment variables (env wins)."""
    merged: dict[str, Any] = {}
    paths = [_expand_path(config_path)] if config_path else _config_search_paths()
    for path in paths:
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                merged = json.load(fh)
            break
    return IntegrationSettings.from_mapping(merged)


def example_config_dict() -> dict[str, Any]:
    return {
        "ftrack": {
            "server_url": "https://YOUR_STUDIO.ftrackapp.com",
            "api_user": "your.api.user@example.com",
            "api_key": "YOUR_FTRACK_API_KEY",
        },
        "iconik": {
            "base_url": "https://app.iconik.io",
            "app_id": "YOUR_ICONIK_APP_ID",
            "auth_token": "YOUR_ICONIK_AUTH_TOKEN",
        },
        "publish_location_name": "auto",
    }
