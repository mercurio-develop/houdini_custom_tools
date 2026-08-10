"""USD material naming strategies for import/rebuild pipelines."""

from __future__ import annotations

from modules.usd_solaris_utils import houdini_safe_name


def name_from_bound_prim(stage, prim_path: str, attr_base: str) -> str | None:
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return None
    for attr_name in (attr_base, f"primvars:{attr_base}"):
        attr = prim.GetAttribute(attr_name)
        if attr and attr.HasAuthoredValue():
            raw = str(attr.Get())
            if raw:
                token = raw.split("/")[-1]
                if "_" in token:
                    return token.split("_")[-1]
                return token
    return None


def resolve_material_display_name(
    stage,
    usd_mat,
    assignments: dict[str, list[str]],
    strategy: str = "usd_prim",
) -> str:
    from pxr import UsdGeom

    mat_path = str(usd_mat.GetPath())
    prim = usd_mat.GetPrim()
    bound = assignments.get(mat_path) or []

    if strategy == "shop_materialpath" and bound:
        name = name_from_bound_prim(stage, bound[0], "shop_materialpath")
        if name:
            return name

    if strategy == "usdmaterialpath" and bound:
        name = name_from_bound_prim(stage, bound[0], "usdmaterialpath")
        if name:
            return name

    if strategy == "subset" and bound:
        for geo_path in bound:
            geo = stage.GetPrimAtPath(geo_path)
            if geo and geo.IsA(UsdGeom.Subset):
                return geo.GetName()

    if strategy == "prim_name" and bound:
        geo = stage.GetPrimAtPath(bound[0])
        if geo:
            if geo.IsA(UsdGeom.Subset) and geo.GetParent():
                return geo.GetParent().GetName()
            return geo.GetName()

    return prim.GetName()


def allocate_safe_names(
    materials: list[dict],
    strategy: str,
    stage,
    mat_by_path: dict,
    assignments: dict,
) -> list[dict]:
    used: set[str] = set()
    enriched = []
    for entry in materials:
        usd_mat = mat_by_path.get(entry["material_path"])
        if usd_mat is None:
            display = entry.get("name", "material")
        else:
            display = resolve_material_display_name(stage, usd_mat, assignments, strategy)
        safe = houdini_safe_name(display, used)
        enriched.append({**entry, "display_name": display, "safe_name": safe})
    return enriched
