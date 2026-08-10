# Code conventions — `scripts/python`

Shared rules for layout, naming, and where new code belongs.

## Directory roles

| Path | Purpose | Runs in Houdini? |
|------|---------|------------------|
| `tools/<product>/` | End-user features (UI, CLI, builders) | Yes |
| `modules/` | Reusable helpers (no shelf entry) | Usually yes |
| `integrations/` | ftrack, Iconik, headless HTTP | No `hou` |
| `HMCP/` | MCP TCP server + bridge | Server in Houdini |
| `pipeline/` | Project/save/USD project tools | Yes |
| `utils/` | Dev scripts, one-offs | Varies |

**Rule:** If two products need it, move it to `modules/` or `integrations/`.

## Naming

| Item | Convention | Example |
|------|------------|---------|
| Packages / folders | `snake_case` | `lops_asset_builder_v3` |
| Python modules | `snake_case.py` | `material_validator.py` |
| Classes | `PascalCase` | `AssetBuilderConfig` |
| Functions | `snake_case` | `run_asset_build` |
| HMCP TCP commands | `snake_case` | `batch_export_variants` |
| MCP tool names | same as TCP command | 1:1 with `handler_registry` |
| Config JSON keys | `snake_case` | `folder_textures` |
| Houdini node names | sanitized, no spaces | `_sanitize()` from `misc_utils` |

## HMCP handler pattern

1. **Logic** in `HMCP/handlers/<domain>/<module>.py` — thin wrappers only when possible.
2. **Shared logic** in `modules/` (e.g. `usd_solaris_utils`, `lop_helpers`).
3. **Register** in the subpackage `__init__.py` `COMMANDS` dict (merged by `handler_registry.py`).
4. **Schema** in `HMCP/mcp_tool_catalog.py` (bridge picks up automatically).
5. **Never** duplicate LOPs Asset Builder logic — call `tools/lops_asset_builder_v3/*`.

Handler signature: `def tool_name(params: dict) -> dict`

Handlers must raise `ValueError` for bad input; server wraps other exceptions.

## Product boundaries

- **Build USD out:** `tools/lops_asset_builder_v3/`, `tools/psx_tools/`
- **Library on disk:** `tools/asset_library_builder/`, `tools/kb3d_tools/`
- **Publish / track:** `integrations/`, `tools/production_hub/`
- **USD inspect/import:** `modules/usd_solaris_utils.py`, `modules/usd_material_naming.py`
- **Agent API:** `HMCP/handlers/*`

Do not add a second asset builder. Extend v3 or add HMCP handlers.

## Imports

Prefer absolute imports from package root (`tools.`, `modules.`, `HMCP.`):

```python
from modules.lop_helpers import find_component_output
from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_asset
```

Avoid handler-to-handler imports; use `modules/` instead.

## USD / texture channel keys

Use the shared vocabulary in `modules/usd_solaris_utils.TEXTURE_CHANNEL_ALIASES`:

`base_color`, `metallic`, `roughness`, `normal`, `specular`, `opacity`, `displacement`, `emission`

Validators, importers, and repair tools should use the same keys.

## Documentation

| Doc | When to update |
|-----|----------------|
| `ARCHITECTURE.md` | New product or major seam |
| `CONVENTIONS.md` | Naming or layout rules change |
| `HMCP/README.md` | New MCP tools |
| `HMCP/handlers/README.md` | New handler module |
| `.cursor/skills/*` | Agent workflow changes |

## Gitignore

- `tools/jltools_decompiled/` — local learning only
- `integrations.json`, `.env*` — secrets
- `docs/` — session notes (optional)

## Testing

- HMCP: `HMCP/smoke_test_tcp.py` via hython (server running)
- Headless: `python3 -m py_compile` on modules without `hou`
- No `hou` in `integrations/` CI paths
