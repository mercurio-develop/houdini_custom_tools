# Houdini MCP Server (HMCP)

Model Context Protocol (MCP) server for integrating **Houdini 22.0** with **Cursor** and other MCP agents. Lets an AI agent inspect scenes, create nodes, execute Python, and run custom pipeline tools like LOPS Asset Builder.

## Overview

Two components:

1. **Houdini Server** (`server.py`) — runs inside Houdini, listens on `localhost:9876`
2. **MCP Bridge** (`houdini_mcp_bridge.py`) — connects MCP agents to Houdini via TCP

## Architecture

```
Cursor IDE (MCP agent)
    ↕ (stdio)
MCP Bridge (houdini_mcp_bridge.py)
    ↕ (TCP socket on localhost:9876)
Houdini MCP Server (server.py running in Houdini)
    ↕
Houdini Python API
```

## Features

- **Scene Management**: Get scene info, list nodes, inspect scene state
- **Node Operations**: Create, modify, delete, and inspect nodes
- **Code Execution**: Run Python code directly in Houdini's environment
- **Asset Scanning**: Scan asset folders for geo/tex layout
- **Pipeline Tools**: LOPS Asset Builder, material validation, custom_tools reload
- **Material Creation**: Create and assign materials to geometry
- **Asset Import**: Download and import assets from URLs

## Installation

### Step 1: Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Step 2: Install MCP dependencies

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
uv sync
python config_helper.py   # prints MCP JSON with H22 paths
```

### Step 3: Configure Cursor (recommended)

Project config template: `$CUSTOM_TOOLS/.cursor/mcp.json.example` (copy to `.cursor/mcp.json`, gitignored). See **[CURSOR_SETUP.md](CURSOR_SETUP.md)** for full steps.

Restart Cursor → **Settings → MCP** → confirm `houdini` is connected when the in-Houdini server is running.

Other MCP-compatible agents can use the same JSON from `config_helper.py` in their MCP settings.

## Usage

### Starting the Houdini server

**Shelf:** Custom Tools → **HMCP** (toggle)

**Python shell:**

```python
from HMCP import start_server
start_server()
```

**Auto-start (optional):** add to `$HOUDINI_USER_PREF_DIR/scripts/456.py`:

```python
try:
    from HMCP import start_server
    start_server()
except Exception as e:
    print(f"HMCP auto-start failed: {e}")
