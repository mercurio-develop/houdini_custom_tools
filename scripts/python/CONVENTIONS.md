# Custom Tools — Conventions

Coding standards for `scripts/python/`. Cursor rule: [`.cursor/rules/houdini-python-tools.mdc`](../../.cursor/rules/houdini-python-tools.mdc). HMCP handlers: [`.cursor/rules/hmcp-handlers.mdc`](../../.cursor/rules/hmcp-handlers.mdc).

---

## Structure

- Tool logic lives under `tools/<package>/`, not in shelf XML.
- Shared helpers go in `modules/`, not duplicated across tools or handlers.
- Config uses `@dataclass` (see `AssetBuilderConfig`, `PSXAssetConfig`).
- Long builds use `ProgressLike` / `ProgressReporter`; log via `progress.log()`.
- Node names: use `_sanitize()` from `modules.misc_utils`.
- Prefer extending existing products over parallel builders (see `ARCHITECTURE.md`).

---

## Imports

```python
from tools.lops_asset_builder_v3.asset_builder_config import AssetBuilderConfig
from modules.houdini_node_utils import set_parm
from modules.misc_utils import _sanitize
```

- Do not import `hou`-dependent UI at module level without guards.
- HMCP handlers import from `tools/` and `modules/` — never duplicate logic inline.

---

## Houdini runtime

- Avoid side effects at import time (no node creation, no UI on import).
- Guard UI entry points: check selection/context; use `hou.ui.displayMessage` for errors.
- After editing Python in a live session: `custom_utils.reload_packages({"altclick": True})` or HMCP `reload_custom_tools`.
- HMCP package is excluded from auto-reload — always call `reload_custom_tools` explicitly after handler edits.

---

## Shelf sync

- Every new shelf tool must call a function in `tools/`, not inline logic in `custom_tools.shelf`.
- Use `importlib.reload(module)` in shelf scripts for dev iteration.
- Document new shelf tools in `SHELF_SCOPE.md`.

---

## HMCP handlers

1. Signature: `def my_tool(params: dict) -> dict`
2. Validate params early; return structured dicts (not bare strings).
3. Register in subpackage `COMMANDS` dict (see `HMCP/handlers/README.md`).
4. Add JSON schema to `HMCP/mcp_tool_catalog.py`.
5. Document in `HMCP/HMCP_SCOPE.md` and `docs/HMCP_TOOLS.md`.
6. Shared logic stays in `modules/` or `tools/` — handlers are thin wrappers.

---

## Testing

| Layer | Method |
|-------|--------|
| Hou-free modules | `python3 -m py_compile path/to/module.py` |
| Dither/texture utils | Direct import of pure modules (no `hou`) |
| HMCP TCP | `hython HMCP/smoke_test_tcp.py` (server running) |
| Live session | HMCP tools via Cursor after `reload_custom_tools` |

---

## Scope and diffs

- Minimal diffs; match surrounding naming and patterns.
- Archive superseded tools to `tools/_archive/` with a short README.
- One HMCP tool = one pipeline action — see `HMCP/HMCP_SCOPE.md`.
