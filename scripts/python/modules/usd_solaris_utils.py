"""Original USD/Solaris helpers inspired by common publish patterns (not third-party code)."""

from __future__ import annotations

import os
import re
import zipfile
from typing import Any

USD_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")

# Channel keys used across texture extraction and MaterialX wiring
TEXTURE_CHANNEL_ALIASES: dict[str, tuple[str, ...]] = {
    "base_color": ("albedo", "color", "diffuse", "diffusecolor", "basecolor", "base_color", "col"),
    "metallic": ("metallic", "metal", "metalness"),
    "roughness": ("roughness", "specularroughness", "refl_roughness", "rough"),
    "normal": ("normal", "bump", "nrm", "norm", "normalcamera"),
    "specular": ("specular", "reflection", "reflect", "refl"),
    "opacity": ("opacity", "alpha", "transparency", "mask"),
    "displacement": ("displacement", "disp", "height"),
    "emission": ("emission", "emit", "emissive"),
}

SHADER_INPUT_TO_CHANNEL: dict[str, str] = {
    "diffusecolor": "base_color",
    "basecolor": "base_color",
    "albedo": "base_color",
    "metallic": "metallic",
    "roughness": "roughness",
    "normal": "normal",
    "opacity": "opacity",
    "displacement": "displacement",
    "emissivecolor": "emission",
    "emission": "emission",
}


def increment_version_token(name: str) -> str:
    """Bump trailing _v###_ suffix or append _v001_."""
    match = re.search(r"_v(\d+)_$", name)
    if match:
        num = int(match.group(1)) + 1
        return re.sub(r"_v\d+_$", f"_v{num:03d}_", name)
    return f"{name}_v001_"


def is_usdz_path(path: str) -> bool:
    return path.lower().endswith(".usdz")


def extract_usdz_archive(usdz_path: str, extract_to: str | None = None) -> str | None:
    """Extract USDZ zip to disk; returns extraction root."""
    usdz_path = os.path.abspath(os.path.expanduser(usdz_path))
    if not os.path.isfile(usdz_path) or not is_usdz_path(usdz_path):
        return None

    if extract_to is None:
        base = os.path.splitext(os.path.basename(usdz_path))[0]
        extract_to = os.path.join(os.path.dirname(usdz_path), f"{base}_usdz_extracted")

    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(usdz_path, "r") as archive:
        archive.extractall(extract_to)
    return extract_to


def resolve_asset_path(raw_value: Any, usd_folder: str) -> str | None:
    """Resolve Sdf.AssetPath or string to absolute forward-slash path."""
    if raw_value is None:
        return None

    text = str(raw_value)
    if hasattr(raw_value, "path"):
        text = str(raw_value.path)

    if "@" in text and "->" in text:
        text = text.split("->", 1)[-1].strip().strip("@")

    text = text.replace("\\", "/")
    if not text or text.startswith("#"):
        return None

    if os.path.isabs(text) and os.path.isfile(text):
        return text

    candidate = os.path.normpath(os.path.join(usd_folder, text.lstrip("./")))
    if os.path.isfile(candidate):
        return candidate.replace("\\", "/")
    return None


def get_usd_root_folder(stage) -> str:
    try:
        real_path = stage.GetRootLayer().realPath
        if real_path:
            return os.path.dirname(os.path.abspath(real_path))
    except Exception:
        pass
    return ""


def find_usd_filepath_on_node(node) -> str | None:
    """Scan string parms on a LOP for an existing USD file path."""
    import hou

    for parm in node.parms():
        try:
            template = parm.parmTemplate()
            if template.type() not in (hou.parmTemplateType.String,):
                continue
            raw = parm.eval()
            if not isinstance(raw, str):
                continue
            expanded = hou.text.expandString(raw)
            lower = expanded.lower()
            if any(lower.endswith(ext) for ext in USD_EXTENSIONS) and os.path.isfile(expanded):
                return os.path.abspath(expanded)
        except Exception:
            continue
    return None


def get_stage_from_lop(node, cook_first: bool = True):
    """Cook LOP and return USD stage, walking inputs if needed."""
    import hou

    visited = set()

    def _walk(n):
        if n is None or n.path() in visited:
            return None
        visited.add(n.path())
        if cook_first:
            n.cook(force=True)
        if hasattr(n, "stage"):
            stage = n.stage()
            if stage is not None:
                return stage
        for inp in n.inputs():
            if inp is not None:
                found = _walk(inp)
                if found is not None:
                    return found
        path = find_usd_filepath_on_node(n)
        if path:
            from pxr import Usd

            if is_usdz_path(path):
                extracted = extract_usdz_archive(path)
                if extracted:
                    for root, _dirs, files in os.walk(extracted):
                        for fname in files:
                            if fname.lower().endswith((".usd", ".usda", ".usdc")):
                                return Usd.Stage.Open(os.path.join(root, fname))
            return Usd.Stage.Open(path)
        return None

    return _walk(node)


