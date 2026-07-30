"""
KB3D Assembly Scanner and Reconstructor - Complete Workflow

This script demonstrates the complete workflow for:
1. Scanning source parts from decomposed FBX/BGEO exports
2. Analyzing production assemblies to extract transform data
3. Creating mapping between source and production
4. Reconstructing production assemblies from source parts

Author: Custom Tools
Date: 2025
"""

from pathlib import Path
import sys
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kb3d_assembly_scanner import (
    KB3DAssemblyScanner,
    KB3DSourcePartScanner,
    KB3DAssemblyReconstructor,
    scan_assembly,
    scan_source_parts,
    reconstruct_from_files
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Source parts from FBX/BGEO decomposition
SOURCE_PARTS_DIR = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                       "mission_to_minerva_clone/kb3d_missiontominerva.fbxobj.native/"
                       "geo/KB3D_MTM_BldgLgCommsArray_A/KB3D_MTM_BldgLgCommsArray_A")

# Production assembly to analyze
PRODUCTION_ASSEMBLY = Path("/media/tushita/TUSHITA_LINUX_DATA/assets/"
                          "kb3d_missiontominerva/Models/KB3D_MTM_BldgLgCommsArray_A/"
                          "KB3D_MTM_BldgLgCommsArray_A.usd")

# Output paths
OUTPUT_DIR = Path("/tmp/kb3d_assembly_workflow")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAPPING_JSON = OUTPUT_DIR / "assembly_mapping.json"
CATALOG_JSON = OUTPUT_DIR / "parts_catalog.json"
RECONSTRUCTED_USD = OUTPUT_DIR / "KB3D_MTM_BldgLgCommsArray_A_reconstructed.usd"


# =============================================================================
# WORKFLOW STEP 1: Scan Source Parts
# =============================================================================

def step_01_scan_source_parts():
    """Scan all source part folders and create catalog"""
    print("=" * 80)
    print("STEP 1: Scanning Source Parts")
    print("=" * 80)
    print(f"Source directory: {SOURCE_PARTS_DIR}")
    print()

    if not SOURCE_PARTS_DIR.exists():
        print(f"❌ Error: Source directory not found!")
        print(f"   Please update SOURCE_PARTS_DIR in the script")
        return None

    # Scan source parts
    scanner = KB3DSourcePartScanner(SOURCE_PARTS_DIR)
    parts = scanner.scan()

    # Save catalog
    scanner.save_catalog(CATALOG_JSON)

    # Print summary
    print()
    print("Part Categories Found:")
    categories = {}
    for part_name in parts.keys():
        # Extract category (first word/prefix)
        category = part_name.split('_')[0] if '_' in part_name else part_name[:10]
        categories[category] = categories.get(category, 0) + 1

    for category, count in sorted(categories.items()):
        print(f"  - {category}: {count} parts")

    return parts


# =============================================================================
# WORKFLOW STEP 2: Scan Production Assembly
# =============================================================================

def step_02_scan_production_assembly():
    """Scan production assembly to extract transform and instance data"""
    print("\n" + "=" * 80)
    print("STEP 2: Scanning Production Assembly")
    print("=" * 80)
    print(f"Production assembly: {PRODUCTION_ASSEMBLY}")
    print()

    if not PRODUCTION_ASSEMBLY.exists():
        print(f"❌ Error: Production assembly not found!")
        print(f"   Please update PRODUCTION_ASSEMBLY in the script")
        return None, None

    # Scan assembly
    scanner = KB3DAssemblyScanner(PRODUCTION_ASSEMBLY)
    metadata, instances = scanner.scan()

    # Save mapping
    scanner.save_mapping(MAPPING_JSON)

    # Print summary
    print()
    print("Assembly Structure:")
    print(f"  - Assembly name: {metadata.assembly_name}")
    print(f"  - Total instances: {metadata.total_instances}")
    print(f"  - Groups: {len(metadata.groups)}")
    if metadata.groups:
        for group in metadata.groups:
            group_instances = [i for i in instances if i.group_name == group]
            print(f"    • {group}: {len(group_instances)} instances")
    print(f"  - Default variant: {metadata.default_variant}")

    if metadata.extent_hint:
        print(f"  - Extent: min={metadata.extent_hint[0]}, max={metadata.extent_hint[1]}")

    # Print instance summary
    print()
    print("Instance Details (first 10):")
    for i, inst in enumerate(instances[:10]):
        print(f"  {i+1}. {inst.instance_name}")
        print(f"     Source: {inst.source_part_name}")
        if inst.transform and inst.transform.translate:
            print(f"     Position: {inst.transform.translate}")
        if inst.group_name:
            print(f"     Group: {inst.group_name}")
        print()

    if len(instances) > 10:
        print(f"  ... and {len(instances) - 10} more instances")

    return metadata, instances


