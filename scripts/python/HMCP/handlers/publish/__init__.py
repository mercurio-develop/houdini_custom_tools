"""Publish, variant export, and texture repair handlers."""

from HMCP.handlers.publish.prep import get_build_output_paths, scan_to_lops_config
from HMCP.handlers.publish.solaris import (
    extract_usd_cameras,
    setup_karma_usd_publish_chain,
    version_up_usd_output,
)
from HMCP.handlers.publish.textures import compare_material_manifests, repair_texture_paths
from HMCP.handlers.publish.variants import (
    batch_export_variants,
    get_variant_manifest,
    list_component_variants,
)

COMMANDS = {
    "setup_karma_usd_publish_chain": setup_karma_usd_publish_chain,
    "version_up_usd_output": version_up_usd_output,
    "extract_usd_cameras": extract_usd_cameras,
    "list_component_variants": list_component_variants,
    "batch_export_variants": batch_export_variants,
    "get_variant_manifest": get_variant_manifest,
    "repair_texture_paths": repair_texture_paths,
    "compare_material_manifests": compare_material_manifests,
    "scan_to_lops_config": scan_to_lops_config,
    "get_build_output_paths": get_build_output_paths,
}

__all__ = list(COMMANDS.keys())
