# Architecture

Custom Houdini pipeline tools organized as five products. This document is the stable, version-controlled overview; session notes live under gitignored `docs/`.

## Layout

```
python/
├── integrations/             # ftrack + Iconik clients, publish workflow, FastAPI (no hou)
├── mcp/                      # MCP server for Production Hub tools
├── pipeline/                 # Project folders, save tool, USD project helpers
├── projects/production_hub/  # Portfolio README, demo checklist, Next.js dashboard
├── tools/
│   ├── production_hub/          # PySide6 ftrack/Iconik + LOPS publish UI
│   ├── lops_asset_builder_v3/   # Flagship LOPS USD/MaterialX builder (UI + CLI)
│   ├── kb3d_tools/              # USD library toolkit (BGEO, assemblies, transforms)
│   ├── material_tools/          # Texture → MaterialX (Houdini + standalone USD)
│   ├── batch_import_workflow/   # Multi-asset import workflow (optional)
│   ├── _archive/                # Superseded code kept for reference
│   └── *.py                     # Stage utilities (organizer, merge, selection, …)
├── modules/                  # Shared helpers (misc_utils, convex hull, …)
├── utils/                    # Quick scripts, tests, dev utilities
└── custom_utils.py           # Module reload for shelf development
```

## Product 1: LOPS Asset Builder (v3)

**Purpose:** Build component-based USD assets inside Houdini LOPS—geometry and material variants, MaterialX libraries, optional lookdev subnet and Karma setup.

| Layer | Module | Role |
|-------|--------|------|
| Core | `lops_asset_builder_v3.py` | Node graph construction, materials, layout |
| CLI | `lops_asset_builder_cli.py` | `AssetBuilderConfig`, JSON/batch builds without UI |
| UI | `batch_asset_builder.py`, `asset_builder_ui.py` | PySide6 batch and progress dialogs |
| Support | `material_validator.py`, `texture_variant_detector.py` | Artist-facing validation |

**Data flow:** Config (dict/JSON) → CLI or UI → LOPS network → USD stage prims + material variants.

## Product 2: USD Library Toolkit (`kb3d_tools`)

**Purpose:** Create and maintain KitBash3D-style USD libraries from parts, BGEO, or scanned assemblies—not tied to a single DCC step.

| Area | Location | Role |
|------|----------|------|
| Parts → assembly | `asset_library_builder/` (canonical `build_from_parts`) | Payload/geo/mtl from part folders |
| BGEO → USD | `kb3d_tools/bgeo/` | Analyze BGEO attributes, emit KB3D hierarchy |
| Transforms | `kb3d_tools/core/transform_extractor.py` | Extract transforms before FBX/BGEO separation |
| Build / scan | `kb3d_usd_builder.py`, `kb3d_assembly_scanner.py` | Class-based USD creation and reverse scan |
| Primary UI | `kb3d_proper_assembly_builder_ui.py` | Documented shelf entry (`show_ui`) |

Legacy duplicate builders re-export the canonical APIs; prefer `tools.asset_library_builder` and `tools.kb3d_tools` imports.

## Product 3: Studio pipeline utilities

**Purpose:** Project lifecycle outside a single LOP network.

- `pipeline/project_manager.py` — PySide6 project/sequence/file browser with JSON config under `$CUSTOM_TOOLS/config`.
- `pipeline/save_tool.py` — Save/version helpers used by the project manager.
- `pipeline/create_project.py`, `asset_generator.py`, `usd_project_manager.py` — Project scaffolding and USD project paths.

## Product 4: Stage and material helpers

**Stage:** `lop_network_organizer.py`, `merge_selected_lops.py`, `select_same_type_simple.py`, `lops_light_rig_pipeline.py` (uses v3 lookdev helpers).

**Materials:**

- `material_tools/TexToMtlX_V2/` — Houdini MaterialX subnet UI (in-scene).
- `material_tools/TexToMtlx_USD/` — Standalone USD/MaterialX export without a full LOPS build.
- `tools/tex_to_mtlx.py` — Re-export of V2 for backward-compatible imports.

## Product 5: Production Hub (ftrack · Iconik · USD publish)

**Purpose:** Bridge production tracking and MAM metadata to Houdini USD deliverables without duplicating LOPS build logic.

| Layer | Module | Role |
|-------|--------|------|
| Settings | `integrations/settings.py` | `$CUSTOM_TOOLS/config/integrations.json` + env vars |
| ftrack | `integrations/ftrack/` | Session, task queries, AssetVersion publish |
| Iconik | `integrations/iconik/` | Search, metadata link/create |
| Workflow | `integrations/workflows/publish_usd_deliverable.py` | Orchestrates ftrack + Iconik |
| Identifiers | `integrations/identifiers/vfx.py` | VFX metadata for Iconik (shot, KB3D code) |
| DCC UI | `tools/production_hub/production_hub_ui.py` | PySide6 tabs: connect, task, build (CLI), publish |
| MCP | `mcp/production_hub_server.py` | Same APIs for Cursor/agents |
| HTTP | `integrations/http_api.py` | FastAPI for Next.js dashboard |

**Data flow:** ftrack task selection → optional LOPS CLI build (`lops_asset_builder_cli`) → local USD path → ftrack AssetVersion + Iconik metadata.

Portfolio docs: `projects/production_hub/README.md`.

## Dependencies

- **Runtime:** Houdini 21.x (`hou`), Python 3.11+, PySide6, optional `pxr` for USD library tools.
- **Integrations (optional venv):** `httpx`, `ftrack-python-api`, `mcp`, `fastapi` — see `requirements-integrations.txt`.
- **Path:** Add `scripts/python` to `PYTHONPATH` or use the Houdini package pointing at `$CUSTOM_TOOLS`.

## Extension guidelines

1. New features belong in the product that owns the workflow (avoid a parallel “builder”).
2. **Production tracking / MAM** logic stays in `integrations/`; Houdini UI stays thin.
3. Expose CLI/config for anything artists run in batch; keep UI thin.
4. Shared logic goes in `modules/`, not copied into shelf scripts.
5. Superseded tools move to `tools/_archive/` with a short README, not deleted immediately.

## For reviewers

These tools mirror common pipeline engineer responsibilities: asset management (USD structure, batch CLI), PySide tooling, **ftrack/Iconik integration**, artist support (validators, organizers), and maintainable layering (config dataclasses, package boundaries)—developed for Houdini/USD production workflows on Linux.
