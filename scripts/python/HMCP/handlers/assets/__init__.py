"""Asset library discovery handlers."""

from HMCP.handlers.assets.library import (
    discover_usd_assets,
    get_asset_categories,
    import_asset,
    search_assets,
)

COMMANDS = {
    "discover_usd_assets": discover_usd_assets,
    "search_assets": search_assets,
    "get_asset_categories": get_asset_categories,
    "import_asset": import_asset,
}

__all__ = list(COMMANDS.keys())
