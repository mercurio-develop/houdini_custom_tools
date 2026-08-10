# Custom Tools Shelf — Audit & Refactor Plan

**Shelf file:** `toolbar/custom_tools.shelf`  
**Python root:** `$CUSTOM_TOOLS/scripts/python`  
**Last updated:** 2026-07-29 (post H22 stabilization)

This document maps every tool on the **Custom Tools** shelf to code, priority tiers, recent fixes, and a phased clean-code / architecture plan.

---

## Shelf inventory

**33 tools** are exposed on the **Custom Tools** shelf (`<toolshelf name="Custom Tools">`).

One additional reload tool (`reload_pak_mod`) exists in the same shelf file but is **not** on the shelf tab — treat as legacy duplicate.

| # | Shelf tool | Shelf ID | Entry script / module | Status |
|---|------------|----------|------------------------|--------|
| 1 | Reload Packages | `Reload Packages` | `custom_utils.reload_packages()` | ✅ Active — H22 reload fixed |
| 2 | Create Project | `create_project` | `pipeline.create_project.CreateProject` | ✅ Active |
| 3 | Clean Logs | `clean_logs` | `custom_utils.clean_log()` | ✅ Active |
| 4 | Project Manager | `Project Manager` | `pipeline.project_manager.ProjectManager` | ✅ Active |
| 5 | Scene Cache Manager | `Scene Cache Mangater` | `tools.scene_cache_manager` | ✅ Active (typo in shelf ID) |
| 6 | Batch Asset Builder | `batch_asset_builder` | `tools.lops_asset_builder_v3.batch_asset_builder.show_batch_asset_builder()` | ✅ Active — production |
| 7 | Lops Asset Builder | `lops_asset_builder` | `tools.lops_asset_builder_v3.lops_asset_builder_v3.create_component_builder()` | ✅ Active — flagship |
| 8 | LOPS Light Rig | `lops_light_rig` | `tools.lops_light_rig.create_three_point_light()` | ✅ Active — non-fatal skip if no bounds |
| 9 | Place Light Highlight | `place_light_highlight` | Inline HScript / UI state | ✅ Active |
| 10 | Split Geo | `split_geo` | `tools.split_geo.split_geo()` | ✅ Active |
| 11 | Group Importer | `group-importer` | `tools.batch_import_workflow.batch_import_workflow` | ✅ Active |
| 12 | Top net | `top_net` | ~110 lines inline Python in shelf | ⚠️ Inline — extract to module |
| 13 | File Path Manager | `file_path_manager` | `tools.file_path_manager` | ✅ Active (~1124 lines) |
| 14 | Shader Nodes Script | `collect_nodes_script` | Inline HScript in shelf (~300 lines) | ⚠️ H21 HScript — not Python |
| 15 | Customize Variant Name | `customize_variant_name` | Inline HScript in shelf | ⚠️ Duplicate of v3 logic |
| 16 | Component Material Custom | `component_material_custom` | Inline HScript in shelf | ⚠️ Duplicate of `component_material_custom.py` |
| 17 | Asset Builder Template | `asset_builder_template` | Inline — hardcoded H21 path | ❌ Broken on H22 |
| 18 | Merge Nodes From HIP | `merges_nodes_from_file` | `tools.merge_nodes_from_hipfile` | ✅ Active |
| 19 | Tx To Mtlx V2 | `tx_to_mtlx_v2` | `TexToMtlX_V2/tex_to_mtlx.py` → `TxToMtlx()` | ✅ Active |
| 20 | Show Node Inputs | `show_node_inputs` | `tools.reveal_node_inputs_and_names` | ✅ Active |
| 21 | Node Batch Setter | `node_batch_setter` | `tools.node_batch_setter` | ✅ Active |
| 22 | Texture From Disk | `texture_from_disk` | `tools.texture_from_disk` | ✅ Active |
| 23 | Get Node Code | `get_node_code` | `tools.get_node_code` | ✅ Active |
| 24 | HMCP | `HMCP` | `HMCP.shelf_tool.toggle_mcp_server` | ℹ️ External MCP |
| 25 | Convert To MTLX & USD | `convert_to_mtlx_usd` | `TexToMtlx_USD/tex_to_mtlx_standalone.show_standalone_converter` | ✅ Active |
| 26 | Select All Nodes Of Same Type | `select_all_node_of_same_type` | `tools.select_same_type_simple` | ✅ Active |
| 27 | BATCH IMPORTER WITH ANALYZE | `batch_importer` | `tools.batch_importer_with_analyze` | ✅ Active — overlaps batch scanner |
| 28 | Spaceship Visualizer | `spaceship_visualizer` | `spaceship_visualizer` (missing) | ❌ Broken |
| 29 | Asset Builder | `asset_builder` | `tools.asset_builder` (missing) | ❌ Broken — use v3 |
| 30 | Asset Builder V2 | `asset_builder_v2` | `lops_asset_builder_workflow` (archived) | ❌ Broken — use v3 |
| 31 | Create Camera | `create_lookdev_camera_for_selected` | `tools.lops_lookdev_camera` | ✅ Active |
| 32 | Houdini MCP | `houdini_mcp` | Inline hou / MCP | ℹ️ External |
| 33 | FORCESTART | `FORCESTART` | `HMCP.force_restart` | ℹ️ External MCP |

