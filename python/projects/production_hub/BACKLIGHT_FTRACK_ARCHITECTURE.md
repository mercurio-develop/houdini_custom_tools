# Backlight / ftrack — conventions and architecture (study guide)

**Backlight** owns **ftrack Studio**, **cineSync**, and **ftrack Review**. Pipeline work is documented on the **[ftrack Developer Hub](https://developer.ftrack.com/)** (Integrating pipelines, Connect, hooks, locations). This note ties official patterns to code you have locally and to **Production Hub**.

---

## 1. Product stack (what “Backlight pipeline” usually means)

| Layer | Role |
|-------|------|
| **ftrack Studio** | System of record: projects, hierarchy (workflows/entities), **tasks**, **assets**, **asset versions**, components, statuses, reviews |
| **ftrack Connect** | Desktop app: launch DCCs, discover plugins, run **hooks** (actions, locations, launch) |
| **Connect Pipeline Framework** (newer) | Modular Py3 framework: definitions, publish/load, DCC layer — see [Connect Pipeline overview](https://ftrack-connect-pipeline.readthedocs.io/en/latest/introduction/overview.html) |
| **ftrack Python API** | `ftrack_api.Session` — queries, create, commit, **locations**, **structure**, events |
| **DCC integration** | Houdini/Maya/Nuke plugin: context from launch, publish UI, import/version on nodes |

Your portfolio path: **Connect for launch context** + **`ftrack-python-api` in Houdini** (Production Hub) + **Iconik** for MAM — not the legacy Py2 connector alone.

---

## 2. Core ftrack entities (publish mental model)

From [Publishing (ftrack Studio help)](https://help.ftrack-studio.backlight.co/hc/en-us/articles/13129940761495-Publishing):

```text
Project → … → Shot / Asset build (context)
                    └── Task  ← work assignment (version links here)
                    └── Asset  ← logical publish group (name + type), parent = context NOT task
                          └── AssetVersion  ← v001, v002…
                                └── Component(s)  ← files (main, thumbnail, …)
                                      └── ComponentLocation  ← path per Location
```

**Conventions:**

- **Asset** parents to **shot/context**; **AssetVersion** associates with **Task**.
- **Components** hold files; **locations** map components to disk paths via **structure** plugins.
- Naming on disk often follows: `project/.../context.../asset_name/v003/file.ext` ([StandardStructure](https://ftrack-python-api.readthedocs.io/en/stable/api_reference/structure/standard.html)).

**Production Hub mapping:** [`FtrackPublisher.publish_usd`](../../integrations/ftrack/publish.py) creates Asset → AssetVersion → Component (`main`) → ComponentLocation with your sandbox location — same entity model, simplified (single USD path, no DCC export step).

---

## 3. Connect plugin architecture (official)

From [Developing plugins](https://developer.ftrack.com/integrating-pipelines/connect/developing_plugins/index.html):

```text
my_studio_plugin/
  hook/
    action/
      my_action.py      # register(session) → actions
    location/
      custom_location.py
  resource/
    shared_modules/     # append to sys.path from hooks
```

**Rules:**

1. Every hook exposes **`register(session, **kw)`** and guards with `isinstance(session, ftrack_api.Session)`.
2. Split **actions** vs **locations** so launch can add only `hook/location/` to `FTRACK_EVENT_PLUGIN_PATH`.
3. Shared code lives under **`resource/`**, not duplicated per hook.

**Launch hook** ([application launch](https://developer.ftrack.com/integrating-pipelines/guides/customise-connect/hooks/)): sets env vars when opening a DCC — e.g. `FTRACK_TASKID`, frame range.

**Local reference:** [`ftrack-connect-houdini/resource/hook/discover_integration.py`](file:///home/tushita/dev/ftrack-connect-houdini/resource/hook/discover_integration.py) — `on_launch_houdini_integration` sets `FTRACK_TASKID`, `FTRACK_SHOTID`, `FS`, `FE`, `PYTHONPATH`, `HOUDINI_PATH`.

---

## 4. Legacy Houdini integration layout (Connect 1.x style)

Repo: [`~/dev/ftrack-connect-houdini`](file:///home/tushita/dev/ftrack-connect-houdini) (EOL, Py2, **not** Backlight-maintained for Houdini 21).

| Piece | Path | Pattern |
|-------|------|---------|
| Connect discovery | `resource/hook/discover_integration.py` | `ftrack_api` session + launch env |
| DCC menu | `resource/houdini_path/MainMenuCommon.xml` | Shelf/menu → `FtrackDialogs(...)` |
| Startup | `resource/houdini_path/python2.7libs/pythonrc.py` | Frame range, register connector |
| **Connector** | `connector/houdinicon.py` | Subclass legacy `Connector`: scene path, selection, **publishAsset** dispatch |
| **Asset types** | `connector/houdiniassets.py` | One class per type (`scene`, `geo`, `cam`): **importAsset**, **publishAsset**, **changeVersion** |
| **UI** | `ui/publisher.py` | ContextSelector → asset type/name → comment/thumbnail/status → publish |

**Legacy publish sequence** (still the right *concept*):

1. Resolve **task** + **shot** from UI / env.
2. **prePublish** validation.
3. `createAsset` / `createVersion` on server.
4. DCC **exports** geometry/scene → **components**.
5. **publishAssetFiles** registers paths on locations.
6. Optional: task **status**, version **thumbnail**.

**Production Hub** skips step 4 for USD (file already exists) but keeps 1–3 and 6; see [FTRACK_CONNECT.md](FTRACK_CONNECT.md).

**Node convention (legacy):** nodes with an **`ftrack` parm folder** and `componentId` for import/version tracking ([`houdinicon.getAssets`](file:///home/tushita/dev/ftrack-connect-houdini/source/ftrack_connect_houdini/connector/houdinicon.py)). USD/LOPS pipelines often use prim paths or sidecar JSON instead — your `$JOB/ftrack_task_id.json` is a lighter pattern.

---

## 5. Connect Pipeline Framework (modern target)

From [Framework overview](https://ftrack-connect-pipeline.readthedocs.io/en/latest/introduction/overview.html):

- **Modular layers:** core pipeline → **definitions** (schemas) → UI → DCC integration.
- **Central definition repository** — avoid copy-paste across Maya/Nuke/Houdini.
- **Py3**, host/UI abstraction (headless + MCP-friendly).
- Key entities: **Context**, **AssetVersion**, **Component** (same as above).

If Backlight ships or your studio adopts **Connect 2 + Framework** for Houdini, your Production Hub split (**integrations/** without `hou` + thin DCC UI) matches their direction.

---

## 6. ftrack-recipes (Backlight-maintained examples)

Repo: [`~/dev/ftrack-recipes-main`](file:///home/tushita/dev/ftrack-recipes-main) — copyright **Backlight** / ftrack on newer files.

| Category | Example | Convention to notice |
|----------|---------|----------------------|
| **Actions** | `clone-review-with-latest-0.0.0` | Subclass **`BaseAction`**, `identifier = "com.ftrack.recipes...."`, `discover()` + `launch()`, `register(session)` |
| **Events** | `cascade-status-changes`, `customise-structure` | `register(session)` → subscribe to event hub |
| **Locations** | `per-project-location`, `customise-structure` | Accessor + **Structure** plugin, `get_resource_identifier` |
| **Tools** | `duplicate_structure` | Standalone `Session(auto_populate=False)` for bulk server ops |
| **Connect hooks** | `encode-image-sequence`, `make-non-encoding-web-playable` | Publish-time Connect hooks |

**Action ID convention:** reverse-DNS style `com.ftrack.recipes.clone_review`.

**Query convention:** string queries, e.g. `AssetVersion where asset_id is … and is_latest_version is True` (see clone_review).

**Performance convention:** `Session(auto_populate=False)` when duplicating large trees ([duplicate_structure](file:///home/tushita/dev/ftrack-recipes-main/python/tools/duplicate_structure/duplicate_structure.py)).

---

## 7. How Production Hub aligns (your code)

```text
                    ┌─────────────────────────────────────┐
                    │  ftrack Studio (Backlight cloud/on-prem) │
                    └─────────────────────────────────────┘
                           ▲                    ▲
                           │ ftrack_api         │ metadata
              ┌────────────┴────────────┐      │
              │  integrations/ftrack/   │      │  integrations/iconik/
              │  queries, publish,      │      │
              │  connect_context        │      │
              └────────────┬────────────┘      │
                           │                  │
         ┌─────────────────┼──────────────────┼──────────────┐
         │                 │                  │              │
    MCP / FastAPI    Production Hub UI    Next dashboard   (future Connect actions)
    (headless)       (Houdini PySide6)    (read/publish API)
```

| Backlight/ftrack convention | Your module |
|-----------------------------|-------------|
| Session + env credentials | [`integrations/ftrack/session.py`](../../integrations/ftrack/session.py), [`settings.py`](../../integrations/settings.py) |
| Launch context `FTRACK_TASKID` | [`connect_context.py`](../../integrations/ftrack/connect_context.py) |
| Publish AssetVersion + components | [`publish.py`](../../integrations/ftrack/publish.py) |
| Orchestration (ftrack + MAM) | [`publish_usd_deliverable.py`](../../integrations/workflows/publish_usd_deliverable.py) |
| DCC UI (thin) | [`production_hub_ui.py`](../../tools/production_hub/production_hub_ui.py) |
| Connect artist behaviors (timeline, thumb) | [`ftrack_connect_bridge.py`](../../tools/production_hub/ftrack_connect_bridge.py) |
| Headless / agents | [`mcp/production_hub_server.py`](../../mcp/production_hub_server.py) |

**Gap vs full studio:** custom **location/structure** plugins (recipes), **Connect actions**, **Framework definitions**, multi-component publishes (Alembic + scene) — natural extensions if you port patterns from `houdiniassets.py` to Py3.

---

## 8. Environment variables cheat sheet

| Variable | Set by | Used by |
|----------|--------|---------|
| `FTRACK_SERVER` / `FTRACK_SERVER_URL` | Connect / studio | API endpoint |
| `FTRACK_API_USER`, `FTRACK_API_KEY` | User / integrations.json | Session auth |
| `FTRACK_TASKID`, `FTRACK_SHOTID` | Connect launch hook | DCC context |
| `FS`, `FE` | Connect launch hook | Timeline |
| `FTRACK_LOCATION` | Workstation / site | Which location plugin is “here” |
| `FTRACK_EVENT_PLUGIN_PATH` | Connect | Hook discovery |
| `PYTHONPATH` | Connect launch | DCC sees integration code |

---

## 9. Suggested learning order (1–2 evenings)

1. Read [Integrating pipelines](https://developer.ftrack.com/integrating-pipelines/) overview (15 min).
2. Skim **Publishing** entity diagram in ftrack Studio help (above link).
3. Walk **`discover_integration.py`** + **`publisher.py`** in `ftrack-connect-houdini` (legacy UX).
4. Run/read one **action** recipe: `clone-review-with-latest` `register()` + `BaseAction`.
5. Read **`customise-structure`** recipe — locations + structure (how paths are generated).
6. Map each step to **`FtrackPublisher.publish_usd`** and your demo checklist [DEMO_CHECKLIST.md](DEMO_CHECKLIST.md).

---

## 10. Interview talking points (Backlight / pipeline TD)

- Backlight’s stack is **tracking + review + Connect**; pipeline TDs extend via **`ftrack_api`**, **hooks**, and **locations**, moving toward the **Connect Pipeline Framework** on Python 3.
- You respect the **Asset vs Task vs Version** model and publish USD as **components** on a **location**.
- You reuse **Connect launch context** (`FTRACK_TASKID`) without relying on deprecated Py2 connectors.
- You separate **integration logic** (testable, MCP/API) from **Houdini UI** — same modular idea as Framework layers.
- **Iconik** (or any MAM) sits beside ftrack via **metadata bridges**, not by replacing ftrack versions.

---

## References (bookmarks)

- [Developer Hub — Integrating pipelines](https://developer.ftrack.com/integrating-pipelines/)
- [Connect — Developing plugins](https://developer.ftrack.com/integrating-pipelines/connect/developing_plugins/index.html)
- [Connect — Hooks](https://developer.ftrack.com/integrating-pipelines/guides/customise-connect/hooks/)
- [Connect Pipeline Framework docs](https://ftrackhq.github.io/ftrack-connect-pipeline/)
- [ftrack Python API](https://ftrack-python-api.readthedocs.io/)
- [ftrack-recipes (GitHub)](https://github.com/ftrackhq/ftrack-recipes)
- Local: `~/dev/ftrack-recipes-main`, `~/dev/ftrack-connect-houdini`
- Local: [FTRACK_CONNECT.md](FTRACK_CONNECT.md), [VFX_PIPELINE.md](VFX_PIPELINE.md)
