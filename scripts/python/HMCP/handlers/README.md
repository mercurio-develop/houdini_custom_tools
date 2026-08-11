# HMCP handlers

TCP command handlers invoked from `HMCP/server.py` via `handler_registry.py`.

See **[HMCP_SCOPE.md](../HMCP_SCOPE.md)** and **[docs/HMCP_TOOLS.md](../../../docs/HMCP_TOOLS.md)** for the supported tool list.

## Layout

```
handlers/
  scene/       inspection, geo stats
  usd/         Solaris inspection, materials analysis
  publish/     variant export, texture repair, build prep
  pipeline/    batch LOPs build
  assets/      on-disk USD library discover/import
  graph/       connect, layout, flags
  render/      Karma preview, viewport, PSX karma
  system/      health, example configs
```

## Adding a handler

1. Implement `def my_tool(params: dict) -> dict` in the appropriate subpackage.
2. Register in that subpackage's `COMMANDS` dict.
3. Add schema to `mcp_tool_catalog.py`.
4. Document in `HMCP/HMCP_SCOPE.md` and `docs/HMCP_TOOLS.md`.

Shared logic belongs in `modules/`, not copied across handlers.