**Off shelf (same file):**

| Tool | Entry | Notes |
|------|-------|-------|
| Reload Packages and Modules (alt) | `rbw_utils.reload_package()` | ❌ Duplicate — remove or alias to `custom_utils` |

---

## Related tools (not on Custom Tools shelf)

Worth documenting next to LOPS builder for KB3D / Luminara work:

| Tool area | Module | Role |
|-----------|--------|------|
| KB3D Proper Assembly Builder | `tools/kb3d_tools/kb3d_proper_assembly_builder_ui.py` | Assembly UI (may live on another shelf) |
| Asset Library Builder | `tools/asset_library_builder/asset_builder.py` | Canonical `build_from_parts()` |
| KB3D tools | `tools/kb3d_tools/` | BGEO→USD, scanner, assembly |

---

## Tier 0 — Infrastructure (review first)

| Shelf tool | Entry | Notes |
|------------|-------|-------|
| **Reload Packages** | `custom_utils.reload_packages()` | Alt+click reloads in-memory modules only; skips `utils/dev`, `utils/testing`, `test_*.py` |
| Reload Packages (alt) | `rbw_utils.reload_package()` | **Remove** — duplicate |

**Config:** `scripts/python/reload_settings.json`

### Tier 0 checklist

- [x] Fix reload order (package-first, deepest-first)
- [x] Exclude dev/test/examples from reload walk
- [x] Do not `import_module` unknown scripts on reload (prevents TxToMtlx pop-up)
- [x] Remove `reload_pak_mod` / `rbw_utils` duplicate from shelf file
- [ ] Document reload behavior in `reload_settings.json` comments / README

---

## Tier 1 — Core pipeline (highest ROI)

Production path for **KB3D / Secrets of the Luminara**-style work.

### LOPS Asset Builder v3 (flagship)

| Shelf tool | Python entry | Key files (~lines) |
|------------|--------------|-------------------|
| **Lops Asset Builder** | `create_component_builder()` | `lops_asset_builder_v3.py` (~1.1k) |
| **Batch Asset Builder** | `show_batch_asset_builder()` | `batch_asset_builder.py` (~1.9k) |

**Support modules:**

