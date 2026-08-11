"""
Helper script to generate MCP configuration for Cursor and other MCP agents.

Run this script to get the configuration JSON for your MCP client.
"""

import os
import sys


def get_bridge_path():
    """Get the absolute path to the MCP bridge script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bridge_path = os.path.join(script_dir, 'houdini_mcp_bridge.py')
    return bridge_path


def generate_mcp_config():
    """
    Generate the MCP configuration for Cursor and other MCP agents.

    Returns:
        dict: Configuration to add to MCP client settings
    """
    bridge_path = get_bridge_path()

    config = {
        "mcpServers": {
            "houdini": {
                "command": "uv",
                "args": [
                    "run",
                    "--directory",
                    os.path.dirname(bridge_path),
                    "python",
                    bridge_path
                ],
                "env": {}
            }
        }
    }

    return config


def print_config():
    """Print the configuration for easy copying."""
    import json

    config = generate_mcp_config()

    print("=" * 80)
    print("HOUDINI MCP CONFIGURATION")
    print("=" * 80)
    print("\nAdd this to your MCP client settings:\n")
    print(json.dumps(config, indent=2))
    print("\n" + "=" * 80)
    print("\nCursor (project-scoped):")
    print("  $CUSTOM_TOOLS/.cursor/mcp.json.example")
    print("\nCursor (global):")
    print("  ~/.cursor/mcp.json")
    print("\nOther MCP clients:")
    print("  Paste the JSON above into your agent's MCP settings (any MCP-compatible client).")
    print("=" * 80)


# Backward-compatible alias (legacy name)
generate_claude_code_config = generate_mcp_config


if __name__ == "__main__":
    print_config()
