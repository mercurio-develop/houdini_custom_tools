# Custom Tools — Architecture

Python pipeline for Houdini 22: USD asset building in LOPs, PSX retro lookdev, project management, and stage utilities. Structured for shelf UI, headless CLI, and HMCP (Cursor MCP) access.

**Agent entry:** Read [`../../AGENTS.md`](../../AGENTS.md) first.  
**Scope docs:** [`SHELF_SCOPE.md`](SHELF_SCOPE.md), [`HMCP/HMCP_SCOPE.md`](HMCP/HMCP_SCOPE.md).

---

## Code layers

```
toolbar/custom_tools.shelf     →  thin entry points only
        ↓
tools/<product>/               →  product logic (builders, UIs, CLI)
        ↓
modules/                       →  shared helpers (no product UI)
        ↓
ui/                            →  PySide6 theme + shared widgets

HMCP/handlers/                 →  thin MCP wrappers → tools/ + modules/
HMCP/server.py                 →  TCP command router (in Houdini)
houdini_mcp_bridge.py          →  stdio MCP bridge (outside Houdini)
```

**Rule:** Shelf and HMCP call into `tools/` or `modules/`. Never duplicate builder logic in handlers or shelf XML.

---

## Directory layout

```
scripts/python/
├── tools/                  # Product packages (lops_asset_builder_v3, psx_tools, …)
├── modules/                # Shared: parms, USD, folder scanner, discovery
├── pipeline/               # Project manager, create project, save tool
├── ui/                     # Qt theme for pipeline dialogs
├── custom_utils.py         # reload_packages, clean_log
├── HMCP/                   # MCP server + bridge + handlers
├── SHELF_SCOPE.md          # Active shelf tools
└── HMCP/HMCP_SCOPE.md      # MCP tool surface + removed tools
```

Repo root (`$CUSTOM_TOOLS`):

```
custom_tools/
├── toolbar/custom_tools.shelf
├── .cursor/                # MCP config, skills, rules
├── docs/                   # Agent governance (AGENTS.md lives at root)
└── config/                 # Optional project configs
```

---

## Products (do not duplicate)

| Product | Location | Entry |
|---------|----------|-------|
| LOPs Asset Builder v3 | `tools/lops_asset_builder_v3/` | Shelf, CLI, HMCP `run_lops_asset_builder` |
| PSX Retro Tools | `tools/psx_tools/` | Shelf, HMCP `run_psx_asset_build` |
| Batch Asset Builder | `tools/lops_asset_builder_v3/batch_asset_builder.py` | Shelf, HMCP `run_batch_lops_build` |
| Project / scene tools | `pipeline/`, `tools/scene_cache_manager.py` | Shelf |
| HMCP | `HMCP/` | Cursor MCP `houdini` server |

Extend the owning product. Do not create parallel builders.

---

## HMCP architecture

```
Cursor Agent
    ↕ stdio (MCP)
houdini_mcp_bridge.py
    ↕ TCP JSON :9876
server.py (inside Houdini)
    ↕ hou.ui.executeDeferred
Houdini main thread
```

### Tool registration

| Tier | Count | Registration |
|------|-------|--------------|
| Core | 15 | Inline in `server.py` + `houdini_mcp_bridge.py` |
| Extended | 41 | `handlers/<domain>/` → `handler_registry.py` + `mcp_tool_catalog.py` |

**Preferred pattern for new tools:** handler → subpackage `COMMANDS` → catalog schema. Avoid adding to the legacy dual-registration path unless necessary.

### Threading

All `hou.*` work runs on Houdini's main thread via `_run_on_main_thread()` / `hou.ui.executeDeferred`. Handlers must not block the socket thread.

### What belongs in HMCP

- Typed tools that map to shelf workflows or documented production steps
- Thin wrappers over `tools/` and `modules/` APIs
- Read-only docs via MCP resources (`mcp_resources.py`)

### What stays outside HMCP

- Studio MAM/tracking (ftrack, Iconik) — removed from repo; future separate service
- Dangerous scene I/O (`load_scene`, `new_scene`) — intentionally removed
- Fragile auto-graph publish chains — use explicit tools instead

---

## Environment

| Variable | Role |
|----------|------|
| `$CUSTOM_TOOLS` | Repo root |
| `$CUSTOM_TOOLS/scripts/python` | Python package root (`PYTHONPATH`) |
| `$JOB`, `$HIP`, `$HB` | Path conventions across tools |

Houdini package loads shelf + PYTHONPATH. HMCP is excluded from automatic module reload — use MCP `reload_custom_tools` after Python edits.

---

## Related docs

| Doc | Purpose |
|-----|---------|
| [`CONVENTIONS.md`](CONVENTIONS.md) | Naming, imports, handler patterns |
| [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md) | Agent-oriented architecture summary |
| [`../../docs/HMCP_TOOLS.md`](../../docs/HMCP_TOOLS.md) | Full MCP tool reference |
| [`HMCP/PIPELINE_DEV.md`](HMCP/PIPELINE_DEV.md) | Edit-test loop for agents and humans |