| File | Role | Review focus |
|------|------|--------------|
| `asset_builder_config.py` | Single `AssetBuilderConfig` (GUI + CLI + batch) | Field defaults, `from_dialog()` |
| `asset_builder_engine.py` | Unified `run_asset_build()` pipeline | One orchestration path only |
| `asset_builder_progress.py` | `ProgressLike` protocol, console reporter, validation logging | DRY progress contract |
| `geo_mtl_builder.py` | Geometry import + geo/mtl variant wiring | SOP import, variant loops |
| `material_builder.py` | Texture scan + MaterialX / template fallback | Shared with validator scan utils |
| `network_layout.py` | Network boxes / sticky organization | Pure LOP layout |
| `lops_asset_builder_cli.py` | Thin CLI wrappers around engine | JSON config entry |
| `lops_asset_builder_v3.py` | Interactive shelf entry + re-exports | Dialog → config → engine |
| `asset_builder_ui.py` | Dialog + `ProgressReporter` | UI/theme only |
| `material_validator.py` | Pre-build material check | Naming vs TexToMtlx; KB3D texture roots |
| `texture_scan_utils.py` | Resolve `Textures/png4k`, skip `geo/` | Shared with validator + material_builder |
| `texture_variant_detector.py` | png4k / jpg2k detection | KB3D texture layout |
| `asset_builder_graph.py` | Shared lookdev/light-rig/Karma LOP wiring | Used by engine |
| `componentoutput_custom.py` | ~25k — decompiled node setup | H22 parm safety; **regen candidate** |
| `subnet_lookdev_setup.py` | ~8.5k — lookdev subnet | Same as above |
| `component_material_custom.py` | Material variant subnet | Keep in sync with shelf HScript twin |
| `modules/houdini_node_utils.py` | Safe parm helpers | H21→H22 compatibility |
| `ui/houdini_theme.py` | Shared Qt theme | Modal vs tool-window patterns |

**Docs:** [BATCH_SCANNER_README.md](tools/lops_asset_builder_v3/BATCH_SCANNER_README.md), [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md)

### Tier 1 checklist — stability (Phase A)

- [x] Qt crash on dialog open (parent + window flags)
- [x] Progress bar desync (`set_total(1000)`, `ensure_total()`)
- [x] Headless material scan (`TextureFolderScanner`, no `TxToMtlx()` in pipeline)
- [x] KB3D texture root resolution (`texture_scan_utils`)
- [x] Validation before progress UI (avoid `loadFromFile` + Qt re-entrancy crash)
- [x] Convex hull: native `convexdecomposition` SOP (no scipy)
- [x] Light rig: cook + non-fatal skip; bounds fallback without `defaultPrim`
- [x] Lookdev enabled by default in dialog
- [ ] Unify progress reporting across interactive / CLI / batch
- [x] Add material validation to CLI/batch (parity with GUI)
- [ ] Pass asset name into `subnet_lookdev_setup` lookdev camera (not hardcoded `"ASSET"`)

### Tier 1 checklist — architecture (Phase B)

- [ ] Split `lops_asset_builder_v3.py` → UI orchestration / graph builder / materials
- [x] Extract `AssetBuilderGraph` class (LOP wiring only)
- [ ] Regenerate or shrink `componentoutput_custom.py` / `subnet_lookdev_setup.py`
- [ ] Single `MaterialNamingConfig` path: validator → scanner → `MtlxMaterial`
- [ ] Align batch scanner KB3D rules with interactive validator

### Materials (shared by LOPS builder)

| Shelf tool | Entry | Key files |
|------------|-------|-----------|
| Tx To Mtlx V2 | `TexToMtlX_V2/tex_to_mtlx.py` → `TxToMtlx()` | ~1.2k + `TextureFolderScanner` |
| Convert To MTLX & USD | `TexToMtlx_USD/tex_to_mtlx_standalone.py` | Standalone USD export |
| Shader Nodes Script | Inline HScript in shelf | Not Python — H21 node defs |

**Upgrade:** Point shelf HScript tools (`collect_nodes_script`, `component_material_custom`, `customize_variant_name`) at Python builders (`build_component_material_custom`, etc.).

---

## Tier 2 — Studio / project utilities (medium priority)

| Shelf tool | Module | Size | Review focus |
|------------|--------|------|--------------|
| Project Manager | `pipeline/project_manager.py` | ~511 | Config JSON, paths |
| Create Project | `pipeline/create_project.py` | — | Project scaffolding |
| Scene Cache Manager | `tools/scene_cache_manager.py` | ~332 | LOP filecache patterns |
| File Path Manager | `tools/file_path_manager.py` | ~1124 | Large UI; path rewrite logic |
| Group Importer | `batch_import_workflow/batch_import_workflow.py` | — | Multi-asset import |
| BATCH IMPORTER WITH ANALYZE | `batch_importer_with_analyze.py` | ~370 | Overlap with batch asset builder? |
| Merge Nodes From HIP | `merge_nodes_from_hipfile.py` | — | Hip merge utility |
| Node Batch Setter | `node_batch_setter.py` | — | Parm batch edits |
| Split Geo | `split_geo.py` | — | Geo utilities |

