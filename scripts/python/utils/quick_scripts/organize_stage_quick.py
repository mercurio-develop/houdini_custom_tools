"""
Quick Stage Organizer

Run this in Houdini's Python Shell to quickly organize your stage network.

Usage in Houdini Python Shell:
    execfile("/home/tushita/houdini21.0/custom_tools/scripts/python/organize_stage_quick.py")

Or:
    import sys
    sys.path.insert(0, '/home/tushita/houdini21.0/custom_tools/scripts/python')
    import organize_stage_quick
    organize_stage_quick.run()
"""

import hou
import sys

# Add custom tools to path
sys.path.insert(0, '/home/tushita/houdini21.0/custom_tools/scripts/python')

from tools.lop_network_organizer import LOPNetworkOrganizer


def run(stage_path: str = "/stage", merge: bool = True, layout: bool = True):
    """
    Quick organize function.

    Args:
        stage_path: Path to stage context
        merge: Merge component outputs
        layout: Grid layout
    """
    print("=" * 80)
    print("QUICK STAGE ORGANIZER")
    print("=" * 80)

    # Find stage
    stage = hou.node(stage_path)
    if not stage:
        print(f"Stage not found at: {stage_path}")
        print("Searching for LOP networks...")

        for node in hou.node("/").allSubChildren():
            if node.type().category().name() == "Lop":
                if node.type().name() == "lopnet":
                    stage = node
                    print(f"Found: {stage.path()}")
                    break

    if not stage:
        print("ERROR: No LOP network found!")
        return

    print(f"\nStage: {stage.path()}")
    print(f"Nodes: {len(stage.children())}")

    # Create organizer
    organizer = LOPNetworkOrganizer(stage.path())

    # Analyze
    component_outputs = organizer.find_component_outputs()
    subnets = organizer.find_subnet_outputs()

    print(f"\nComponent outputs: {len(component_outputs)}")
    print(f"Subnets: {len(subnets)}")
    print(f"Total to organize: {len(component_outputs) + len(subnets)}")

    # Confirm
    if len(component_outputs) + len(subnets) == 0:
        print("\nNothing to organize!")
        return

    print("\n" + "-" * 80)
    response = input(f"Organize {len(component_outputs) + len(subnets)} nodes? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return

    # Organize
    print("\nOrganizing...")
    organizer.organize_network(merge_outputs=merge, layout_grid=layout, create_boxes=False)

    print("\n" + "=" * 80)
    print("DONE!")
    print("=" * 80)


def run_with_ui():
    """Show UI dialog"""
    from tools.lop_network_organizer_ui import show_organizer_dialog
    show_organizer_dialog()


if __name__ == "__main__":
    # If running with UI available, show dialog
    try:
        run_with_ui()
    except:
        # Otherwise run in terminal mode
        run()
