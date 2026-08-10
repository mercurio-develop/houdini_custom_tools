# HMCP + Cursor Setup (Houdini 22)

Connect Cursor to your live Houdini session via the Model Context Protocol (HMCP).

## Architecture

```
Cursor IDE  →  houdini_mcp_bridge.py (stdio)  →  HMCP/server.py (TCP :9876)  →  hou.*
```

## 1. Install bridge dependencies

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
uv sync
python config_helper.py   # prints MCP JSON with correct paths
```

## 2. Cursor MCP config

Project-scoped config (recommended):

**Template:** `$CUSTOM_TOOLS/.cursor/mcp.json.example`  
**Local (gitignored):** `$CUSTOM_TOOLS/.cursor/mcp.json`

Generate paths automatically:

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
python config_helper.py
```

Alternative: copy the JSON from `config_helper.py` into global `~/.cursor/mcp.json`.

Restart Cursor → **Settings → MCP** → confirm `houdini` shows connected (green) after the in-Houdini server is running.

Optional second server **`production-hub`** is configured in the same `mcp.json` for ftrack/Iconik publish (no Houdini required).

## 3. Start the in-Houdini server

**Shelf (recommended):** Custom Tools → **HMCP** (toggle on/off)

**Python shell:**

```python
from HMCP import start_server, is_server_running
print(is_server_running())
start_server()
```

**Force restart** if port 9876 is stuck: shelf **FORCESTART**

## 4. Smoke test prompts

Try these in Cursor chat after MCP is green:

| Prompt | Expected |
|--------|----------|
| "Get Houdini scene info" | HIP name, node list, frame/fps |
| `execute_code: print(hou.applicationVersionString())` | `22.0.xxx` |
| "Reload custom tools modules" | `reload_custom_tools` success |
| "Scan asset folder at /path/to/asset" | Scanner JSON |
| "Validate materials for /path/to/asset" | Validation report |

## 5. Automated smoke test (terminal)

With Houdini's Python (`hython`):

```bash
export PYTHONPATH="$CUSTOM_TOOLS/scripts/python:$PYTHONPATH"
/opt/hfs22.0.368/bin/hython $CUSTOM_TOOLS/scripts/python/HMCP/smoke_test_tcp.py
```

From HMCP directory, test the bridge while server is running:

```bash
cd $CUSTOM_TOOLS/scripts/python/HMCP
uv run python -c "from houdini_mcp_bridge import HoudiniMCPBridge; b=HoudiniMCPBridge(); b.connect(); print(b.send_command('get_scene_info',{}))"
```

## 6. Custom pipeline tools

These MCP tools wrap your existing custom_tools code:

| Tool | Purpose |
|------|---------|
| `run_lops_asset_builder` | Build from JSON config file or inline config dict |
| `run_psx_asset_build` | PSX preprocessing + LOPs Asset Builder |
| `validate_asset_folder` | Validate materials vs textures |
| `get_stage_summary` | Lightweight /stage LOP summary |
| `cook_node` | Cook node and return prim stats |
| `organize_lop_network` | Organize LOP network layout |
| `reload_custom_tools` | Reload package + Python modules after edits |
| `scan_asset_folder` | Identify main geo, variants, texture folders |

Example:

```
Run LOPS asset builder with config /path/to/asset_config.json
```

## Troubleshooting

### MCP red / "Not connected"

1. Start HMCP in Houdini first (bridge connects lazily on first tool call)
2. Confirm port: `ss -ltn | grep 9876`
3. Run `from HMCP.diagnose_server import diagnose_server; diagnose_server()` in Houdini

### Port 9876 already in use

```python
from HMCP import stop_server
stop_server()
```

Or use shelf **FORCESTART**.

### Code changes not picked up

Ask Cursor to run `reload_custom_tools`, or Alt+click **Reload Packages and Modules** on the shelf.

### Only one MCP bridge

Do not run HMCP alongside another Houdini MCP server on the same port. Use **HMCP** shelf tool (the legacy **Houdini MCP** shelf button now calls the same HMCP toggle).

## Workspace tip

Open the scripts workspace in Cursor:

```bash
cursor $CUSTOM_TOOLS/scripts/python
```

Use the integrated terminal for `git`, `uv`, and `hython`. Use MCP for live Houdini session control.
