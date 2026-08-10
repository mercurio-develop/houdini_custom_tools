"""
Material Validator - Validate materials and warn about missing textures

Checks if geometry files have material assignments that can't be satisfied
by the available texture folders, and provides detailed warnings to users.
"""

import os
from typing import List, Set, Tuple

import hou
from modules.misc_utils import slugify, MaterialNamingConfig
from tools.lops_asset_builder_v3.texture_variant_detector import TextureVariantDetector
from tools.lops_asset_builder_v3.texture_scan_utils import (
    resolve_texture_search_roots,
    walk_texture_dirs,
)

# Formats safe to load with hou.Geometry during pre-build validation
_HOU_GEOMETRY_EXTENSIONS = frozenset({
    ".bgeo", ".bgeo.sc", ".obj", ".ply", ".stl", ".off", ".dxf",
})
_USD_EXTENSIONS = frozenset({".usd", ".usda", ".usdc"})
# Skip in-memory geometry loads above this size during pre-flight validation
_MAX_VALIDATION_GEO_BYTES = 256 * 1024 * 1024
_TEXTURE_MATERIAL_CACHE: dict[tuple[str, bool], frozenset[str]] = {}


def _asset_extension(asset_path: str) -> str:
    lower = asset_path.lower()
    if lower.endswith(".bgeo.sc"):
        return ".bgeo.sc"
    return os.path.splitext(lower)[1]


def _normalize_material_name(material_path: str, lowercase: bool) -> str:
    material_name = os.path.basename(material_path or "")
    if not material_name:
        return ""
    if lowercase:
        material_name = material_name.lower().replace(" ", "_")
    else:
        material_name = material_name.replace(" ", "_")
    material_name = slugify(material_name, lowercase=lowercase).strip("_")
    return material_name


def _extract_materials_from_hou_geometry(asset_path: str, lowercase: bool) -> Set[str]:
    material_names: Set[str] = set()
    geo = hou.Geometry()
    geo.loadFromFile(asset_path)

    shop_attrib = geo.findPrimAttrib("shop_materialpath")
    if shop_attrib:
        for prim in geo.prims():
            material_path = prim.stringAttribValue(shop_attrib)
            material_name = _normalize_material_name(material_path, lowercase)
            if material_name:
                material_names.add(material_name)

    binding_attrib = geo.findPrimAttrib("material:binding")
    if binding_attrib:
        for prim in geo.prims():
            material_path = prim.stringAttribValue(binding_attrib)
            material_name = _normalize_material_name(material_path, lowercase)
            if material_name:
                material_names.add(material_name)

    return material_names


def _extract_materials_from_usd(asset_path: str, lowercase: bool) -> Set[str]:
    material_names: Set[str] = set()
    try:
        from pxr import Usd, UsdShade
    except ImportError:
        return material_names

    stage = Usd.Stage.Open(asset_path)
    if not stage:
        return material_names

    for prim in stage.Traverse():
        if not prim.IsValid():
            continue
        binding_api = UsdShade.MaterialBindingAPI(prim)
        if not binding_api:
            continue
        material, _relationship = binding_api.ComputeBoundMaterial()
        if material:
            material_name = _normalize_material_name(material.GetPath().path.split("/")[-1], lowercase)
            if material_name:
                material_names.add(material_name)

    return material_names


