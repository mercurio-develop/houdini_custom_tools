"""ftrack session lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from integrations.settings import FtrackSettings, IntegrationSettings, load_settings

if TYPE_CHECKING:
    import ftrack_api


class FtrackService:
    """Thin wrapper around ftrack_api.Session."""

    def __init__(self, session: "ftrack_api.Session", api_user: str = ""):
        self.session = session
        self.api_user = api_user

    def ping(self) -> dict:
        user = None
        if self.api_user:
            user = self.session.query(
                f"User where username is '{self.api_user}'"
            ).first()
            if user is None:
                user = self.session.query(
                    f"User where email is '{self.api_user}'"
                ).first()
        if user is None:
            user = self.session.query("User").first()
        if user is None:
            raise RuntimeError("Connected to ftrack but could not resolve a user")
        return {
            "username": user["username"],
            "id": user["id"],
            "server_url": self.session.server_url,
        }


def create_session(settings: Optional[IntegrationSettings] = None) -> "ftrack_api.Session":
    settings = settings or load_settings()
    errors = settings.validate_ftrack()
    if errors:
        raise ValueError("; ".join(errors))
    try:
        import ftrack_api
    except ImportError as exc:
        raise ImportError(
            "ftrack-python-api is required. Install with: pip install ftrack-python-api"
        ) from exc

    ft: FtrackSettings = settings.ftrack
    session = ftrack_api.Session(
        server_url=ft.server_url,
        api_key=ft.api_key,
        api_user=ft.api_user,
        auto_populate=True,
        plugin_paths=[],
    )
    return session


def create_service(settings: Optional[IntegrationSettings] = None) -> FtrackService:
    settings = settings or load_settings()
    session = create_session(settings)
    return FtrackService(session, api_user=settings.ftrack.api_user)
