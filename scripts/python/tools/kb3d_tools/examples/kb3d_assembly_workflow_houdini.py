"""
KB3D Assembly Scanner and Reconstructor - Houdini Version

Run this inside Houdini Python Shell or as a shelf tool.

Usage in Houdini Python Shell:
    execfile('/home/tushita/houdini21.0/custom_tools/scripts/python/tools/kb3d_tools/examples/kb3d_assembly_workflow_houdini.py')

Author: Custom Tools
Date: 2025
"""

import hou
from pathlib import Path
import sys
import json

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from kb3d_assembly_scanner import (
    KB3DAssemblyScanner,
    KB3DSourcePartScanner,
    KB3DAssemblyReconstructor,
    scan_assembly,
    scan_source_parts,
    reconstruct_from_files
)


# =============================================================================
# CONFIGURATION - Update these paths for your system
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
# HOUDINI UI HELPERS
# =============================================================================

def show_message(title, message, severity=hou.severityType.Message):
    """Show message dialog in Houdini"""
    hou.ui.displayMessage(message, title=title, severity=severity)


def show_progress(message):
    """Print to Houdini console"""
    print(f"\n{'=' * 80}")
    print(message)
    print('=' * 80)


# =============================================================================
# WORKFLOW FUNCTIONS
# =============================================================================

def step_01_scan_source_parts():
    """Scan all source part folders and create catalog"""
    show_progress("STEP 1: Scanning Source Parts")
    print(f"Source directory: {SOURCE_PARTS_DIR}")

    if not SOURCE_PARTS_DIR.exists():
        show_message("Error", f"Source directory not found:\n{SOURCE_PARTS_DIR}",
                    hou.severityType.Error)
        return None

    try:
        # Scan source parts
        scanner = KB3DSourcePartScanner(SOURCE_PARTS_DIR)
        parts = scanner.scan()

        # Save catalog
        scanner.save_catalog(CATALOG_JSON)

        # Print summary
        print(f"\nPart Categories Found:")
        categories = {}
        for part_name in parts.keys():
            category = part_name.split('_')[0] if '_' in part_name else part_name[:10]
            categories[category] = categories.get(category, 0) + 1

        for category, count in sorted(categories.items()):
            print(f"  - {category}: {count} parts")

        show_message("Success",
                    f"Found {len(parts)} source parts\n\nCatalog saved to:\n{CATALOG_JSON}")

        return parts

    except Exception as e:
        show_message("Error", f"Failed to scan source parts:\n{str(e)}",
                    hou.severityType.Error)
        import traceback
        traceback.print_exc()
        return None


def step_02_scan_production_assembly():
    """Scan production assembly to extract transform and instance data"""
    show_progress("STEP 2: Scanning Production Assembly")
    print(f"Production assembly: {PRODUCTION_ASSEMBLY}")

    if not PRODUCTION_ASSEMBLY.exists():
        show_message("Error",
                    f"Production assembly not found:\n{PRODUCTION_ASSEMBLY}",
                    hou.severityType.Error)
        return None, None

    try:
        # Scan assembly
        scanner = KB3DAssemblyScanner(PRODUCTION_ASSEMBLY)
        metadata, instances = scanner.scan()

        # Save mapping
        scanner.save_mapping(MAPPING_JSON)

        # Print summary
        print(f"\nAssembly Structure:")
        print(f"  - Assembly name: {metadata.assembly_name}")
        print(f"  - Total instances: {metadata.total_instances}")
        print(f"  - Groups: {len(metadata.groups)}")
        if metadata.groups:
            for group in metadata.groups:
                group_instances = [i for i in instances if i.group_name == group]
                print(f"    • {group}: {len(group_instances)} instances")
        print(f"  - Default variant: {metadata.default_variant}")

        message = f"Assembly: {metadata.assembly_name}\n"
        message += f"Instances: {metadata.total_instances}\n"
        message += f"Groups: {len(metadata.groups)}\n\n"
        message += f"Mapping saved to:\n{MAPPING_JSON}"

        show_message("Success", message)

        return metadata, instances

    except Exception as e:
        show_message("Error", f"Failed to scan assembly:\n{str(e)}",
                    hou.severityType.Error)
        import traceback
        traceback.print_exc()
        return None, None