def list_usd_cameras(stage) -> list[dict]:
    from pxr import Usd, UsdGeom

    cameras = []
    time_code = Usd.TimeCode.Default()
    cache = UsdGeom.XformCache(time_code)

    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Camera):
            continue
        cam = UsdGeom.Camera(prim)
        world = cache.GetLocalToWorldTransform(prim)
        translation = world.ExtractTranslation()
        rotation = world.ExtractRotation()
        cameras.append({
            "path": str(prim.GetPath()),
            "name": prim.GetName(),
            "focal_length": cam.GetFocalLengthAttr().Get(time_code),
            "horizontal_aperture": cam.GetHorizontalApertureAttr().Get(time_code),
            "vertical_aperture": cam.GetVerticalApertureAttr().Get(time_code),
            "translate": [translation[i] for i in range(3)],
            "rotate": [rotation[i] for i in range(3)],
        })
    return cameras


def get_all_usd_materials(stage) -> list:
    from pxr import UsdShade

    materials = []
    for prim in stage.Traverse():
        if prim.IsA(UsdShade.Material):
            materials.append(UsdShade.Material(prim))
    return materials


def get_material_assignments(stage) -> dict[str, list[str]]:
    from pxr import UsdShade

    mapping: dict[str, list[str]] = {}
    for prim in stage.Traverse():
        if not prim.IsActive():
            continue
        binding = UsdShade.MaterialBindingAPI(prim)
        mat, _rel = binding.ComputeBoundMaterial()
        if mat and mat.GetPrim().IsValid():
            mat_path = str(mat.GetPath())
            geo_path = str(prim.GetPath())
            mapping.setdefault(mat_path, []).append(geo_path)
    return mapping


def get_materials_in_binding_order(stage) -> list[str]:
    order = []
    seen = set()
    for prim in stage.Traverse():
        if not prim.IsActive():
            continue
        from pxr import UsdShade

        binding = UsdShade.MaterialBindingAPI(prim)
        mat, _rel = binding.ComputeBoundMaterial()
        if mat and mat.GetPrim().IsValid():
            path = str(mat.GetPath())
            if path not in seen:
                seen.add(path)
                order.append(path)
    return order


def _match_channel(name: str) -> str | None:
    key = name.lower().replace(":", "").replace("_", "").replace("inputs", "")
    if key in SHADER_INPUT_TO_CHANNEL:
        return SHADER_INPUT_TO_CHANNEL[key]
    for channel, aliases in TEXTURE_CHANNEL_ALIASES.items():
        for alias in aliases:
            if alias.replace("_", "") in key or key in alias.replace("_", ""):
                return channel
    return None


def extract_texture_map_from_material(usd_mat, usd_folder: str) -> dict[str, str]:
    """Walk USD material shader graph and collect texture paths by channel key."""
    from pxr import Sdf, UsdShade

    textures: dict[str, str] = {}
    material_prim = usd_mat.GetPrim()

    for prim in (material_prim, *material_prim.GetAllChildren()):
        for attr in prim.GetAttributes():
            if attr.GetName() != "inputs:file":
                continue
            resolved = resolve_asset_path(attr.Get(), usd_folder)
            if not resolved:
                continue
            channel = _match_channel(prim.GetName()) or _match_channel(attr.GetName())
            if channel and channel not in textures:
                textures[channel] = resolved

    shader = usd_mat.ComputeSurfaceSource()[0]
    if shader:
        for input_name in shader.GetInputNames():
            inp = shader.GetInput(input_name)
            if not inp:
                continue
            val = inp.Get()
            channel = _match_channel(str(input_name))
            if channel and channel in textures:
                continue
            if isinstance(val, (Sdf.AssetPath, str)):
                resolved = resolve_asset_path(val, usd_folder)
                if resolved and channel:
                    textures[channel] = resolved
            conn = inp.GetConnectedSource()
            if conn:
                src_prim = conn[0].GetPrim()
                file_attr = src_prim.GetAttribute("inputs:file")
                if file_attr and file_attr.HasAuthoredValue():
                    resolved = resolve_asset_path(file_attr.Get(), usd_folder)
                    ch = channel or _match_channel(src_prim.GetName())
                    if resolved and ch and ch not in textures:
                        textures[ch] = resolved

    return textures


def houdini_safe_name(name: str, used: set[str] | None = None) -> str:
    import re

    safe = re.sub(r"[^A-Za-z0-9_]", "_", name)
    safe = safe.strip("_") or "material"
    if safe[0].isdigit():
        safe = f"m_{safe}"
    used = used or set()
    base = safe
    idx = 1
    while safe in used:
        safe = f"{base}_{idx}"
        idx += 1
    used.add(safe)
    return safe
