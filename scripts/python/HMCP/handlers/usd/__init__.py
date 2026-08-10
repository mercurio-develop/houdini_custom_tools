"""USD / Solaris inspection and material handlers."""

from HMCP.handlers.usd.bindings import list_material_assignments
from HMCP.handlers.usd.inspection import export_usd_from_lop, inspect_usd_prim, list_usd_prims
from HMCP.handlers.usd.materials import (
    analyze_usd_materials,
    extract_usdz_archive,
    import_usd_materials,
)
from HMCP.handlers.usd.solaris import (
    create_usd_reference_lop,
    get_usd_bounding_box,
    get_usd_layer_stack,
    get_usd_stage_info,
    inspect_usd_attribute,
    list_variant_sets,
    set_default_prim,
    set_variant_selection,
    validate_usd_file,
)

COMMANDS = {
    "inspect_usd_prim": inspect_usd_prim,
    "list_usd_prims": list_usd_prims,
    "export_usd_from_lop": export_usd_from_lop,
    "list_material_assignments": list_material_assignments,
    "get_usd_stage_info": get_usd_stage_info,
    "inspect_usd_attribute": inspect_usd_attribute,
    "get_usd_bounding_box": get_usd_bounding_box,
    "get_usd_layer_stack": get_usd_layer_stack,
    "list_variant_sets": list_variant_sets,
    "set_variant_selection": set_variant_selection,
    "create_usd_reference_lop": create_usd_reference_lop,
    "set_default_prim": set_default_prim,
    "validate_usd_file": validate_usd_file,
    "extract_usdz_archive": extract_usdz_archive,
    "analyze_usd_materials": analyze_usd_materials,
    "import_usd_materials": import_usd_materials,
}

__all__ = list(COMMANDS.keys())
