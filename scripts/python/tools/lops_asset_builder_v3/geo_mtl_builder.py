"""Geometry import and geo/material variant graph construction."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import hou

from modules.misc_utils import MaterialNamingConfig, _sanitize
from tools.lops_asset_builder_v3.componentoutput_custom import componentoutput_custom_creation
from tools.lops_asset_builder_v3.material_builder import create_materials, extract_material_names

if TYPE_CHECKING:
    from tools.lops_asset_builder_v3.asset_builder_progress import ProgressLike


def _create_convex(parent):
    return parent.createNode("convexdecomposition", "convex_hull_setup")


def _bind_materials_by_mesh_name(comp_material, material_lib) -> None:
    """Bind each mesh to the material of the same name (/ASSET/mtl/<mesh name>)."""
    names = [child.name() for child in material_lib.children()]
    comp_material.parm("nummaterials").set(len(names))
    for i, name in enumerate(names, 1):
        comp_material.parm(f"primpattern{i}").set(f"%type:Mesh & /ASSET/**/{name}")
        comp_material.parm(f"matspecpath{i}").set(f"/ASSET/mtl/{name}")


def prepare_imported_asset(
    parent,
    name,
    extension,
    path,
    out_node,
    skip_matchsize=False,
    lowercase_material_names: bool = True,
) -> None:
    try:
        parent = hou.node(parent.path() + "/sopnet/geo")
        default_output = hou.node(f"{parent.path()}/default")
        proxy_output = hou.node(f"{parent.path()}/proxy")
        sim_output = hou.node(f"{parent.path()}/simproxy")

        file_extension = ["fbx", "obj", "bgeo", "bgeo.sc"]
        if extension in file_extension:
            file_import = parent.createNode("file", _sanitize(f"import_{name}"))
            parm_name = "file"
        elif extension == "abc":
            file_import = parent.createNode("alembic", _sanitize(f"import_{name}"))
            parm_name = "fileName"
        else:
            return

        attrib_wrangler = parent.createNode("attribwrangle", "convert_mat_to_name")
        attrib_delete = parent.createNode("attribdelete", "keep_P_N_UV_NAME")
        remove_points = parent.createNode("add", _sanitize(f"remove_points"))

        match_size = None
        if not skip_matchsize:
            match_size = parent.createNode("matchsize", _sanitize(f"matchsize_{name}"))
            match_size.setParms({"justify_x": 0, "justify_y": 1, "justify_z": 0})

        file_import.parm(parm_name).set(f"{path}/{name}.{extension}")

        vex_lines = []
        if lowercase_material_names:
            vex_lines.append('s@shop_materialpath = tolower(replace(s@shop_materialpath, " ", "_"));')
        else:
            vex_lines.append('s@shop_materialpath = replace(s@shop_materialpath, " ", "_");')
        vex_lines.extend(
            [
                'string material_to_name[] = split(s@shop_materialpath, "/");',
                's@name = material_to_name[-1];',
                's@name = rstrip(s@name, "_");',
            ]
        )
        attrib_wrangler.setParms({"class": 1, "snippet": "\n".join(vex_lines)})
        attrib_delete.setParms({"negate": True, "ptdel": "N P", "vtxdel": "uv", "primdel": "name"})
        remove_points.parm("remove").set(True)

        if skip_matchsize:
            attrib_wrangler.setInput(0, file_import)
        else:
            match_size.setInput(0, file_import)
            attrib_wrangler.setInput(0, match_size)

        attrib_delete.setInput(0, attrib_wrangler)
        remove_points.setInput(0, attrib_delete)
        default_output.setInput(0, remove_points)

        poly_reduce = parent.createNode("polyreduce::2.0", "reduce_to_5")
        attrib_colour = parent.createNode("attribwrangle", "set_color")
        color_node = parent.createNode("color", "unique_color")
        attrib_promote = parent.createNode("attribpromote", "promote_Cd")
        attrib_delete_name = parent.createNode("attribdelete", _sanitize(f"delete_asset_name"))
        name_node = parent.createNode("name", "name")

        poly_reduce.parm("percentage").set(5)
        attrib_colour.parm("class").set(1)
        ptg = attrib_colour.parmTemplateGroup()
        ptg.insertAfter(
            "class",
            hou.StringParmTemplate(name="asset_name", label="Asset name", num_components=1),
        )
        attrib_colour.setParmTemplateGroup(ptg)

        relative_path = attrib_colour.relativePathTo(out_node)
        expression_parm = f'`chs("{relative_path}/rootprim")`'
        attrib_colour.setParms(
            {"asset_name": expression_parm, "snippet": 's@asset_name = chs("asset_name");'}
        )
        color_node.setParms({"class": 1, "colortype": 4, "rampattribute": "asset_name"})
        attrib_promote.setParms({"inname": "Cd", "inclass": 1, "outclass": 0})
        attrib_delete_name.parm("primdel").set("asset_name")
        name_node.parm("name1").set(expression_parm)

        poly_reduce.setInput(0, remove_points)
        attrib_colour.setInput(0, poly_reduce)
        color_node.setInput(0, attrib_colour)
        attrib_promote.setInput(0, color_node)
        attrib_delete_name.setInput(0, attrib_promote)
        proxy_output.setInput(0, attrib_delete_name)

        python_sop = _create_convex(parent)
        python_sop.setInput(0, remove_points)
        name_node.setInput(0, python_sop)
        sim_output.setInput(0, name_node)
        parent.layoutChildren()
    except Exception as exc:
        if hou.isUIAvailable():
            hou.ui.displayMessage(
                f"An error happened in prepare imported assets: {exc}",
                severity=hou.severityType.Error,
            )
        else:
            raise RuntimeError(f"prepare_imported_asset failed for {name}: {exc}") from exc


def _parse_asset_filename(filename: str) -> tuple[str, str]:
    if filename.endswith(".bgeo.sc"):
        return filename[: -len(".bgeo.sc")], "bgeo.sc"
    parts = filename.rsplit(".", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return filename, ""


def build_geo_and_mtl_variants(
    stage_context,
    node_name: str,
    main_asset_file_path: str,
    asset_variants: list,
    asset_vset_name: str,
    mtl_variants: list,
    folder_textures: str,
    mtl_vset_name: str,
    skip_matchsize: bool = False,
    progress: "ProgressLike | None" = None,
    lowercase_material_names: bool = False,
    use_custom_component_output: bool = True,
    create_geo_variants: bool = True,
    expected_material_names: list[str] | None = None,
):
    naming_config = MaterialNamingConfig.from_ui(lowercase=lowercase_material_names)
    assets = [main_asset_file_path] + (asset_variants or []) if create_geo_variants else [main_asset_file_path]
    has_geo_variants = len(assets) > 1

    if use_custom_component_output:
        comp_out = componentoutput_custom_creation(node_name=_sanitize(node_name))
    else:
        comp_out = stage_context.createNode("componentoutput", _sanitize(node_name))
        comp_out.parm("rootprim").set("/ASSET")

    if has_geo_variants:
        geometry_variants_node = stage_context.createNode("componentgeometryvariants", "geometry_variants")
        if asset_vset_name:
            geometry_variants_node.parm("variantset").set(asset_vset_name)
        nodes_to_layout = [geometry_variants_node, comp_out]

        for index, asset in enumerate(assets):
            if progress and progress.is_cancelled():
                raise KeyboardInterrupt("Cancelled by user")
            path, filename = os.path.split(asset.split(";")[0])
            asset_name, asset_extension = _parse_asset_filename(filename)
            if progress:
                progress.log(f"Creating geometry variant {index + 1}/{len(assets)}: {asset_name}")
            comp_geo = stage_context.createNode("componentgeometry", _sanitize(f"{asset_name}_geo"))
            geometry_variants_node.setInput(index, comp_geo)
            prepare_imported_asset(
                comp_geo,
                _sanitize(asset_name),
                asset_extension,
                path,
                comp_out,
                skip_matchsize=skip_matchsize,
                lowercase_material_names=lowercase_material_names,
            )
            nodes_to_layout.append(comp_geo)
        first_geo_node = geometry_variants_node
    else:
        if progress:
            progress.log("No geometry variants - creating single geometry node")
        path, filename = os.path.split(main_asset_file_path.split(";")[0])
        asset_name, asset_extension = _parse_asset_filename(filename)
        comp_geo = stage_context.createNode("componentgeometry", _sanitize(f"{asset_name}_geo"))
        prepare_imported_asset(
            comp_geo,
            _sanitize(asset_name),
            asset_extension,
            path,
            comp_out,
            skip_matchsize=skip_matchsize,
            lowercase_material_names=lowercase_material_names,
        )
        nodes_to_layout = [comp_geo, comp_out]
        first_geo_node = comp_geo
        geometry_variants_node = comp_geo

    mtl_folders = list(mtl_variants or [])
    if folder_textures:
        mtl_folders.append(folder_textures)

    comp_material_last = None
    for index, mtl_folder in enumerate(mtl_folders):
        if progress and progress.is_cancelled():
            raise KeyboardInterrupt("Cancelled by user")
        mtl_folder_name = os.path.basename(mtl_folder)
        if progress:
            progress.log(
                f"Creating material variant {index + 1}/{len(mtl_folders)} from folder: {mtl_folder_name}"
            )
        material_lib = stage_context.createNode(
            "materiallibrary", _sanitize(f"{node_name}_mtl_{mtl_folder_name}")
        )
        # Stock componentmaterial: it records component:mtl:lastnode, which componentoutput's
        # fetch_mtls needs to write mtl.usdc. The custom subnet did not, so mtl.usdc came out empty.
        comp_material = stage_context.createNode(
            "componentmaterial", _sanitize(f"{node_name}_material_variant_{mtl_folder_name}")
        )
        comp_material.parm("variantset").set(mtl_vset_name or "mtl_variant")
        comp_material.parm("variantname").set(comp_material.name())
        material_lib.parm("matpathprefix").set("/ASSET/mtl/")
        comp_material.setInput(0, first_geo_node if index == 0 else comp_material_last)
        comp_material.setInput(1, material_lib)
        comp_material_last = comp_material

        if expected_material_names is not None:
            material_names = list(expected_material_names)
        else:
            if progress and hasattr(progress, "suspend_events"):
                with progress.suspend_events():
                    material_names = extract_material_names(assets, lowercase=naming_config.lowercase)
            else:
                material_names = extract_material_names(assets, lowercase=naming_config.lowercase)

        if progress:
            if material_names:
                readable_list = "\n".join(f"- {m}" for m in material_names)
                progress.log(
                    f"Using {len(material_names)} material name(s) from geometry:\n{readable_list}"
                )
            else:
                progress.log("No geometry material names; creating materials discovered from textures.")

        create_materials(
            first_geo_node,
            mtl_folder,
            material_lib,
            material_names or None,
            progress=progress,
            naming_config=naming_config,
        )
        _bind_materials_by_mesh_name(comp_material, material_lib)
        nodes_to_layout.extend([material_lib, comp_material])

    if comp_material_last is not None:
        comp_out.setInput(0, comp_material_last)

    return geometry_variants_node, comp_out, nodes_to_layout, comp_material_last
