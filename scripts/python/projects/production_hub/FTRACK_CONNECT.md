# ftrack Connect Houdini (0.2.3) vs Production Hub

Local copy: `$CUSTOM_TOOLS/ftrack-connect-houdini-0.2.3`

## What Connect provides

| Feature | Location | Notes |
|---------|----------|--------|
| Launch from ftrack Connect | `hook/ftrack_connect_houdini_hook.py` | Sets `FTRACK_TASKID`, `FTRACK_SHOTID`, `FS`, `FE`, extends `HOUDINI_PATH` / `PYTHONPATH` |
| ftrack menu in Houdini | `resource/houdini_path/MainMenuCommon.xml` | Import, Publish, Asset Manager, Tasks, Info |
| Publish UI | `ui/publisher.py` | Task/shot browser, asset type, comment, thumbnail, status |
| Asset types | `connector/houdiniassets.py` | **scene** (.hip), **geo** (subnet + Alembic), **cam** (baked Alembic) |
| Import / version on nodes | `connector/houdinicon.py` | `ftrack` parm folder on nodes |
| Startup | `resource/houdini_path/python2.7libs/pythonrc.py` | Frame range, registers connector |

Docs: [ftrack-connect-houdini RTD](http://ftrack-connect-houdini.rtd.ftrack.com/en/latest/index.html)

## Compatibility with Houdini 21

Connect **0.2.3** targets:

- Legacy Python **`ftrack`** module (pre–`ftrack-python-api`)
- **Python 2.7** (`pythonrc.py` syntax, `python2.7libs`)
- **ftrack Connect** desktop + `ftrack_connect` package
- **Qt.py / PySide2**

Houdini 21 uses **Python 3.11** and **PySide6**. The bundled `pythonrc` will not load as-is. Options:

1. **Use Connect only to launch** Houdini (hook still runs in Connect’s Python) so env vars are set; use **Production Hub** inside Houdini for publish/query with `ftrack-python-api`.
2. **Keep Connect menus** only if you port the plugin or run a supported Backlight/ftrack Houdini integration for your studio version.
3. **Use Production Hub** for USD + Iconik; use Connect’s **publish patterns** (Alembic, .hip) as a reference for future Hub exporters.

## What Production Hub reuses from Connect

| Connect behavior | Production Hub |
|------------------|----------------|
| `FTRACK_TASKID` / `FS` / `FE` | Task tab banner, **Use FTRACK_TASKID**, auto-bind on open |
| Shot frame range | **Apply frame range** (`integrations/ftrack/connect_context.py` + `ftrack_connect_bridge.py`) |
| Publish comment / thumbnail / task status | Publish tab + `FtrackPublisher` |
| **geo / scene / cam** multi-component | Publish tab → **Connect-style export** + [`connect_exports.py`](../../tools/production_hub/connect_exports.py) |
| Viewport thumbnail | **Viewport JPG** |
| USD + MAM | LOPS CLI + Iconik (not in Connect 0.2.3) |

## Side-by-side workflow (recommended for portfolio)

```text
ftrack Connect  →  Launch Houdini (env vars set)
       ↓
Production Hub  →  Task bound from FTRACK_TASKID
       ↓
Apply frame range  →  Build USD (LOPS v3 CLI)
       ↓
Publish  →  ftrack AssetVersion + Iconik metadata (+ optional thumbnail/status)
```

Legacy **Publish Asset** in the Connect menu remains a reference; the same export logic is ported under **Export & publish Connect components** in Production Hub.

## Connect publish in Production Hub

1. Select ftrack task (or **Use FTRACK_TASKID**).
2. Choose **Geometry**, **Scene**, or **Camera**.
3. Enable components (Houdini subnet, Alembic, optional scene attach).
4. **Export & publish Connect components** — exports to temp files, registers all components on one ftrack `AssetVersion`, optional Iconik link.

```python
from tools.production_hub.connect_exports import ConnectAssetKind, ConnectExportOptions, export_connect_asset
```

Legacy **Publish Asset** menu (Connect 0.2.3) still requires Py2 unless ported separately.

## Environment variables (Connect launch)

| Variable | Meaning |
|----------|---------|
| `FTRACK_TASKID` | Current task UUID |
| `FTRACK_SHOTID` | Parent context id |
| `FS` / `FE` | Frame start / end on parent |
| `FTRACK_SERVER` | Server URL (Connect) |
| `FTRACK_CONNECT_HOUDINI_PLUGINS_PATH` | Override plugin resource path |

Production Hub API credentials remain in `integrations.json` / `FTRACK_API_*` for `ftrack-python-api` (separate from legacy Connect session).
