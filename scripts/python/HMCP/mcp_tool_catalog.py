"""MCP tool catalog for HMCP bridge — schemas only, no Houdini logic."""

from mcp import types

# Each entry: mcp_tool_name -> (houdini_command, description, input_schema)
EXTENDED_TOOLS = {
    "get_node_errors": (
        "get_node_errors",
        "Cook a node (optional) and return errors/warnings",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "cook_first": {"type": "boolean", "default": True},
                "force": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "get_cook_chain": (
        "get_cook_chain",
        "List upstream or downstream node chain from a node",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "direction": {"type": "string", "enum": ["upstream", "downstream", "both"], "default": "upstream"},
                "max_depth": {"type": "integer", "default": 32},
            },
            "required": ["node_path"],
        },
    ),
    "get_parameter_schema": (
        "get_parameter_schema",
        "List parameter names, types, values, and menu items for a node",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "parm_name": {"type": "string", "description": "Optional single parm filter"},
            },
            "required": ["node_path"],
        },
    ),
    "inspect_usd_prim": (
        "inspect_usd_prim",
        "Inspect a USD prim from a cooked LOP node's stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "cook_first": {"type": "boolean", "default": True},
                "max_children": {"type": "integer", "default": 50},
            },
            "required": ["node_path"],
        },
    ),
    "list_usd_prims": (
        "list_usd_prims",
        "List USD prims under a root path from a LOP stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "root_path": {"type": "string", "default": "/"},
                "type_filter": {"type": "string"},
                "max_prims": {"type": "integer", "default": 200},
            },
            "required": ["node_path"],
        },
    ),
    "export_usd_from_lop": (
        "export_usd_from_lop",
        "Export cooked USD stage from a LOP node to a file",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "output_path": {"type": "string"},
            },
            "required": ["node_path", "output_path"],
        },
    ),
    "connect_nodes": (
        "connect_nodes",
        "Connect output_node into input_node at input_index",
        {
            "type": "object",
            "properties": {
                "output_node": {"type": "string"},
                "input_node": {"type": "string"},
                "input_index": {"type": "integer", "default": 0},
            },
            "required": ["output_node", "input_node"],
        },
    ),
    "layout_nodes": (
        "layout_nodes",
        "Auto-layout nodes in a network (parent or explicit list)",
        {
            "type": "object",
            "properties": {
                "parent_path": {"type": "string"},
                "node_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": [],
        },
    ),
    "set_node_flags": (
        "set_node_flags",
        "Set display/render/template/bypass/lock flags on a node",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "display": {"type": "boolean"},
                "render": {"type": "boolean"},
                "template": {"type": "boolean"},
                "bypass": {"type": "boolean"},
                "lock": {"type": "boolean"},
            },
            "required": ["node_path"],
        },
    ),
    "run_batch_lops_build": (
        "run_batch_lops_build",
        "Run multiple LOPs Asset Builder configs from JSON file or inline array",
        {
            "type": "object",
            "properties": {
                "config_filepath": {"type": "string"},
                "configs": {"type": "array", "items": {"type": "object"}},
                "verbose": {"type": "boolean", "default": True},
            },
            "required": [],
        },
    ),
    "build_library_from_parts": (
        "build_library_from_parts",
        "Build KB3D-style USD assembly from part folders (asset_library_builder)",
        {
            "type": "object",
            "properties": {
                "parts_folder": {"type": "string"},
                "asset_name": {"type": "string"},
                "models_folder": {"type": "string"},
                "materials_folder": {"type": "string"},
                "texture_variants": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["parts_folder", "asset_name", "models_folder", "materials_folder"],
        },
    ),
    "capture_viewport": (
        "capture_viewport",
        "Capture active Scene Viewer to PNG (returns base64 image)",
        {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "Optional output PNG path"},
            },
            "required": [],
        },
    ),
    "cook_render_node": (
        "cook_render_node",
        "Cook a ROP/render node (e.g. usdrender_rop) and report output path",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
            },
            "required": ["node_path"],
        },
    ),
    "set_frame_range": (
        "set_frame_range",
        "Set Houdini playbar frame and playback range",
        {
            "type": "object",
            "properties": {
                "start_frame": {"type": "integer", "default": 1},
                "end_frame": {"type": "integer", "default": 120},
            },
            "required": [],
        },
    ),
    "get_server_health": (
        "get_server_health",
        "HMCP/Houdini health snapshot (version, HIP, port, selection)",
        {"type": "object", "properties": {}, "required": []},
    ),
    "get_asset_builder_example": (
        "get_asset_builder_example",
        "Read a LOPs Asset Builder example JSON config from the repo",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "default": "simple_config.json"},
            },
            "required": [],
        },
    ),
    "get_geo_stats": (
        "get_geo_stats",
        "Point/prim counts, bounds, groups, and attributes for a SOP node",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "cook_first": {"type": "boolean", "default": True},
                "force": {"type": "boolean", "default": True},
                "max_attributes": {"type": "integer", "default": 40},
            },
            "required": ["node_path"],
        },
    ),
    "list_material_assignments": (
        "list_material_assignments",
        "List USD material bindings from a cooked LOP stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "root_path": {"type": "string", "default": "/"},
                "max_prims": {"type": "integer", "default": 500},
                "include_unbound": {"type": "boolean", "default": False},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "get_build_output_paths": (
        "get_build_output_paths",
        "Read componentoutput disk paths for publish prep",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string", "description": "componentoutput path; auto-find if omitted"},
            },
            "required": [],
        },
    ),
    "scan_to_lops_config": (
        "scan_to_lops_config",
        "Scan asset folder and return ready LOPs Asset Builder config dict",
        {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string"},
                "geo_subfolder": {"type": "string", "default": "geo"},
                "tex_subfolder": {"type": "string", "default": "tex"},
                "asset_name": {"type": "string"},
                "create_lookdev": {"type": "boolean", "default": False},
            },
            "required": ["folder_path"],
        },
    ),
    "discover_usd_assets": (
        "discover_usd_assets",
        "Crawl a library folder for primary USD assets (headless discovery rules)",
        {
            "type": "object",
            "properties": {
                "root_path": {"type": "string"},
                "mode": {"type": "string", "enum": ["primary", "all", "glob"], "default": "primary"},
                "recursive": {"type": "boolean", "default": True},
                "max_items": {"type": "integer", "default": 200},
            },
            "required": ["root_path"],
        },
    ),
    "search_assets": (
        "search_assets",
        "Search USD assets under a library root by name or path substring",
        {
            "type": "object",
            "properties": {
                "root_path": {"type": "string"},
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 50},
            },
            "required": ["root_path"],
        },
    ),
    "get_asset_categories": (
        "get_asset_categories",
        "Group discovered USD assets by folder, KB3D code, or extension",
        {
            "type": "object",
            "properties": {
                "root_path": {"type": "string"},
                "group_by": {"type": "string", "enum": ["parent_folder", "kb3d_code", "extension"], "default": "parent_folder"},
                "max_per_category": {"type": "integer", "default": 20},
            },
            "required": ["root_path"],
        },
    ),
    "import_asset": (
        "import_asset",
        "Scan folder and import geometry as USD references in /stage",
        {
            "type": "object",
            "properties": {
                "folder_path": {"type": "string"},
                "geo_subfolder": {"type": "string", "default": "geo"},
                "tex_subfolder": {"type": "string", "default": "tex"},
                "stage_name": {"type": "string", "default": "hmcp_asset_import"},
                "spacing": {"type": "number", "default": 5.0},
                "layout_type": {"type": "string", "enum": ["grid", "line", "circular"], "default": "grid"},
            },
            "required": ["folder_path"],
        },
    ),
    "render_karma_preview": (
        "render_karma_preview",
        "Render Karma preview from a LOP node; returns PNG image",
        {
            "type": "object",
            "properties": {
                "lop_node_path": {"type": "string"},
                "parent_path": {"type": "string", "default": "/stage"},
                "render_node_path": {"type": "string"},
                "frame": {"type": "integer"},
                "resolution": {"type": "array", "items": {"type": "integer"}, "default": [1024, 1024]},
                "psx_preset": {"type": "boolean", "default": False},
                "create_if_missing": {"type": "boolean", "default": True},
                "output_path": {"type": "string"},
            },
            "required": [],
        },
    ),
    "apply_psx_karma": (
        "apply_psx_karma",
        "Apply PSX low-res Karma render settings to a karmarenderproperties node",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "render_resolution": {"type": "array", "items": {"type": "integer"}},
            },
            "required": [],
        },
    ),
    "get_usd_stage_info": (
        "get_usd_stage_info",
        "USD stage metadata — defaultPrim, upAxis, metersPerUnit, prim counts",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "inspect_usd_attribute": (
        "inspect_usd_attribute",
        "Read one or all attributes on a USD prim from a cooked LOP",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "attribute_name": {"type": "string"},
                "time_code": {"type": "number"},
                "max_attributes": {"type": "integer", "default": 100},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "get_usd_bounding_box": (
        "get_usd_bounding_box",
        "World-space bounding box for a USD prim on a cooked LOP stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "purpose": {"type": "string", "enum": ["default", "render", "proxy", "guide"], "default": "default"},
                "time_code": {"type": "number"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "get_usd_layer_stack": (
        "get_usd_layer_stack",
        "Root sublayers, references, payloads, and prim stack for a prim",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "list_variant_sets": (
        "list_variant_sets",
        "List variant sets, available variants, and current selection on a prim",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "set_variant_selection": (
        "set_variant_selection",
        "Set USD variant on session layer or create a Set Variant LOP",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string", "default": "/"},
                "variant_set": {"type": "string"},
                "variant_name": {"type": "string"},
                "mode": {"type": "string", "enum": ["session", "create_lop"], "default": "session"},
                "parent_path": {"type": "string", "default": "/stage"},
                "input_node_path": {"type": "string"},
            },
            "required": ["variant_set", "variant_name"],
        },
    ),
    "create_usd_reference_lop": (
        "create_usd_reference_lop",
        "Create a Solaris reference LOP pointing at a USD file on disk",
        {
            "type": "object",
            "properties": {
                "usd_path": {"type": "string"},
                "parent_path": {"type": "string", "default": "/stage"},
                "input_node_path": {"type": "string"},
                "prim_path": {"type": "string"},
                "reference_type": {"type": "string", "enum": ["reference", "reference::2.0"], "default": "reference"},
                "node_name": {"type": "string"},
            },
            "required": ["usd_path"],
        },
    ),
    "set_default_prim": (
        "set_default_prim",
        "Set stage defaultPrim via session edit or Configure Layer LOP",
        {
            "type": "object",
            "properties": {
                "default_prim": {"type": "string"},
                "node_path": {"type": "string"},
                "mode": {"type": "string", "enum": ["session", "create_lop"], "default": "session"},
                "parent_path": {"type": "string", "default": "/stage"},
                "input_node_path": {"type": "string"},
            },
            "required": ["default_prim"],
        },
    ),
    "validate_usd_file": (
        "validate_usd_file",
        "Validate a USD file on disk (pxr checks + optional usdchecker)",
        {
            "type": "object",
            "properties": {
                "usd_path": {"type": "string"},
                "run_usdchecker": {"type": "boolean", "default": True},
            },
            "required": ["usd_path"],
        },
    ),
    "setup_karma_usd_publish_chain": (
        "setup_karma_usd_publish_chain",
        "Create Karma → USD ROP → Sublayer/Reference publish stack on /stage",
        {
            "type": "object",
            "properties": {
                "parent_path": {"type": "string", "default": "/stage"},
                "input_node_path": {"type": "string"},
                "name_prefix": {"type": "string", "default": "publish"},
                "import_mode": {"type": "string", "enum": ["sublayer", "reference"], "default": "sublayer"},
                "picture": {"type": "string"},
                "lop_output": {"type": "string"},
                "resolution": {"type": "array", "items": {"type": "integer"}},
                "prim_path": {"type": "string"},
            },
            "required": [],
        },
    ),
    "version_up_usd_output": (
        "version_up_usd_output",
        "Duplicate USD ROP/componentoutput with incremented _v### suffix",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "create_import_lop": {"type": "boolean", "default": False},
                "import_mode": {"type": "string", "enum": ["sublayer", "reference"], "default": "sublayer"},
            },
            "required": ["node_path"],
        },
    ),
    "extract_usd_cameras": (
        "extract_usd_cameras",
        "Create Solaris camera LOPs from USD camera prims on a cooked stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "parent_path": {"type": "string", "default": "/stage"},
                "name_prefix": {"type": "string", "default": "usd_cam"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "extract_usdz_archive": (
        "extract_usdz_archive",
        "Extract USDZ zip archive for texture/USD access",
        {
            "type": "object",
            "properties": {
                "usdz_path": {"type": "string"},
                "extract_to": {"type": "string"},
                "max_files": {"type": "integer", "default": 50},
            },
            "required": ["usdz_path"],
        },
    ),
    "analyze_usd_materials": (
        "analyze_usd_materials",
        "List USD materials, bindings, and texture maps from a LOP stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "max_materials": {"type": "integer", "default": 100},
                "naming_strategy": {
                    "type": "string",
                    "enum": ["usd_prim", "shop_materialpath", "usdmaterialpath", "subset", "prim_name"],
                    "default": "usd_prim",
                },
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "import_usd_materials": (
        "import_usd_materials",
        "Rebuild USD materials as Material Library + Assign Material LOPs",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "parent_path": {"type": "string", "default": "/stage"},
                "max_materials": {"type": "integer", "default": 20},
                "engine": {"type": "string", "enum": ["mtlx", "openpbr"], "default": "mtlx"},
                "naming_strategy": {"type": "string", "default": "usd_prim"},
                "assign_all": {"type": "boolean", "default": True},
                "dry_run": {"type": "boolean", "default": False},
                "build_empty": {"type": "boolean", "default": False},
                "wire_source": {"type": "boolean", "default": True},
            },
            "required": ["node_path"],
        },
    ),
    "list_component_variants": (
        "list_component_variants",
        "List geo/mtl variant sets on a componentoutput cooked stage",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "prim_path": {"type": "string"},
                "cook_first": {"type": "boolean", "default": True},
            },
            "required": [],
        },
    ),
    "batch_export_variants": (
        "batch_export_variants",
        "Export USD files for geo × mtl variant combinations with manifest JSON",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "output_dir": {"type": "string"},
                "geo_variant_set": {"type": "string"},
                "mtl_variant_set": {"type": "string"},
                "geo_variants": {"type": "array", "items": {"type": "string"}},
                "mtl_variants": {"type": "array", "items": {"type": "string"}},
                "version": {"type": "string", "default": "v001"},
            },
            "required": ["output_dir"],
        },
    ),
    "get_variant_manifest": (
        "get_variant_manifest",
        "Read variant export manifest JSON (or run batch export first)",
        {
            "type": "object",
            "properties": {
                "manifest_path": {"type": "string"},
                "node_path": {"type": "string"},
                "output_dir": {"type": "string"},
            },
            "required": [],
        },
    ),
    "repair_texture_paths": (
        "repair_texture_paths",
        "Find/repair broken USD texture paths using folder search roots",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "textures": {"type": "object"},
                "folder_textures": {"type": "string"},
                "search_roots": {"type": "array", "items": {"type": "string"}},
                "copy_to": {"type": "string"},
            },
            "required": [],
        },
    ),
    "compare_material_manifests": (
        "compare_material_manifests",
        "Compare folder texture scan vs USD-extracted material textures",
        {
            "type": "object",
            "properties": {
                "node_path": {"type": "string"},
                "folder_textures": {"type": "string"},
                "material_name": {"type": "string"},
                "naming_strategy": {"type": "string", "default": "usd_prim"},
            },
            "required": ["node_path", "folder_textures"],
        },
    ),
}


def build_extended_tool_types() -> list:
    tools = []
    for mcp_name, (_cmd, description, schema) in EXTENDED_TOOLS.items():
        tools.append(types.Tool(name=mcp_name, description=description, inputSchema=schema))
    return tools


def extended_command_map() -> dict:
    return {name: entry[0] for name, entry in EXTENDED_TOOLS.items()}