**Upgrade:** Extract shared path/env helpers (`$JOB`, `$CUSTOM_TOOLS`, KB3D roots) into `modules/`; reuse LOPS builder path normalization.

### Tier 2 checklist

- [ ] Shared `path_utils` / KB3D library root detection
- [ ] Consolidate batch import vs batch asset builder scanning
- [ ] Apply `HoudiniTheme` to remaining large dialogs (`file_path_manager`, `project_manager`)

---

## Tier 3 — LOPS stage helpers (smaller, focused)

| Shelf tool | Module |
|------------|--------|
| LOPS Light Rig | `tools/lops_light_rig.py` |
| Place Light Highlight | Inline Houdini UI |
| Create Camera | `tools/lops_lookdev_camera.py` |
| Select All Nodes Of Same Type | `select_same_type_simple.py` |
| Show Node Inputs | `reveal_node_inputs_and_names.py` |
| Texture From Disk | `texture_from_disk.py` |
| Get Node Code | `get_node_code.py` |
| Clean Logs | `custom_utils.clean_log()` |

### Tier 3 checklist

- [x] Light rig graceful fallback (no build abort)
- [ ] Document “cook `/stage` then run Light Rig shelf” workflow
- [ ] Share bounds logic with asset builder (`calculate_prim_bounds`)

---

## Tier 4 — Legacy / broken (remove or hide)

| Shelf tool | Status | Action |
|------------|--------|--------|
| Asset Builder | `tools.asset_builder` missing | **Remove** from shelf |
| Asset Builder V2 | Only in `_archive/` | **Remove** from shelf |
| Spaceship Visualizer | Module missing | **Remove** from shelf |
| Asset Builder Template | H21 hardcoded path | Fix path or **remove** |
| Top net | Inline shelf Python | Extract to `tools/export_top_network.py` |
| component_material_custom (shelf) | Duplicates Python | Point at `component_material_custom.py` |
| HMCP / FORCESTART / Houdini MCP | External | Keep if needed; not pipeline core |
| reload_pak_mod | Duplicate reload | **Remove** |

### Tier 4 checklist

- [x] Hide or delete broken shelf entries (v1, v2, spaceship, template)
- [x] Single reload tool on shelf
- [ ] Move `top_net` inline script to `tools/`
- [x] Fix template path → `$CUSTOM_TOOLS/templates/...`

---

## Architecture snapshot

```
Custom Tools shelf
│
├─ lops_asset_builder ──► lops_asset_builder_v3.create_component_builder()
│                              ├─ asset_builder_ui.py (dialog + ProgressReporter)
│                              ├─ material_validator.py (pre-build, before progress UI)
│                              ├─ build_geo_and_mtl_variants()
│                              │     ├─ componentoutput_custom.py
│                              │     ├─ component_material_custom.py
│                              │     ├─ convexdecomposition SOP (sim proxy)
│                              │     └─ _create_materials() ──► TextureFolderScanner / MtlxMaterial
│                              └─ lookdev branch
│                                    ├─ graft stages / switches
│                                    ├─ lops_light_rig (optional, non-fatal)
│                                    ├─ subnet_lookdev_setup.py
│                                    └─ create_transform_nodes + Karma ROP
│
├─ batch_asset_builder ──► batch_asset_builder.show_batch_asset_builder()
│                              └─ lops_asset_builder_cli.build_asset()
│
├─ tx_to_mtlx_v2 ──► TexToMtlX_V2/tex_to_mtlx.TxToMtlx()  (interactive only)
│
└─ Reload Packages ──► custom_utils.reload_packages()
                         └─ reload_settings.json
```

---

## Suggested review order

```
1. custom_utils + reload_settings
        ↓
2. lops_asset_builder_v3 core (interactive)
        ↓
3. material_validator + tex_to_mtlx / TextureFolderScanner
        ↓
4. batch_asset_builder + CLI
        ↓
5. Decompiled node files (componentoutput_custom, subnet_lookdev_setup)
        ↓
6. pipeline + file_path_manager
        ↓
7. Legacy shelf cleanup
```