def step_03_analyze_mapping(parts_catalog, instances):
    """Analyze mapping between source parts and assembly instances"""
    show_progress("STEP 3: Analyzing Part-to-Instance Mapping")

    # Check which instances have matching source parts
    matched = 0
    unmatched = []

    for inst in instances:
        if inst.source_part_name in parts_catalog:
            matched += 1
        else:
            unmatched.append(inst)

    print(f"\nMapping Analysis:")
    print(f"  - Matched instances: {matched}/{len(instances)} ({matched/len(instances)*100:.1f}%)")
    print(f"  - Unmatched instances: {len(unmatched)}")

    if unmatched:
        print(f"\nUnmatched Instances (first 10):")
        unique_unmatched = set(inst.source_part_name for inst in unmatched)
        for i, part_name in enumerate(sorted(unique_unmatched)[:10], 1):
            count = sum(1 for inst in unmatched if inst.source_part_name == part_name)
            print(f"  {i}. {part_name} ({count} instances)")

    # Analyze transform data
    print(f"\nTransform Data Analysis:")
    has_translate = sum(1 for inst in instances if inst.transform and inst.transform.translate)
    has_rotate = sum(1 for inst in instances if inst.transform and inst.transform.rotate)
    has_scale = sum(1 for inst in instances if inst.transform and inst.transform.scale)

    print(f"  - With translation: {has_translate}/{len(instances)} ({has_translate/len(instances)*100:.1f}%)")
    print(f"  - With rotation: {has_rotate}/{len(instances)} ({has_rotate/len(instances)*100:.1f}%)")
    print(f"  - With scale: {has_scale}/{len(instances)} ({has_scale/len(instances)*100:.1f}%)")

    message = f"Mapping Analysis:\n\n"
    message += f"Matched: {matched}/{len(instances)} ({matched/len(instances)*100:.1f}%)\n"
    message += f"Unmatched: {len(unmatched)}\n\n"
    message += f"Transform Coverage:\n"
    message += f"  Translation: {has_translate}/{len(instances)}\n"
    message += f"  Rotation: {has_rotate}/{len(instances)}\n"
    message += f"  Scale: {has_scale}/{len(instances)}"

    show_message("Analysis Results", message)

    return matched, unmatched


def step_04_reconstruct_assembly():
    """Reconstruct assembly from source parts using mapping data"""
    show_progress("STEP 4: Reconstructing Assembly from Source Parts")

    if not MAPPING_JSON.exists() or not CATALOG_JSON.exists():
        show_message("Error",
                    "Mapping or catalog files not found!\nRun previous steps first.",
                    hou.severityType.Error)
        return

    print(f"Loading mapping from: {MAPPING_JSON}")
    print(f"Loading catalog from: {CATALOG_JSON}")

    try:
        # Load data
        with open(MAPPING_JSON) as f:
            mapping = json.load(f)

        with open(CATALOG_JSON) as f:
            catalog = json.load(f)

        # Reconstruct
        reconstructor = KB3DAssemblyReconstructor(mapping, catalog)

        relative_path = str(SOURCE_PARTS_DIR)

        print(f"\nReconstructing assembly...")
        print(f"Output: {RECONSTRUCTED_USD}")
        print(f"Parts path: {relative_path}")

        reconstructor.reconstruct(RECONSTRUCTED_USD, relative_path)

        message = f"Assembly reconstructed successfully!\n\n"
        message += f"Output file:\n{RECONSTRUCTED_USD}\n\n"
        message += f"Next steps:\n"
        message += f"1. Load in Houdini: File > Import > USD\n"
        message += f"2. Or click 'Load in Stage' below"

        # Ask if user wants to load it
        result = hou.ui.displayMessage(
            message,
            buttons=("Load in Stage", "Close"),
            severity=hou.severityType.Message,
            title="Reconstruction Complete"
        )

        if result == 0:  # Load in Stage
            load_usd_in_stage(RECONSTRUCTED_USD)

    except Exception as e:
        show_message("Error", f"Failed to reconstruct assembly:\n{str(e)}",
                    hou.severityType.Error)
        import traceback
        traceback.print_exc()