# =============================================================================
# WORKFLOW STEP 3: Analyze Mapping
# =============================================================================

def step_03_analyze_mapping(parts_catalog, instances):
    """Analyze mapping between source parts and assembly instances"""
    print("\n" + "=" * 80)
    print("STEP 3: Analyzing Part-to-Instance Mapping")
    print("=" * 80)
    print()

    # Check which instances have matching source parts
    matched = 0
    unmatched = []

    for inst in instances:
        if inst.source_part_name in parts_catalog:
            matched += 1
        else:
            unmatched.append(inst)

    print(f"Mapping Analysis:")
    print(f"  - Matched instances: {matched}/{len(instances)} ({matched/len(instances)*100:.1f}%)")
    print(f"  - Unmatched instances: {len(unmatched)}")

    if unmatched:
        print()
        print("Unmatched Instances (source parts not found):")
        unique_unmatched = set(inst.source_part_name for inst in unmatched)
        for i, part_name in enumerate(sorted(unique_unmatched)[:20], 1):
            count = sum(1 for inst in unmatched if inst.source_part_name == part_name)
            print(f"  {i}. {part_name} ({count} instances)")
            # Try to find similar parts
            similar = [p for p in parts_catalog.keys() if part_name.lower() in p.lower() or p.lower() in part_name.lower()]
            if similar:
                print(f"     Possible matches: {', '.join(similar[:3])}")

        if len(unique_unmatched) > 20:
            print(f"  ... and {len(unique_unmatched) - 20} more")

    # Analyze transform data
    print()
    print("Transform Data Analysis:")
    has_translate = sum(1 for inst in instances if inst.transform and inst.transform.translate)
    has_rotate = sum(1 for inst in instances if inst.transform and inst.transform.rotate)
    has_scale = sum(1 for inst in instances if inst.transform and inst.transform.scale)

    print(f"  - With translation: {has_translate}/{len(instances)} ({has_translate/len(instances)*100:.1f}%)")
    print(f"  - With rotation: {has_rotate}/{len(instances)} ({has_rotate/len(instances)*100:.1f}%)")
    print(f"  - With scale: {has_scale}/{len(instances)} ({has_scale/len(instances)*100:.1f}%)")

    return matched, unmatched


# =============================================================================
# WORKFLOW STEP 4: Reconstruct Assembly
# =============================================================================

def step_04_reconstruct_assembly():
    """Reconstruct assembly from source parts using mapping data"""
    print("\n" + "=" * 80)
    print("STEP 4: Reconstructing Assembly from Source Parts")
    print("=" * 80)
    print()

    if not MAPPING_JSON.exists() or not CATALOG_JSON.exists():
        print("❌ Error: Mapping or catalog files not found!")
        print("   Run previous steps first")
        return

    print(f"Loading mapping from: {MAPPING_JSON}")
    print(f"Loading catalog from: {CATALOG_JSON}")
    print()

    # Load data
    with open(MAPPING_JSON) as f:
        mapping = json.load(f)

    with open(CATALOG_JSON) as f:
        catalog = json.load(f)

    # Reconstruct
    reconstructor = KB3DAssemblyReconstructor(mapping, catalog)

    # Calculate relative path from output to source parts
    # For this example, we'll use an absolute path reference
    # In production, you'd calculate proper relative path
    relative_path = str(SOURCE_PARTS_DIR)

    print(f"Reconstructing assembly...")
    print(f"Output: {RECONSTRUCTED_USD}")
    print(f"Parts path: {relative_path}")
    print()

    reconstructor.reconstruct(RECONSTRUCTED_USD, relative_path)

    print()
    print("✓ Assembly reconstruction complete!")
    print()
    print("Next steps:")
    print("  1. Open reconstructed USD in usdview or Houdini")
    print("  2. Verify all instances loaded correctly")
    print("  3. Check transforms are correct")
    print("  4. Adjust material assignments if needed")


# =============================================================================
# WORKFLOW STEP 5: Compare Original vs Reconstructed
# =============================================================================