```

### Using with Cursor

1. Start Houdini and toggle **HMCP** on
2. Open workspace: `cursor $CUSTOM_TOOLS/scripts/python`
3. Confirm MCP server `houdini` is green in Cursor settings
4. Try: *"Get Houdini scene info"* or *"Execute: print(hou.fps())"*

### Available MCP tools

| Tool | Description |
|------|-------------|
| `get_scene_info` | Current HIP, nodes, frame, fps |
| `create_node` | Create nodes under a parent |
| `modify_node` | Set node parameters |
| `delete_node` | Delete a node |
| `get_node_info` | Parameters and connections |
| `execute_code` | Run Python with `hou` available |
| `set_material` | Create/assign materials |
| `scan_asset_folder` | Scan geo/tex folder layout |
| `run_lops_asset_builder` | Run LOPS Asset Builder v3 |
| `run_psx_asset_build` | PSX textures + SOP FX + LOPs builder |
| `validate_asset_folder` | Validate materials vs textures |
| `get_stage_summary` | Lightweight /stage inspection |
| `cook_node` | Cook node + prim count |
| `organize_lop_network` | Layout/merge LOP network |
| `reload_custom_tools` | Reload package + Python modules |

### Extended tools (HMCP/handlers/)

See **[HMCP_SCOPE.md](HMCP_SCOPE.md)** for the full supported tool list (~56 total: 15 core + 41 extended).

### Pipeline QA (highlights)

| Tool | Description |
|------|-------------|
| `get_geo_stats` | SOP point/prim counts, bounds, groups |
| `list_material_assignments` | USD material bindings on cooked LOP |
| `get_build_output_paths` | componentoutput disk paths for publish |
| `scan_to_lops_config` | Scan folder → Asset Builder config dict |
| `discover_usd_assets` | Library crawl for primary USD files |
| `search_assets` | Search library by name/path |
| `get_asset_categories` | Group assets by folder/KB3D code |
| `import_asset` | Reference-import scanned geo into /stage |
| `render_karma_preview` | Karma still render (returns image) |
| `apply_psx_karma` | PSX low-res Karma preset |

### USD / Solaris depth

| Tool | Description |
|------|-------------|
| `get_usd_stage_info` | defaultPrim, upAxis, metersPerUnit, prim counts |
| `inspect_usd_attribute` | Read attributes on a prim |
| `get_usd_bounding_box` | World bounds for layout/scale QA |
| `get_usd_layer_stack` | Sublayers, references, payloads, prim stack |
| `list_variant_sets` | Variant sets, names, current selection |
| `set_variant_selection` | Switch variant (session or Set Variant LOP) |
| `create_usd_reference_lop` | Add reference LOP to /stage |
| `set_default_prim` | Set defaultPrim (session or Configure Layer) |
| `validate_usd_file` | On-disk USD validation + usdchecker |

### Publish prep & variants

| Tool | Description |
|------|-------------|
| `extract_usd_cameras` | USD cameras → Solaris camera LOPs |
| `analyze_usd_materials` | Material/texture manifest (no graph) |
| `list_component_variants` | Geo/mtl variant sets on componentoutput |
| `batch_export_variants` | Export geo×mtl USD matrix + manifest |
| `repair_texture_paths` | Fix broken texture paths from folder search |
| `compare_material_manifests` | Folder scan vs USD texture extraction |

Removed experimental publish-chain tools — see **HMCP_SCOPE.md**.

### MCP resources and prompts

The bridge also exposes read-only **resources** (pipeline docs, example configs) and **prompts** (asset build, PSX, debug workflows) without requiring Houdini.

## Example interactions

```
"Create a geometry node in /stage"
"What nodes are in my scene?"
"Scan asset folder at /media/.../my_asset"
"Run LOPS asset builder with config /path/to/config.json"
"Reload custom tools after my code edit"
```

## Troubleshooting

### "Not connected to Houdini"

```python
from HMCP import start_server, is_server_running
print(is_server_running())
start_server()
```

### MCP package not found

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP && uv sync
```

### Port 9876 already in use

```python
from HMCP import stop_server
stop_server()
```

Or use shelf **FORCESTART**. See [CURSOR_SETUP.md](CURSOR_SETUP.md).

### Cursor doesn't see the server

1. Verify `.cursor/mcp.json` paths (use absolute paths; generate via `config_helper.py`)
2. Restart Cursor after config changes
3. Start HMCP in Houdini before first tool call

## Development

### Smoke test

```bash
export PYTHONPATH="$CUSTOM_TOOLS/scripts/python:$PYTHONPATH"
/opt/hfs22.0.368/bin/hython $CUSTOM_TOOLS/scripts/python/HMCP/smoke_test_tcp.py
```

### Adding new tools

**Preferred:** add a handler in `HMCP/handlers/`, register in `handler_registry.py`, add schema in `mcp_tool_catalog.py`. The server auto-wires registry commands; the bridge picks them up from the catalog.

**Legacy / one-offs:** add `handle_*` in `server.py` and register in `self.commands`, then add `types.Tool` + `command_map` entry in `houdini_mcp_bridge.py`.

Document in this README, `PIPELINE_DEV.md`, `docs/HMCP_TOOLS.md`, and the `hmcp-cursor-workflow` skill.

Handlers that call `hou.*` run on Houdini's main thread via `hou.ui.executeDeferred`.

See **[PIPELINE_DEV.md](PIPELINE_DEV.md)** for the agent/human development playbook.

## Security

- Server binds to localhost only
- No authentication (local-only)
- `execute_code` runs arbitrary Python in Houdini — use with care

## Version compatibility

- **Houdini**: 22.0+ (tested with 22.0.368)
- **Python**: Houdini's bundled Python for server; 3.10+ for bridge via `uv`
- **MCP**: 1.4.1+
- **Clients**: Cursor and any MCP-compatible agent

## Shelf tools

- **HMCP** — toggle MCP server (primary)
- **Houdini MCP** — alias to same HMCP toggle (legacy name kept for muscle memory)
- **FORCESTART** — force restart if port is stuck

## Acknowledgments

Based on [capoomgit/houdini-mcp](https://github.com/capoomgit/houdini-mcp), extended for Custom Tools pipeline integration.