---

## Phased roadmap

### Phase A — Stability (1–2 weeks) ← mostly done

Focus files:

- `lops_asset_builder_v3.py`, `asset_builder_ui.py`, `lops_asset_builder_cli.py`
- `material_validator.py`, `texture_scan_utils.py`, `TexToMtlX_V2/tex_to_mtlx.py`
- `batch_asset_builder.py`
- `modules/houdini_node_utils.py`, `modules/misc_utils.py`, `ui/houdini_theme.py`
- `custom_utils.py`, `reload_settings.json`
- `modules/convex_hull_utils.py`, `tools/lops_light_rig.py`

**Exit criteria:** KB3D Luminara asset builds end-to-end on H22 with lookdev; reload does not spawn dev UIs; no fatal light-rig abort.

### Phase B — Architecture (2–4 weeks)

- Extract `AssetBuilderGraph` from UI orchestration
- Headless materials path: `TextureFolderScanner` + `MtlxMaterial` only (no Qt) in all modes
- Regenerate or template-ize `componentoutput_custom.py` / `subnet_lookdev_setup.py`
- Unified `ProgressReporter` protocol for GUI / CLI / batch
- Material validation in CLI/batch

**Exit criteria:** `lops_asset_builder_v3.py` under ~400 lines of orchestration; decompiled files reduced or generated from templates.

### Phase C — Consolidation (ongoing)

- One asset builder story on shelf: **v3 interactive + batch** only
- Retire v1/v2/template/spaceship shelf entries
- Move inline shelf scripts to `tools/`
- HScript TAB tools call Python builders
- Document KB3D Proper Assembly Builder alongside LOPS builder in README

**Exit criteria:** Shelf has no broken tools; no duplicate reload; HScript/Py duplication eliminated for material/variant tools.

---

## Quick wins tracker

| Issue | Where | Status |
|-------|-------|--------|
| Progress bar desync | `ProgressReporter.set_total(1000)` | ✅ Fixed |
| Qt crash on open | `HoudiniTheme`, dialog parenting | ✅ Fixed |
| Reload breaks packages / spawns UIs | `custom_utils.reload_packages` | ✅ Fixed |
| `loadFromFile` during progress (SIGSEGV) | Validation before progress; no re-extract in build | ✅ Fixed |
| scipy missing on convex hull | `convexdecomposition` SOP | ✅ Fixed |
| Light rig aborts build | Non-fatal skip + bounds fallback | ✅ Fixed |
| Lookdev off by default | `cb_create_lookdev.setChecked(True)` | ✅ Fixed |
| KB3D texture walk through `geo/` | `texture_scan_utils.resolve_texture_search_roots` | ✅ Fixed |
| Duplicate material scan logic | Partial — shared `MaterialNamingConfig` + scanner | 🔄 In progress |
| 25k-line decompiled files | `componentoutput_custom.py` | ⏳ Phase B |
| Broken shelf tools (v1, v2, …) | `custom_tools.shelf` | ✅ Phase C |
| HScript duplicated in shelf | collect / component_material | ⏳ Phase C |
| CLI/batch material validation | `lops_asset_builder_cli.py` | ✅ Phase A |

---

## KB3D / Luminara recommended paths

When using **Lops Asset Builder** with `kb3d_secretsoftheluminara`:

| Field | Example |
|-------|---------|
| Main asset | `.../geo/KB3D_SOL_BldgTemple/KB3D_SOL_BldgTemple.bgeo.sc` |
| Textures | `.../Textures/png4k` (library root also resolves automatically) |
| Lookdev | Leave **Create Lookdev Setup** enabled |
| Light rig | Optional — skipped automatically if component output is not cooked |

---

## Next actions (recommended)

1. **Phase C (quick):** Remove broken shelf tools (asset_builder, asset_builder_v2, spaceship_visualizer) and duplicate reload.
2. **Phase B (start):** Sketch `AssetBuilderGraph` interface — inputs from UI/CLI JSON, outputs node handles for layout.
3. **Phase A (finish):** CLI/batch material validation + unified progress reporter.

For implementation tracking, check boxes in this file as work completes.
