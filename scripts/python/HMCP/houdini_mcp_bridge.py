#!/usr/bin/env python3
"""
Houdini MCP Bridge - Connects Claude Code to Houdini via Model Context Protocol

This script acts as a bridge between:
- Claude Code (via MCP stdio protocol)
- Houdini MCP Server (via TCP socket on localhost:9876)

It translates MCP tool calls into Houdini commands and returns results to Claude.
"""

import socket
import json
import sys
import asyncio
from typing import Any

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    from mcp import types
except ImportError:
    print("Error: 'mcp' package not found. Install with: uv add 'mcp[cli]'", file=sys.stderr)
    sys.exit(1)

from mcp_tool_catalog import build_extended_tool_types, extended_command_map
from mcp_resources import (
    get_prompt_messages,
    list_prompt_types,
    list_resource_types,
    read_resource_content,
)


class HoudiniMCPBridge:
    """
    Bridge between MCP protocol (Claude) and Houdini TCP server.

    Maintains a persistent connection to Houdini and translates
    MCP tool calls into Houdini commands.
    """

    def __init__(self, host='localhost', port=9876):
        """
        Initialize the bridge.

        Args:
            host (str): Houdini server host
            port (int): Houdini server port
        """
        self.host = host
        self.port = port
        self.socket = None
        self.request_id = 0

    def connect(self):
        """Establish connection to Houdini server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            print(f"Connected to Houdini MCP Server at {self.host}:{self.port}", file=sys.stderr)
            return True
        except Exception as e:
            print(f"Failed to connect to Houdini: {e}", file=sys.stderr)
            self.socket = None
            return False

    def send_command(self, command: str, params: dict) -> dict:
        """
        Send a command to Houdini and get the response.

        Args:
            command (str): Command name
            params (dict): Command parameters

        Returns:
            dict: Response from Houdini
        """
        if not self.socket:
            if not self.connect():
                return {'status': 'error', 'error': 'Not connected to Houdini'}

        # Prepare request
        self.request_id += 1
        request = {
            'id': self.request_id,
            'command': command,
            'params': params
        }

        try:
            # Send request
            message = json.dumps(request) + '\n'
            self.socket.sendall(message.encode('utf-8'))

            # Receive response
            buffer = ""
            while True:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    return {'status': 'error', 'error': 'Connection closed by Houdini'}

                buffer += data
                if '\n' in buffer:
                    response_str, buffer = buffer.split('\n', 1)
                    response = json.loads(response_str)
                    return response

        except Exception as e:
            print(f"Communication error: {e}", file=sys.stderr)
            self.socket = None
            return {'status': 'error', 'error': str(e)}

    def close(self):
        """Close connection to Houdini."""
        if self.socket:
            self.socket.close()
            self.socket = None


# Global bridge instance
bridge = HoudiniMCPBridge()

# Create MCP server
mcp_server = Server("houdini-mcp")


@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List all available tools for Claude to use.

    Returns:
        list[types.Tool]: Available MCP tools
    """
    tools = [
        types.Tool(
            name="get_scene_info",
            description="Get Houdini scene summary. By default returns HIP metadata and selection only; set include_all_nodes=true or context_path to list nodes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_all_nodes": {
                        "type": "boolean",
                        "description": "List nodes (default false — avoids dumping entire HIP)",
                        "default": False,
                    },
                    "context_path": {
                        "type": "string",
                        "description": "Limit node listing to subtree (e.g. /stage, /obj)",
                    },
                    "node_type": {
                        "type": "string",
                        "description": "Filter listed nodes by type name",
                    },
                    "max_nodes": {
                        "type": "integer",
                        "description": "Max nodes to return when listing",
                        "default": 200,
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get_stage_summary",
            description="Lightweight /stage LOP summary: children, component outputs, selection",
            inputSchema={
                "type": "object",
                "properties": {
                    "stage_path": {
                        "type": "string",
                        "description": "Path to stage LOP network",
                        "default": "/stage",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="create_node",
            description="Create a new node in Houdini",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_path": {
                        "type": "string",
                        "description": "Path to parent node (e.g., /obj, /stage)",
                        "default": "/obj"
                    },
                    "node_type": {
                        "type": "string",
                        "description": "Type of node to create (e.g., geo, cam, light)"
                    },
                    "node_name": {
                        "type": "string",
                        "description": "Optional name for the node"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Optional dictionary of parameter names and values"
                    }
                },
                "required": ["node_type"]
            }
        ),
        types.Tool(
            name="modify_node",
            description="Modify parameters of an existing node",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_path": {
                        "type": "string",
                        "description": "Full path to the node (e.g., /obj/geo1)"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Dictionary of parameter names and values to set"
                    }
                },
                "required": ["node_path", "parameters"]
            }
        ),
        types.Tool(
            name="delete_node",
            description="Delete a node from the scene",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_path": {
                        "type": "string",
                        "description": "Full path to the node to delete"
                    }
                },
                "required": ["node_path"]
            }
        ),
        types.Tool(
            name="get_node_info",
            description="Get detailed information about a specific node including parameters and connections",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_path": {
                        "type": "string",
                        "description": "Full path to the node"
                    }
                },
                "required": ["node_path"]
            }
        ),
        types.Tool(
            name="execute_code",
            description="Execute Python code within Houdini's environment. Use 'hou' module for Houdini operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code to execute (hou module is available)"
                    },
                    "return_expr": {
                        "type": "string",
                        "description": "Optional expression to eval and return after code runs",
                    },
                },
                "required": ["code"]
            }
        ),
        types.Tool(
            name="set_material",
            description="Create and assign a material to geometry",
            inputSchema={
                "type": "object",
                "properties": {
                    "geo_path": {
                        "type": "string",
                        "description": "Path to geometry node"
                    },
                    "material_name": {
                        "type": "string",
                        "description": "Name for the material"
                    },
                    "diffuse_color": {
                        "type": "array",
                        "description": "RGB color values [r, g, b]",
                        "items": {"type": "number"}
                    }
                },
                "required": ["geo_path", "material_name"]
            }
        ),
        types.Tool(
            name="render_single_view",
            description="Render a single view from Houdini (placeholder implementation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "camera": {
                        "type": "string",
                        "description": "Camera path or 'default'"
                    },
                    "resolution": {
                        "type": "array",
                        "description": "Resolution [width, height]",
                        "items": {"type": "integer"}
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="import_url",
            description="Download and import a model from URL (supports USD, GLTF)",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to download (supports .zip files)"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="scan_asset_folder",
            description="Scan an asset folder and automatically identify main assets, variants, and texture folders prioritized by resolution (4k > 2k > 1k)",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Path to the root asset folder to scan (supports Houdini environment variables like $HIP, $JOB)"
                    },
                    "geo_subfolder": {
                        "type": "string",
                        "description": "Name of geometry subfolder (default: 'geo')",
                        "default": "geo"
                    },
                    "tex_subfolder": {
                        "type": "string",
                        "description": "Name of texture subfolder (default: 'tex')",
                        "default": "tex"
                    }
                },
                "required": ["folder_path"]
            }
        ),
        types.Tool(
            name="run_lops_asset_builder",
            description="Run LOPS Asset Builder v3 from a JSON config file or inline config dict",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_filepath": {
                        "type": "string",
                        "description": "Path to asset builder JSON config file"
                    },
                    "config": {
                        "type": "object",
                        "description": "Inline asset builder config dict (alternative to config_filepath)"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose build output",
                        "default": True
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="validate_asset_folder",
            description="Validate geometry materials against available textures for an asset folder or explicit paths",
            inputSchema={
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "Root asset folder to scan and validate (supports $HIP, $JOB, etc.)"
                    },
                    "main_asset_file_path": {
                        "type": "string",
                        "description": "Main geometry file (use with folder_textures instead of folder_path)"
                    },
                    "folder_textures": {
                        "type": "string",
                        "description": "Main texture folder path"
                    },
                    "asset_variants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional geometry variant file paths"
                    },
                    "mtl_variants": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional texture variant folder paths"
                    },
                    "geo_subfolder": {
                        "type": "string",
                        "description": "Geometry subfolder when using folder_path",
                        "default": "geo"
                    },
                    "tex_subfolder": {
                        "type": "string",
                        "description": "Texture subfolder when using folder_path",
                        "default": "tex"
                    },
                    "lowercase": {
                        "type": "boolean",
                        "description": "Lowercase material names during validation",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="run_psx_asset_build",
            description="Run PSX retro preprocessing (dither textures, SOP effects) plus LOPs Asset Builder",
            inputSchema={
                "type": "object",
                "properties": {
                    "main_asset_file_path": {"type": "string"},
                    "folder_textures": {"type": "string"},
                    "asset_name": {"type": "string"},
                    "run_lops_asset_builder": {"type": "boolean", "default": True},
                    "stage_context_path": {"type": "string", "default": "/stage"},
                    "psx": {
                        "type": "object",
                        "description": "PSXAssetConfig fields: decimate_ratio, triangulate, process_textures, palette_size, etc.",
                    },
                },
                "required": ["main_asset_file_path", "folder_textures"],
            },
        ),
        types.Tool(
            name="cook_node",
            description="Cook a node and return stage stats (prim count for LOPs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "node_path": {"type": "string", "description": "Full node path"},
                    "force": {"type": "boolean", "default": True},
                },
                "required": ["node_path"],
            },
        ),
        types.Tool(
            name="organize_lop_network",
            description="Organize the current LOP/stage network (layout, merge outputs)",
            inputSchema={
                "type": "object",
                "properties": {
                    "merge": {"type": "boolean", "default": True},
                    "layout": {"type": "boolean", "default": True},
                    "boxes": {"type": "boolean", "default": False},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="reload_custom_tools",
            description="Reload the custom_tools Houdini package and Python modules after code edits",
            inputSchema={
                "type": "object",
                "properties": {
                    "reload_modules": {
                        "type": "boolean",
                        "description": "Also reload Python modules (equivalent to Alt+click on Reload Packages shelf)",
                        "default": True
                    }
                },
                "required": []
            }
        ),
    ]
    tools.extend(build_extended_tool_types())
    return tools


@mcp_server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    return list_resource_types()


@mcp_server.read_resource()
async def handle_read_resource(uri: str) -> types.ReadResourceResult:
    contents = read_resource_content(uri)
    return types.ReadResourceResult(contents=[contents])


@mcp_server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    return list_prompt_types()


@mcp_server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict | None = None) -> types.GetPromptResult:
    messages = get_prompt_messages(name)
    return types.GetPromptResult(messages=messages)