def step_05_compare_assemblies():
    """Compare original and reconstructed assemblies"""
    print("\n" + "=" * 80)
    print("STEP 5: Comparing Original vs Reconstructed")
    print("=" * 80)
    print()

    if not RECONSTRUCTED_USD.exists():
        print("❌ Error: Reconstructed USD not found!")
        print("   Run step 4 first")
        return

    from pxr import Usd

    print("Opening stages...")
    original_stage = Usd.Stage.Open(str(PRODUCTION_ASSEMBLY))
    reconstructed_stage = Usd.Stage.Open(str(RECONSTRUCTED_USD))

    if not original_stage or not reconstructed_stage:
        print("❌ Error: Could not open one or both stages")
        return

    # Compare prim counts
    def count_prims(stage):
        return len([p for p in stage.Traverse()])

    original_count = count_prims(original_stage)
    reconstructed_count = count_prims(reconstructed_stage)

    print(f"Prim Count:")
    print(f"  - Original: {original_count}")
    print(f"  - Reconstructed: {reconstructed_count}")
    print(f"  - Difference: {abs(original_count - reconstructed_count)}")

    # Compare default prims
    orig_default = original_stage.GetDefaultPrim()
    recon_default = reconstructed_stage.GetDefaultPrim()

    print()
    print(f"Default Prims:")
    print(f"  - Original: {orig_default.GetPath() if orig_default else 'None'}")
    print(f"  - Reconstructed: {recon_default.GetPath() if recon_default else 'None'}")

    # Compare extents
    if orig_default and recon_default:
        orig_extent = orig_default.GetAttribute('extentsHint')
        recon_extent = recon_default.GetAttribute('extentsHint')

        if orig_extent and recon_extent:
            print()
            print("Extent Hints:")
            print(f"  - Original: {orig_extent.Get()}")
            print(f"  - Reconstructed: {recon_extent.Get()}")

    print()
    print("✓ Comparison complete!")


# =============================================================================
# CONVENIENCE FUNCTION: Run All Steps
# =============================================================================

def run_complete_workflow():
    """Run all workflow steps in sequence"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "KB3D ASSEMBLY WORKFLOW - COMPLETE PIPELINE" + " " * 20 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Step 1: Scan source parts
    parts = step_01_scan_source_parts()
    if not parts:
        return

    # Step 2: Scan production assembly
    metadata, instances = step_02_scan_production_assembly()
    if not metadata or not instances:
        return

    # Step 3: Analyze mapping
    matched, unmatched = step_03_analyze_mapping(parts, instances)

    # Step 4: Reconstruct assembly
    step_04_reconstruct_assembly()

    # Step 5: Compare assemblies
    step_05_compare_assemblies()

    print()
    print("=" * 80)
    print("WORKFLOW COMPLETE!")
    print("=" * 80)
    print()
    print(f"Generated files:")
    print(f"  - Parts catalog: {CATALOG_JSON}")
    print(f"  - Assembly mapping: {MAPPING_JSON}")
    print(f"  - Reconstructed USD: {RECONSTRUCTED_USD}")
    print()
    print("To view the reconstructed assembly:")
    print(f"  usdview {RECONSTRUCTED_USD}")


# =============================================================================
# QUICK EXAMPLES
# =============================================================================

def example_quick_scan():
    """Quick example: Scan and save without analysis"""
    print("Quick Scan Example")
    print("-" * 40)

    # Scan and save in one go
    parts = scan_source_parts(SOURCE_PARTS_DIR, CATALOG_JSON)
    metadata, instances = scan_assembly(PRODUCTION_ASSEMBLY, MAPPING_JSON)

    print(f"\n✓ Found {len(parts)} parts")
    print(f"✓ Found {len(instances)} instances")


def example_reconstruct_only():
    """Quick example: Reconstruct from existing JSON files"""
    print("Reconstruct Only Example")
    print("-" * 40)

    if not MAPPING_JSON.exists() or not CATALOG_JSON.exists():
        print("❌ JSON files not found. Run scan first.")
        return

    reconstruct_from_files(
        MAPPING_JSON,
        CATALOG_JSON,
        RECONSTRUCTED_USD,
        relative_parts_path=str(SOURCE_PARTS_DIR)
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="KB3D Assembly Scanner and Reconstructor Workflow"
    )
    parser.add_argument(
        'command',
        nargs='?',
        default='all',
        choices=['all', 'scan-parts', 'scan-assembly', 'analyze', 'reconstruct', 'compare', 'quick'],
        help='Workflow step to run (default: all)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'all':
            run_complete_workflow()
        elif args.command == 'scan-parts':
            step_01_scan_source_parts()
        elif args.command == 'scan-assembly':
            step_02_scan_production_assembly()
        elif args.command == 'analyze':
            # Load existing data
            with open(CATALOG_JSON) as f:
                parts = json.load(f)
            with open(MAPPING_JSON) as f:
                mapping = json.load(f)
            from kb3d_assembly_scanner import InstanceData, TransformData
            instances = []
            for inst_data in mapping['instances']:
                inst = InstanceData(**inst_data)
                if inst_data.get('transform'):
                    inst.transform = TransformData(**inst_data['transform'])
                instances.append(inst)
            step_03_analyze_mapping(parts, instances)
        elif args.command == 'reconstruct':
            step_04_reconstruct_assembly()
        elif args.command == 'compare':
            step_05_compare_assemblies()
        elif args.command == 'quick':
            example_quick_scan()
            example_reconstruct_only()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
