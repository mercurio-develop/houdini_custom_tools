"""Scene and SOP inspection handlers."""

from HMCP.handlers.scene.geo import get_geo_stats
from HMCP.handlers.scene.inspection import (
    get_cook_chain,
    get_node_errors,
    get_parameter_schema,
)

COMMANDS = {
    "get_node_errors": get_node_errors,
    "get_cook_chain": get_cook_chain,
    "get_parameter_schema": get_parameter_schema,
    "get_geo_stats": get_geo_stats,
}

__all__ = list(COMMANDS.keys())
