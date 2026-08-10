"""Iconik REST API client (httpx)."""

from __future__ import annotations

from typing import Any, Optional

from integrations.settings import IconikSettings, IntegrationSettings, load_settings


class IconikError(RuntimeError):
    pass


class IconikClient:
    def __init__(self, settings: Optional[IntegrationSettings] = None):
        self.settings = settings or load_settings()
        self._ik: IconikSettings = self.settings.iconik

    def _headers(self) -> dict[str, str]:
        return {
            "App-ID": self._ik.app_id,
            "Auth-Token": self._ik.auth_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        errors = self.settings.validate_iconik()
        if errors:
            raise IconikError("; ".join(errors))

        try:
            import httpx
        except ImportError as exc:
            raise ImportError("httpx is required. Install with: pip install httpx") from exc

        url = f"{self._ik.api_base()}/{path.lstrip('/')}"
        with httpx.Client(timeout=60.0) as client:
            response = client.request(
                method.upper(),
                url,
                headers=self._headers(),
                json=json_body,
                params=params,
            )
        if response.status_code >= 400:
            raise IconikError(f"Iconik {method} {path} failed ({response.status_code}): {response.text[:500]}")
        if not response.content:
            return {}
        return response.json()

    def ping(self) -> dict[str, Any]:
        """Lightweight auth check via user profile endpoint."""
        data = self.request("GET", "users/v1/users/current/")
        return {
            "id": data.get("id"),
            "email": data.get("email") or data.get("username"),
            "base_url": self._ik.base_url,
        }
