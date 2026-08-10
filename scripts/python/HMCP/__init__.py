"""
Houdini MCP Server Plugin - Integration for Claude Code via Model Context Protocol

This plugin enables Claude to interact with Houdini through MCP, allowing:
- Scene inspection and node creation
- Python code execution within Houdini
- Rendering and asset management
- Real-time bidirectional communication

Author: Custom Tools
Version: 1.0.0
"""

import hou

# Global reference to server instance
_server_instance = None


def start_server():
    """
    Start the Houdini MCP server.

    Creates a singleton instance of HoudiniMCPServer and stores it in the session.
    If the server is already running, this function does nothing.

    Returns:
        HoudiniMCPServer: The running server instance
    """
    global _server_instance

    # Check if server already exists in session
    if hasattr(hou.session, 'houdini_mcp_server') and hou.session.houdini_mcp_server:
        print("Houdini MCP Server is already running")
        return hou.session.houdini_mcp_server

    # Import and create server
    from HMCP.server import HoudiniMCPServer

    server = HoudiniMCPServer()
    hou.session.houdini_mcp_server = server
    _server_instance = server

    print("Houdini MCP Server started successfully on port 9876")
    return server


def stop_server():
    """
    Stop the Houdini MCP server.

    Cleanly shuts down the server and removes it from the session.
    """
    global _server_instance

    if hasattr(hou.session, 'houdini_mcp_server') and hou.session.houdini_mcp_server:
        hou.session.houdini_mcp_server.shutdown()
        hou.session.houdini_mcp_server = None
        _server_instance = None
        print("Houdini MCP Server stopped")
    else:
        print("No server is currently running")


def get_server():
    """
    Get the current server instance if running.

    Returns:
        HoudiniMCPServer or None: The server instance if running, None otherwise
    """
    if hasattr(hou.session, 'houdini_mcp_server'):
        return hou.session.houdini_mcp_server
    return None


def is_server_running():
    """
    Check if the server is currently running.

    Returns:
        bool: True if server is running, False otherwise
    """
    server = get_server()
    return server is not None and server.is_running


def initialize_plugin():
    """
    Initialize the plugin with default settings.

    This is called automatically when the module is imported.
    Sets up default configuration in hou.session.
    """
    # Set default configurations
    if not hasattr(hou.session, 'houdini_mcp_config'):
        hou.session.houdini_mcp_config = {
            'auto_start': False,  # Don't auto-start by default
            'port': 9876,
            'host': 'localhost',
            'enable_asset_library': False,  # Stub feature
        }

    # Auto-start if configured
    if hou.session.houdini_mcp_config.get('auto_start', False):
        start_server()


# Initialize on import
initialize_plugin()
