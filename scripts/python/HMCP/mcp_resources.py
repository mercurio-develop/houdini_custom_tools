"""Static MCP resources and prompts served by the HMCP bridge (no Houdini required)."""

from __future__ import annotations

import os

from mcp import types

# hmcp:// URI -> relative path under CUSTOM_TOOLS root
DOC_RESOURCES = {
    "hmcp://docs/pipeline-dev": {
        "name": "Pipeline Dev Playbook",
        "description": "HMCP edit-test loop and tool selection guide",
        "relative_path": "scripts/python/HMCP/PIPELINE_DEV.md",
        "mime": "text/markdown",
    },
    "hmcp://docs/lops-asset-builder": {
        "name": "LOPs Asset Builder Examples",
        "description": "Example JSON configs for LOPs Asset Builder v3",
        "relative_path": "scripts/python/tools/lops_asset_builder_v3/examples/simple_config.json",
        "mime": "application/json",
    },
    "hmcp://docs/psx-config-schema": {
        "name": "PSX Tools Config Reference",
        "description": "PSX retro tools configuration fields",
        "relative_path": "scripts/python/tools/psx_tools/psx_config.py",
        "mime": "text/x-python",
    },
    "hmcp://docs/agents": {
        "name": "Agent Context (compressed)",
        "description": "Compressed agent context for HMCP workflows",
        "relative_path": "docs/mempalace.md",
        "mime": "text/markdown",
    },
}

WORKFLOW_PROMPTS = {
    "asset-build-workflow": {
        "name": "LOPs Asset Build Workflow",
        "description": "Validate, build, inspect, and organize a USD asset via HMCP",
        "text": """You are building a USD asset in Houdini using custom_tools HMCP.

Follow this sequence:
1. scan_asset_folder — confirm geo/tex layout
2. validate_asset_folder — fix material issues before build
3. get_asset_builder_example or read existing build JSON
4. run_lops_asset_builder — single asset build
5. get_stage_summary — locate component output nodes
6. cook_node on the output LOP
7. inspect_usd_prim or list_usd_prims on the cooked stage
8. organize_lop_network — tidy the graph

Use reload_custom_tools after any Python code edits in custom_tools.
Prefer get_stage_summary over unfiltered get_scene_info on large HIPs.""",
    },
    "psx-retro-workflow": {
        "name": "PSX Retro Asset Workflow",
        "description": "Run PSX dither/decimate pipeline on top of LOPs Asset Builder",
        "text": """You are running the PSX retro pipeline in Houdini via HMCP.

Follow this sequence:
1. validate_asset_folder — textures and materials ready
2. run_psx_asset_build with main_asset_file_path, folder_textures, asset_name, and psx options
3. get_stage_summary — find output nodes
4. cook_node on PSX output
5. capture_viewport for visual QA

PSX options include decimate_ratio, triangulate, process_textures, palette_size, apply_vertex_wobble.
Use reload_custom_tools after editing psx_tools modules.""",
    },
    "debug-node-workflow": {
        "name": "Debug Node Cook Errors",
        "description": "Trace cook failures and parameter issues on a Houdini node",
        "text": """Debug a problematic Houdini node using HMCP inspection tools.

1. get_node_errors with cook_first=true on the failing node
2. get_cook_chain direction=upstream to find the first bad ancestor
3. get_parameter_schema on suspect nodes
4. For LOP nodes: inspect_usd_prim at / after cook
5. execute_code only for one-off checks — prefer typed tools

Report errors, warnings, and the upstream chain clearly.""",
    },
    "publish-prep-workflow": {
        "name": "Publish Prep Workflow",
        "description": "Collect output paths and validate materials before delivery",
        "text": """Prepare a LOPs Asset Builder result for publish via HMCP.

1. get_stage_summary — find componentoutput node
2. get_build_output_paths — read lopoutput, geo/mtl/payload layers
3. list_material_assignments — confirm materials bound on stage
4. cook_node on component output
5. export_usd_from_lop if disk file needed
6. validate_usd_file on exported paths

Use scan_to_lops_config before building if starting from a raw asset folder.""",
    },
    "usd-solaris-workflow": {
        "name": "USD / Solaris Deep Inspection",
        "description": "Inspect composition, variants, bounds, and validate exported USD",
        "text": """Work with USD / Solaris in Houdini using HMCP depth tools.

Inspection flow on a cooked LOP:
1. get_usd_stage_info — defaultPrim, upAxis, metersPerUnit, prim counts
2. list_usd_prims or inspect_usd_prim — navigate the stage
3. get_usd_layer_stack — sublayers, references, payloads, prim stack
4. list_variant_sets — geo/mtl variant options
5. list_material_assignments — material bindings
6. inspect_usd_attribute — read specific attributes (transforms, custom data)
7. get_usd_bounding_box — layout / scale checks

Authoring flow:
1. create_usd_reference_lop — pull payload/geo USD into /stage
2. set_variant_selection — switch geo/mtl variants (session or Set Variant LOP)
3. set_default_prim — fix export metadata before publish
4. export_usd_from_lop — write cooked stage to disk
5. validate_usd_file — run pxr + usdchecker checks on exported file

Prefer typed USD tools over execute_code for stage inspection.""",
    },
    "solaris-publish-workflow": {
        "name": "Solaris Publish Workflow",
        "description": "Karma render, USD export, and validation for publish prep",
        "text": """Publish a Solaris asset using HMCP publish tools.

1. get_stage_summary — find componentoutput node
2. get_build_output_paths — read deliverable disk paths
3. render_karma_preview on the cooked LOP output
4. export_usd_from_lop — write cooked stage to disk if needed
5. validate_usd_file on exported paths
6. analyze_usd_materials — confirm material/texture manifest

For variant deliverables: use variant-export-workflow instead.
See docs/HMCP_TOOLS.md for the canonical tool list.""",
    },
    "variant-export-workflow": {
        "name": "Variant Export Workflow",
        "description": "Export geo × material variant USD matrix from componentoutput",
        "text": """Export LOPs Asset Builder variants to disk via HMCP.

1. get_stage_summary — locate componentoutput node
2. list_component_variants — read geo/mtl variant sets
3. compare_material_manifests — folder textures vs USD extraction
4. batch_export_variants — write geo×mtl USD files + manifest JSON
5. validate_usd_file on each export (or sample)
6. get_variant_manifest — read manifest for delivery tracking

Use repair_texture_paths if analyze_usd_materials shows missing textures.""",
    },
}