def load_usd_in_stage(usd_path):
    """Load USD file into Houdini stage"""
    try:
        # Create or get /stage context
        stage_context = hou.node("/stage")
        if not stage_context:
            stage_context = hou.node("/obj").createNode("stage", "stage")

        # Create USD reference node
        ref_node = stage_context.createNode("reference", "reconstructed_assembly")
        ref_node.parm("filepath1").set(str(usd_path))

        # Layout nodes
        ref_node.moveToGoodPosition()

        # Frame the node
        stage_context.layoutChildren()

        # Show message
        show_message("Success",
                    f"USD loaded into stage!\n\nNode: {ref_node.path()}\n\n"
                    f"Open the Scene Graph Tree to view the assembly.")

        print(f"\n✓ USD loaded: {ref_node.path()}")

    except Exception as e:
        show_message("Error", f"Failed to load USD in stage:\n{str(e)}",
                    hou.severityType.Error)
        import traceback
        traceback.print_exc()


# =============================================================================
# MAIN WORKFLOW FUNCTION
# =============================================================================

def run_complete_workflow():
    """Run all workflow steps in sequence"""
    show_progress("KB3D ASSEMBLY WORKFLOW - COMPLETE PIPELINE")

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

    show_progress("WORKFLOW COMPLETE!")
    print(f"\nGenerated files:")
    print(f"  - Parts catalog: {CATALOG_JSON}")
    print(f"  - Assembly mapping: {MAPPING_JSON}")
    print(f"  - Reconstructed USD: {RECONSTRUCTED_USD}")


# =============================================================================
# INTERACTIVE MENU FUNCTION
# =============================================================================

def show_workflow_menu():
    """Show interactive menu for workflow steps"""
    choices = [
        "Run Complete Workflow (All Steps)",
        "Step 1: Scan Source Parts",
        "Step 2: Scan Production Assembly",
        "Step 3: Analyze Mapping",
        "Step 4: Reconstruct Assembly",
        "Load Reconstructed USD in Stage"
    ]

    result = hou.ui.selectFromList(
        choices,
        message="Select workflow step to run:",
        title="KB3D Assembly Workflow",
        column_header="Workflow Steps",
        num_visible_rows=10
    )

    if not result:
        return

    choice = result[0]

    try:
        if choice == 0:
            run_complete_workflow()
        elif choice == 1:
            step_01_scan_source_parts()
        elif choice == 2:
            step_02_scan_production_assembly()
        elif choice == 3:
            # Load existing data for analysis
            if CATALOG_JSON.exists() and MAPPING_JSON.exists():
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
            else:
                show_message("Error",
                           "Catalog or mapping files not found!\nRun steps 1 and 2 first.",
                           hou.severityType.Error)
        elif choice == 4:
            step_04_reconstruct_assembly()
        elif choice == 5:
            if RECONSTRUCTED_USD.exists():
                load_usd_in_stage(RECONSTRUCTED_USD)
            else:
                show_message("Error",
                           "Reconstructed USD not found!\nRun step 4 first.",
                           hou.severityType.Error)

    except Exception as e:
        show_message("Error", f"An error occurred:\n{str(e)}",
                    hou.severityType.Error)
        import traceback
        traceback.print_exc()


# =============================================================================
# AUTO-RUN WHEN EXECUTED
# =============================================================================

if __name__ == "__main__":
    # If run as script, show menu
    show_workflow_menu()
else:
    # If imported, just print instructions
    print("\nKB3D Assembly Workflow loaded!")
    print("\nAvailable functions:")
    print("  - show_workflow_menu()          # Show interactive menu")
    print("  - run_complete_workflow()       # Run all steps")
    print("  - step_01_scan_source_parts()   # Scan source parts")
    print("  - step_02_scan_production_assembly()  # Scan production assembly")
    print("  - step_03_analyze_mapping()     # Analyze mapping")
    print("  - step_04_reconstruct_assembly()  # Reconstruct assembly")
    print("\nTo start, run: show_workflow_menu()")
