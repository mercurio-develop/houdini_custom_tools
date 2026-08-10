"""System health and reference handlers."""

from HMCP.handlers.system.health import get_asset_builder_example, get_server_health

COMMANDS = {
    "get_server_health": get_server_health,
    "get_asset_builder_example": get_asset_builder_example,
}

__all__ = list(COMMANDS.keys())