def custom_tools_root() -> str:
    env_root = os.environ.get("CUSTOM_TOOLS")
    if env_root and os.path.isdir(env_root):
        return env_root
    # HMCP lives at $CUSTOM_TOOLS/scripts/python/HMCP
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def resolve_resource_path(uri: str) -> tuple[str, str]:
    """Return (absolute_path, mime) for a resource URI."""
    entry = DOC_RESOURCES.get(uri)
    if not entry:
        raise ValueError(f"Unknown resource: {uri}")
    abs_path = os.path.join(custom_tools_root(), entry["relative_path"])
    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Resource file missing: {abs_path}")
    return abs_path, entry["mime"]


def list_resource_types() -> list[types.Resource]:
    resources = []
    for uri, meta in DOC_RESOURCES.items():
        resources.append(
            types.Resource(
                uri=uri,
                name=meta["name"],
                description=meta["description"],
                mimeType=meta["mime"],
            )
        )
    return resources


def read_resource_content(uri: str) -> types.TextResourceContents | types.BlobResourceContents:
    abs_path, mime = resolve_resource_path(uri)
    with open(abs_path, encoding="utf-8") as handle:
        text = handle.read()
    return types.TextResourceContents(uri=uri, mimeType=mime, text=text)


def list_prompt_types() -> list[types.Prompt]:
    prompts = []
    for slug, meta in WORKFLOW_PROMPTS.items():
        prompts.append(
            types.Prompt(
                name=slug,
                description=meta["description"],
                arguments=[],
            )
        )
    return prompts


def get_prompt_messages(name: str) -> list[types.PromptMessage]:
    entry = WORKFLOW_PROMPTS.get(name)
    if not entry:
        raise ValueError(f"Unknown prompt: {name}")
    return [
        types.PromptMessage(
            role="user",
            content=types.TextContent(type="text", text=entry["text"]),
        )
    ]
