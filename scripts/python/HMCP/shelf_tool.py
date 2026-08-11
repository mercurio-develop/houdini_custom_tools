"""
Shelf tool script for starting/stopping the Houdini MCP Server

This script can be added to a Houdini shelf button to toggle the server.
"""

import hou
from HMCP import start_server, stop_server, is_server_running


def toggle_mcp_server():
    """Toggle the MCP server on/off from a shelf button."""
    if is_server_running():
        stop_server()
        hou.ui.displayMessage(
            "Houdini MCP Server stopped",
            severity=hou.severityType.Message,
            title="MCP Server"
        )
    else:
        server = start_server()
        if server and server.is_running:
            hou.ui.displayMessage(
                "Houdini MCP Server started on port 9876\n\n"
                "Connect your MCP agent (e.g. Cursor) via the bridge.",
                severity=hou.severityType.Message,
                title="MCP Server"
            )
        else:
            hou.ui.displayMessage(
                "Failed to start Houdini MCP Server",
                severity=hou.severityType.Error,
                title="MCP Server Error"
            )


# Execute when called from shelf
if __name__ == "__main__":
    toggle_mcp_server()
