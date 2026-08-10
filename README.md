# Houdini Custom Tools (`$CUSTOM_TOOLS`)

Pipeline tools for **Houdini 21/22**: LOPs USD asset building, KB3D-style libraries, Production Hub (ftrack · Iconik), **HMCP** (live Houdini MCP for Cursor), and stage utilities.

**Python docs:** [`scripts/python/README.md`](scripts/python/README.md)  
**Architecture:** [`scripts/python/ARCHITECTURE.md`](scripts/python/ARCHITECTURE.md)  
**Conventions:** [`scripts/python/CONVENTIONS.md`](scripts/python/CONVENTIONS.md)

---

## Quick install

### 1. Clone into Houdini user preferences

```bash
git clone git@github.com:mercurio-develop/houdini_custom_tools.git \
  "$HOUDINI_USER_PREF_DIR/custom_tools"
```

Or clone anywhere and symlink that path to `$HOUDINI_USER_PREF_DIR/custom_tools`.

### 2. Enable the Houdini package

```bash
cp packages/custom_tools.json.example \
  "$HOUDINI_USER_PREF_DIR/packages/custom_tools.json"
```

This sets `$CUSTOM_TOOLS` and adds the repo root to `$HOUDINI_PATH` (toolbar, scripts, etc.).

Restart Houdini. Confirm in a Python shell:

```python
import os; print(os.environ["CUSTOM_TOOLS"])
import sys; print(any("custom_tools/scripts/python" in p for p in sys.path))
```

### 3. Shelf

The **Custom Tools** shelf is included at [`toolbar/custom_tools.shelf`](toolbar/custom_tools.shelf). It loads automatically when `$CUSTOM_TOOLS` is on `$HOUDINI_PATH`.

### 4. Studio config (optional)

```bash
cp config/integrations.example.json config/integrations.json   # ftrack + Iconik
cp config/projects_config.example.json config/projects_config.json
```

Edit paths and credentials. These files are **gitignored** — never commit secrets.

### 5. Cursor + HMCP (optional)

```bash
cd scripts/python/HMCP && uv sync
python config_helper.py   # prints MCP JSON with your paths
cp .cursor/mcp.json.example .cursor/mcp.json   # from repo root; edit paths
# Edit paths, or paste output from config_helper.py
```

Toggle **HMCP** on the Custom Tools shelf in Houdini, then connect Cursor MCP.

See [`scripts/python/HMCP/CURSOR_SETUP.md`](scripts/python/HMCP/CURSOR_SETUP.md).

---

## Repository layout

```
custom_tools/                     ← $CUSTOM_TOOLS (this repo)
├── packages/                     Houdini package template
├── toolbar/                      Custom Tools shelf
├── config/                       Example JSON (secrets gitignored)
├── .cursor/                      MCP example + agent skills
├── scripts/
│   ├── python/                   Main Python package root
│   │   ├── tools/                LOPs builder, kb3d, material_tools, psx_tools, …
│   │   ├── HMCP/                 Houdini MCP server + bridge
│   │   ├── integrations/         ftrack, Iconik, publish workflow
│   │   ├── modules/              Shared helpers
│   │   └── projects/production_hub/
│   └── VEX/                      Snippets
└── LICENSE
```

---

## Products

| Product | Entry |
|---------|--------|
| **LOPs Asset Builder v3** | Shelf → Batch Asset Builder / Lops Asset Builder |
| **USD library toolkit** | `tools/kb3d_tools/`, `tools/asset_library_builder/` |
| **Production Hub** | `tools/production_hub/` + [`projects/production_hub/README.md`](scripts/python/projects/production_hub/README.md) |
| **HMCP** | Shelf → HMCP toggle; 46+ MCP tools for agents |
| **PSX retro tools** | Shelf → PSX Tools |
| **MaterialX from textures** | `from tools.material_tools import MtlxMaterial` |

---

## Development

```python
# Inside Houdini — reload changed modules
from custom_utils import reload_packages
reload_packages({"altclick": True})
```

```bash
# Lint (optional)
cd scripts/python && uv run ruff check HMCP/handlers/ modules/
```

Open in Cursor: `cursor /path/to/custom_tools` (skills in `.cursor/skills/`).

---

## What not to commit

- `config/integrations.json`, `config/projects_config.json` — local studio data
- `.cursor/mcp.json` — machine-specific paths (use `.cursor/mcp.json.example`)
- `scripts/python/tools/jltools_decompiled/` — proprietary third-party bytecode

---

## License

MIT — see [LICENSE](LICENSE).
