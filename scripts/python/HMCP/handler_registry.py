"""Register HMCP handler callables for server command dispatch."""

from HMCP.handlers.assets import COMMANDS as ASSET_COMMANDS
from HMCP.handlers.graph import COMMANDS as GRAPH_COMMANDS
from HMCP.handlers.pipeline import COMMANDS as PIPELINE_COMMANDS
from HMCP.handlers.publish import COMMANDS as PUBLISH_COMMANDS
from HMCP.handlers.render import COMMANDS as RENDER_COMMANDS
from HMCP.handlers.scene import COMMANDS as SCENE_COMMANDS
from HMCP.handlers.system import COMMANDS as SYSTEM_COMMANDS
from HMCP.handlers.usd import COMMANDS as USD_COMMANDS

HANDLER_REGISTRY = {
    **SCENE_COMMANDS,
    **USD_COMMANDS,
    **PUBLISH_COMMANDS,
    **PIPELINE_COMMANDS,
    **ASSET_COMMANDS,
    **GRAPH_COMMANDS,
    **RENDER_COMMANDS,
    **SYSTEM_COMMANDS,
}
