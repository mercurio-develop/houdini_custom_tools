"""Render and viewport handlers."""

from HMCP.handlers.render.karma import apply_psx_karma, render_karma_preview
from HMCP.handlers.render.viewport import capture_viewport, cook_render_node, set_frame_range

COMMANDS = {
    "render_karma_preview": render_karma_preview,
    "apply_psx_karma": apply_psx_karma,
    "capture_viewport": capture_viewport,
    "cook_render_node": cook_render_node,
    "set_frame_range": set_frame_range,
}

__all__ = list(COMMANDS.keys())