class MaterialValidationResult:
    """Result of material validation."""

    def __init__(self):
        self.materials_expected: Set[str] = set()  # Materials found in geometry
        self.materials_available: Set[str] = set()  # Materials found in textures
        self.materials_missing: Set[str] = set()    # Expected but not available
        self.has_warnings: bool = False
        self.warnings: List[str] = []
        self.info: List[str] = []

    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
        self.has_warnings = True

    def add_info(self, message: str):
        """Add an info message."""
        self.info.append(message)

    def get_summary(self) -> str:
        """Get a formatted summary of validation results."""
        lines = []
        lines.append("=" * 70)
        lines.append("MATERIAL VALIDATION REPORT")
        lines.append("=" * 70)

        # Statistics
        lines.append(f"\nMaterials expected (from geometry): {len(self.materials_expected)}")
        lines.append(f"Materials available (from textures): {len(self.materials_available)}")
        lines.append(f"Materials missing: {len(self.materials_missing)}")

        # Missing materials detail
        if self.materials_missing:
            lines.append(f"\n⚠️  MISSING MATERIALS ({len(self.materials_missing)}):")
            for mat in sorted(self.materials_missing):
                lines.append(f"   ❌ {mat}")

        # Available materials
        if self.materials_available:
            lines.append(f"\n✓ AVAILABLE MATERIALS ({len(self.materials_available)}):")
            for mat in sorted(self.materials_available):
                lines.append(f"   ✓ {mat}")

        # Warnings
        if self.warnings:
            lines.append(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                lines.append(f"   • {warning}")

        # Info
        if self.info:
            lines.append(f"\nℹ️  INFORMATION:")
            for info in self.info:
                lines.append(f"   • {info}")

        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

    def get_html_summary(self) -> str:
        """Get HTML formatted summary for Qt dialogs."""
        lines = []
        lines.append("<h3>Material Validation Report</h3>")

        # Statistics
        lines.append("<table border='0' cellpadding='3'>")
        lines.append(f"<tr><td><b>Materials expected:</b></td><td>{len(self.materials_expected)}</td></tr>")
        lines.append(f"<tr><td><b>Materials available:</b></td><td>{len(self.materials_available)}</td></tr>")
        lines.append(f"<tr><td><b>Materials missing:</b></td><td style='color: red;'><b>{len(self.materials_missing)}</b></td></tr>")
        lines.append("</table>")

        # Missing materials
        if self.materials_missing:
            lines.append(f"<h4 style='color: orange;'>⚠️ Missing Materials ({len(self.materials_missing)}):</h4>")
            lines.append("<ul style='color: red;'>")
            for mat in sorted(self.materials_missing):
                lines.append(f"<li><b>{mat}</b></li>")
            lines.append("</ul>")

        # Warnings
        if self.warnings:
            lines.append(f"<h4 style='color: orange;'>⚠️ Warnings:</h4>")
            lines.append("<ul>")
            for warning in self.warnings:
                lines.append(f"<li>{warning}</li>")
            lines.append("</ul>")

        return "".join(lines)


def extract_material_names_from_geometry(
    asset_paths: List[str],
    lowercase: bool = False,
    progress=None,
) -> Set[str]:
    """Extract material names from geometry files without unsafe loaders."""
    material_names: Set[str] = set()

    for asset_path in asset_paths:
        asset_path = asset_path.strip()
        if not asset_path or not os.path.exists(asset_path):
            continue

        ext = _asset_extension(asset_path)
        try:
            if ext in _HOU_GEOMETRY_EXTENSIONS:
                if os.path.getsize(asset_path) > _MAX_VALIDATION_GEO_BYTES:
                    continue
                if progress is not None:
                    try:
                        progress.log(f"Reading geometry materials: {os.path.basename(asset_path)}")
                    except Exception:
                        pass
                if progress is not None and hasattr(progress, "suspend_events"):
                    with progress.suspend_events():
                        material_names.update(
                            _extract_materials_from_hou_geometry(asset_path, lowercase)
                        )
                else:
                    material_names.update(_extract_materials_from_hou_geometry(asset_path, lowercase))
            elif ext in _USD_EXTENSIONS:
                if progress is not None:
                    try:
                        progress.log(f"Reading USD materials: {os.path.basename(asset_path)}")
                    except Exception:
                        pass
                material_names.update(_extract_materials_from_usd(asset_path, lowercase))
        except Exception:
            continue

    return material_names


def find_available_materials_in_textures(
    texture_folder: str,
    lowercase: bool = False,
    progress=None,
) -> Set[str]:
    """Scan texture folders using the same headless scanner as the builder."""
    if not texture_folder:
        return set()

    cache_key = (os.path.normpath(texture_folder), bool(lowercase))
    cached = _TEXTURE_MATERIAL_CACHE.get(cache_key)
    if cached is not None:
        return set(cached)

    from tools.material_tools.TexToMtlX_V2.tex_to_mtlx import TextureFolderScanner
    from modules.misc_utils import MaterialNamingConfig

    naming_config = MaterialNamingConfig.from_ui(lowercase=lowercase)
    scanner = TextureFolderScanner(naming_config)
    material_names: Set[str] = set()

    dir_count = 0
    for search_root in resolve_texture_search_roots(texture_folder):
        if not search_root or not os.path.isdir(search_root):
            continue
        for root, _dirs, _files in walk_texture_dirs(search_root):
            dir_count += 1
            if progress is not None and dir_count % 40 == 0:
                try:
                    progress.log(f"Scanning textures… ({dir_count} folders checked)")
                    if progress.is_cancelled():
                        break
                except Exception:
                    pass
            if not scanner.folder_with_textures(root):
                continue
            details = scanner.get_texture_details(root)
            material_names.update(details.keys())

    _TEXTURE_MATERIAL_CACHE[cache_key] = frozenset(material_names)
    return material_names


def validate_materials(
    asset_paths: List[str],
    texture_folder: str,
    texture_variants: List[str] = None,
    lowercase: bool = False,
    naming_config: MaterialNamingConfig = None,
    skip_geometry_scan: bool = False,
    progress=None,
) -> MaterialValidationResult:
    """
    Validate that geometry materials can be satisfied by available textures.

    Args:
        asset_paths: List of geometry file paths
        texture_folder: Path to main texture folder
        texture_variants: Optional list of texture variant folders (e.g., ["4k", "2k"])
        lowercase: If True, convert material names to lowercase (deprecated, use naming_config)
        naming_config: Material naming configuration (preferred over lowercase param)

    Returns:
        MaterialValidationResult with detailed validation info
    """
    # Use naming_config if provided, otherwise create from lowercase param
    if naming_config is None:
        naming_config = MaterialNamingConfig.from_ui(lowercase=lowercase)

    result = MaterialValidationResult()

    # Extract expected materials from geometry (optional — skipped in GUI to avoid
    # hou.Geometry.loadFromFile before the progress window, which crashes H22).
    if skip_geometry_scan:
        result.add_info("Skipping geometry material scan (texture folder validation only)")
    else:
        result.add_info(f"Scanning {len(asset_paths)} geometry file(s)...")
        if progress is not None:
            try:
                progress.step("Scanning geometry for materials")
            except Exception:
                pass
        result.materials_expected = extract_material_names_from_geometry(
            asset_paths, lowercase=naming_config.lowercase, progress=progress
        )
        if progress is not None and hasattr(progress, "flush_ui"):
            try:
                progress.flush_ui()
            except Exception:
                pass

        if not result.materials_expected:
            result.add_info("No material assignments found in geometry files")
            result.add_info("Geometry has no shop_materialpath or material:binding attributes")
            # Continue to texture scan — materials may still be created from textures.

    if not skip_geometry_scan and not result.materials_expected:
        return result

    # Find available materials in textures
    if not os.path.exists(texture_folder):
        result.add_warning(f"Texture folder does not exist: {texture_folder}")
        result.add_warning("Template materials will be created instead")
        result.materials_missing = result.materials_expected.copy()
        return result

    # Scan main texture folder (resolved roots avoid walking geo/ in KB3D libraries)
    resolved_roots = resolve_texture_search_roots(texture_folder)
    scan_label = resolved_roots[0] if resolved_roots else texture_folder
    result.add_info(f"Scanning texture folder: {scan_label}")
    if progress is not None:
        try:
            progress.step("Scanning texture folders")
        except Exception:
            pass
    result.materials_available = find_available_materials_in_textures(
        texture_folder, lowercase=naming_config.lowercase, progress=progress
    )

    # Detect variant folders from the Textures parent when rooted at png4k/jpg4k
    variant_scan_root = texture_folder
    if resolved_roots:
        variant_scan_root = os.path.dirname(resolved_roots[0])
        if os.path.basename(variant_scan_root).lower() != "textures":
            variant_scan_root = texture_folder

    if not texture_variants:
        detector = TextureVariantDetector()
        detected_variants = detector.detect_variants(variant_scan_root)
        if detected_variants:
            result.add_info(f"Auto-detected {len(detected_variants)} texture variant folder(s)")
            for variant in detected_variants:
                result.add_info(f"  Found variant: {variant.folder_name} ({variant.variant_key})")
            texture_variants = [v.folder_name for v in detected_variants]

    # Scan variant folders
    if texture_variants:
        for variant in texture_variants:
            # Handle both folder names and full paths
            if os.path.isabs(variant):
                variant_path = variant
            else:
                variant_path = os.path.join(texture_folder, variant)

            if os.path.exists(variant_path) and os.path.isdir(variant_path):
                result.add_info(f"Scanning variant folder: {os.path.basename(variant_path)}")
                variant_materials = find_available_materials_in_textures(
                    variant_path, lowercase=naming_config.lowercase, progress=progress
                )
                result.materials_available.update(variant_materials)

    # Identify missing materials
    result.materials_missing = result.materials_expected - result.materials_available

    # Generate warnings
    if result.materials_missing:
        result.add_warning(f"{len(result.materials_missing)} material(s) referenced in geometry have no matching textures")
        result.add_warning("Missing materials will use fallback template shaders")

        if len(result.materials_missing) <= 10:
            for mat in sorted(result.materials_missing):
                result.add_warning(f"  Missing: {mat}")

    # Generate info messages
    if result.materials_available:
        result.add_info(f"Found {len(result.materials_available)} material set(s) in textures")
        result.add_info(f"{len(result.materials_expected - result.materials_missing)} material(s) will be created successfully")

    return result


def validate_and_warn_user(
    asset_paths: List[str],
    texture_folder: str,
    texture_variants: List[str] = None,
    show_dialog: bool = True,
    lowercase: bool = False,
    naming_config: MaterialNamingConfig = None,
    skip_geometry_scan: bool = False,
    progress=None,
) -> Tuple[MaterialValidationResult, bool]:
    """
    Validate materials and optionally show warning dialog to user.

    Args:
        asset_paths: List of geometry file paths
        texture_folder: Path to texture folder
        texture_variants: Optional list of texture variant folders
        show_dialog: If True, show Qt warning dialog when issues found
        lowercase: If True, convert material names to lowercase (deprecated, use naming_config)
        naming_config: Material naming configuration (preferred over lowercase param)

    Returns:
        Tuple of (MaterialValidationResult, user_wants_to_continue)
    """
    # Use naming_config if provided, otherwise create from lowercase param
    if naming_config is None:
        naming_config = MaterialNamingConfig.from_ui(lowercase=lowercase)

    result = validate_materials(
        asset_paths,
        texture_folder,
        texture_variants,
        naming_config=naming_config,
        skip_geometry_scan=skip_geometry_scan,
        progress=progress,
    )

    # Print to console
    print(result.get_summary())

    # Show dialog if requested and there are warnings (native Houdini UI — safe with no Qt progress open)
    if show_dialog and result.has_warnings:
        try:
            summary = result.get_summary()
            missing_count = len(result.materials_missing)
            message = (
                f"Material validation found {missing_count} missing material(s).\n\n"
                "Some materials referenced in geometry don't have matching texture files.\n"
                "These materials will use fallback template shaders.\n\n"
                "Continue with the build?"
            )
            choice = hou.ui.displayMessage(
                message,
                buttons=("Continue", "Cancel"),
                severity=hou.severityType.Warning,
                default_choice=0,
                close_choice=1,
                help=summary,
                title="Material Validation Warning",
            )
            user_continues = choice == 0
            return result, user_continues

        except Exception as e:
            print(f"Warning: Could not show validation dialog: {e}")
            return result, True

    return result, True


# Example usage
if __name__ == "__main__":
    # Test validation
    test_assets = [
        "/path/to/asset.abc"
    ]
    test_textures = "/path/to/textures"

    result = validate_materials(test_assets, test_textures)
    print(result.get_summary())