@mcp_server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests from Claude.

    Args:
        name (str): Tool name
        arguments (dict): Tool arguments

    Returns:
        list: Tool execution results
    """
    try:
        # Map MCP tool names to Houdini commands
        command_map = {
            'get_scene_info': 'get_scene_info',
            'get_stage_summary': 'get_stage_summary',
            'create_node': 'create_node',
            'modify_node': 'modify_node',
            'delete_node': 'delete_node',
            'get_node_info': 'get_node_info',
            'execute_code': 'execute_code',
            'set_material': 'set_material',
            'render_single_view': 'render_single_view',
            'import_url': 'import_opus_url',
            'scan_asset_folder': 'scan_asset_folder',
            'run_lops_asset_builder': 'run_lops_asset_builder',
            'run_psx_asset_build': 'run_psx_asset_build',
            'validate_asset_folder': 'validate_asset_folder',
            'cook_node': 'cook_node',
            'organize_lop_network': 'organize_lop_network',
            'reload_custom_tools': 'reload_custom_tools',
        }
        command_map.update(extended_command_map())

        if name not in command_map:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

        # Send command to Houdini
        command = command_map[name]
        response = bridge.send_command(command, arguments)

        # Format response
        if response.get('status') == 'error':
            error_msg = response.get('error', 'Unknown error')
            return [types.TextContent(
                type="text",
                text=f"Error: {error_msg}"
            )]

        # Handle image responses (render_single_view, capture_viewport, etc.)
        result = response.get('result', {})
        if isinstance(result, dict) and result.get('image'):
            fmt = (result.get('format') or 'png').lower()
            mime = 'image/jpeg' if fmt in ('jpg', 'jpeg') else 'image/png'
            caption_parts = []
            if result.get('output_path'):
                caption_parts.append(f"Saved to: {result['output_path']}")
            if result.get('width') and result.get('height'):
                caption_parts.append(f"Size: {result['width']}x{result['height']}")
            if result.get('frame') is not None:
                caption_parts.append(f"Frame: {result['frame']}")
            return [
                types.ImageContent(type="image", data=result['image'], mimeType=mime),
                types.TextContent(
                    type="text",
                    text="\n".join(caption_parts) or "Image captured from Houdini",
                ),
            ]

        # Standard text response
        result_text = json.dumps(result, indent=2)

        return [types.TextContent(
            type="text",
            text=result_text
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"Bridge error: {str(e)}"
        )]


async def main():
    """Main entry point for the MCP server."""
    print("Starting Houdini MCP Bridge...", file=sys.stderr)
    print("Make sure Houdini MCP Server is running on localhost:9876", file=sys.stderr)

    # Try to connect to Houdini
    if bridge.connect():
        print("Successfully connected to Houdini!", file=sys.stderr)
    else:
        print("Warning: Not connected to Houdini. Will retry on first command.", file=sys.stderr)

    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="houdini-mcp",
                server_version="1.1.0",
                capabilities=mcp_server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
