"""Headless Houdini 22 Crucible Verification Suite for houdini_custom_tools [LAB-CLONE]."""

from __future__ import annotations

import ast
import importlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_ROOT = ROOT / "scripts" / "python"
sys.path.insert(0, str(PY_ROOT))

import hou  # noqa: E402


def verify_ast_and_no_bom() -> dict:
    py_files = sorted(p for p in ROOT.rglob("*.py") if ".git" not in p.parts and "__pycache__" not in p.parts)
    failures = []
    for p in py_files:
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            failures.append((str(p.relative_to(ROOT)), "UTF-8 BOM present"))
            continue
        try:
            ast.parse(raw.decode("utf-8"), filename=str(p))
        except SyntaxError as exc:
            failures.append((str(p.relative_to(ROOT)), str(exc)))
    assert not failures, f"AST/BOM failures: {failures}"
    return {"py_files_parsed": len(py_files), "failures": 0}


def verify_shelf_xml() -> dict:
    shelf = ROOT / "toolbar" / "custom_tools.shelf"
    tree = ET.parse(shelf)
    sroot = tree.getroot()
    tools = sroot.findall("tool")
    banned_imports = [
        "batch_importer_with_analyze",
        "spaceship_visualizer",
        "tools.asset_builder",
        "lops_asset_builder_workflow",
        "iconik_tops",
    ]
    bad = []
    for t in tools:
        code = (t.findtext("script") or "")
        for b in banned_imports:
            if b in code:
                bad.append((t.attrib.get("name"), b))
    assert not bad, f"Dead shelf tool imports remain: {bad}"
    return {"shelf_tools": len(tools), "dead_refs": 0}


def verify_imports() -> dict:
    targets = [
        "custom_utils",
        "modules.asset_folder_scanner",
        "modules.houdini_node_utils",
        "modules.misc_utils",
        "modules.texture_path_repair",
        "modules.usd_discovery",
        "modules.usd_solaris_utils",
        "tools.lops_asset_builder_v3.asset_builder_config",
        "tools.lops_asset_builder_v3.asset_builder_engine",
        "tools.lops_asset_builder_v3.geo_mtl_builder",
        "tools.lops_asset_builder_v3.network_layout",
        "tools.material_tools.TexToMtlx_USD.materialx_exporter",
        "tools.psx_tools",
        "tools.psx_tools.dither",
        "tools.psx_tools.karma_presets",
        "tools.psx_tools.psx_asset_builder",
        "tools.psx_tools.sop_effects",
        "tools.psx_tools.psx_tools_ui",
        "tools.texture_from_disk",
        "pipeline.create_project",
        "pipeline.save_tool",
        "HMCP.handlers.render.karma",
    ]
    for mod in targets:
        importlib.import_module(mod)
    return {"imported": len(targets)}


def verify_vex_snippets() -> dict:
    from tools.psx_tools.sop_effects import SCREEN_SNAP_VEX, WOBBLE_VEX

    split_vex = (ROOT / "scripts" / "VEX" / "snippets" / "split_attribute.vex").read_text(encoding="utf-8")
    geo = hou.node("/obj").createNode("geo", "crucible_vex_test")
    box = geo.createNode("box", "src_box")
    results = {}
    for label, code, run_class in [
        ("WOBBLE_VEX", WOBBLE_VEX, 0),
        ("SCREEN_SNAP_VEX", SCREEN_SNAP_VEX, 0),
        ("split_attribute.vex", split_vex, 1),
    ]:
        w = geo.createNode("attribwrangle", "w_" + label.lower().replace(".", "_"))
        w.setInput(0, box)
        w.parm("class").set(run_class)
        w.parm("snippet").set(code)
        w.cook(force=True)
        errs = list(w.errors())
        assert not errs, f"{label} VEX compile error: {errs}"
        results[label] = {"errors": 0, "prims": len(w.geometry().prims())}
    geo.destroy()
    return results


def verify_karma_resolution_unlock() -> dict:
    from tools.psx_tools.karma_presets import apply_psx_karma_settings
    from tools.psx_tools.psx_config import PSXAssetConfig

    cfg = PSXAssetConfig(render_resolution=(320, 240))
    node = apply_psx_karma_settings(config=cfg)
    assert node is not None, "apply_psx_karma_settings returned None"
    actual = tuple(int(v) for v in node.parmTuple("resolution").eval())
    assert actual == (320, 240), f"Expected (320, 240), got {actual}"
    node.destroy()
    return {"psx_karma_resolution": list(actual)}


def verify_psx_sop_and_dither() -> dict:
    import numpy as np
    from tools.psx_tools.dither import apply_dithering
    from tools.psx_tools.psx_config import PSXAssetConfig
    from tools.psx_tools.psx_sop_pipeline import apply_psx_sop_chain

    # Pure dither check
    img = np.linspace(0, 255, 32 * 32 * 3, dtype=np.float32).reshape(32, 32, 3)
    out = apply_dithering(img, method="BAYER", palette_size=16, dither_scale=0.1)
    assert out.shape == (32, 32, 3) and out.dtype == np.uint8

    # Live Houdini SOP chain check
    geo = hou.node("/obj").createNode("geo", "crucible_psx_sop")
    sphere = geo.createNode("sphere", "src_sphere")
    sphere.parm("type").set(2)  # polygon
    cfg = PSXAssetConfig(decimate_ratio=0.5, triangulate=True, apply_vertex_wobble=True, apply_screen_snap=True)
    end_node = apply_psx_sop_chain(geo, sphere, cfg)
    end_node.cook(force=True)
    assert not end_node.errors(), f"PSX SOP chain errors: {end_node.errors()}"
    prims_out = len(end_node.geometry().prims())
    geo.destroy()
    return {"dither_shape": list(out.shape), "psx_sop_prims": prims_out}


def main() -> int:
    summary = {
        "houdini_version": hou.applicationVersionString(),
        "ast_bom": verify_ast_and_no_bom(),
        "shelf_xml": verify_shelf_xml(),
        "imports": verify_imports(),
        "vex": verify_vex_snippets(),
        "karma": verify_karma_resolution_unlock(),
        "psx_pipeline": verify_psx_sop_and_dither(),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
