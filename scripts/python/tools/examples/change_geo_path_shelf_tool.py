"""
Shelf Tool: Change Geometry Path in LOPs

This creates a simple UI tool to quickly change geometry paths from /ASSET/geo to /filename/geo

USAGE:
1. Select this script in the Python Source Editor
2. Run it (Ctrl+Enter)
3. Enter your component name
4. Geometry path will be updated automatically
"""

import hou


def change_geo_path_ui():
    """
    Interactive UI to change geometry path in selected LOP nodes
    """

    print("\n" + "="*70)
    print("CHANGE GEOMETRY PATH TOOL")
    print("="*70 + "\n")

    # Get current selection
    selected = hou.selectedNodes()

    if not selected:
        hou.ui.displayMessage(
            "Please select a LOP node first!",
            severity=hou.severityType.Warning
        )
        return

    # Get the LOP node
    lop_node = selected[0]

    if lop_node.type().category().name() != "Lop":
        hou.ui.displayMessage(
            "Please select a LOP node (you selected a {} node)".format(
                lop_node.type().category().name()
            ),
            severity=hou.severityType.Warning
        )
        return

    # Get stage
    stage = lop_node.stage()
    if not stage:
        hou.ui.displayMessage(
            "No USD stage found on selected node!",
            severity=hou.severityType.Warning
        )
        return

    # Ask user for component name
    result = hou.ui.readInput(
        "Enter new component name:\n\n"
        "This will rename /ASSET to /{component_name}\n"
        "Geometry will be at /{component_name}/geo",
        buttons=("OK", "Cancel"),
        initial_contents="MyComponent",
        title="Change Geometry Path"
    )

    if result[0] != 0:  # Cancelled
        return

    component_name = result[1].strip()

    if not component_name:
        hou.ui.displayMessage(
            "Component name cannot be empty!",
            severity=hou.severityType.Warning
        )
        return

    # Create Edit node to rename
    parent = lop_node.parent()
    edit_node = parent.createNode("edit", f"rename_to_{component_name}")
    edit_node.setInput(0, lop_node)

    # Set parameters
    edit_node.parm("primpattern1").set("/ASSET")
    edit_node.parm("primpath1").set(f"/{component_name}")

    # Position nicely
    pos = lop_node.position()
    edit_node.setPosition([pos[0], pos[1] - 1])

    # Set display flag
    edit_node.setDisplayFlag(True)

    # Success message
    hou.ui.displayMessage(
        f"✓ Geometry path changed!\n\n"
        f"Old path: /ASSET/geo\n"
        f"New path: /{component_name}/geo\n\n"
        f"Node created: {edit_node.name()}",
        severity=hou.severityType.Message,
        title="Success"
    )

    print(f"✓ Created rename node: {edit_node.path()}")
    print(f"  Old: /ASSET/geo")
    print(f"  New: /{component_name}/geo")


def create_component_with_custom_geo_path():
    """
    Create new component setup with custom geo path from scratch
    """

    print("\n" + "="*70)
    print("CREATE COMPONENT WITH CUSTOM GEO PATH")
    print("="*70 + "\n")

    # Ask for component name
    result = hou.ui.readInput(
        "Enter component name:\n\n"
        "This will create a component with geometry at:\n"
        "/{component_name}/geo",
        buttons=("OK", "Cancel"),
        initial_contents="MyComponent",
        title="Create Component"
    )

    if result[0] != 0:
        return

    component_name = result[1].strip()

    if not component_name:
        hou.ui.displayMessage("Component name cannot be empty!")
        return

    # Ask for SOP path
    sop_result = hou.ui.readInput(
        "Enter SOP path (geometry to import):\n\n"
        "Example: /obj/geo1/OUT",
        buttons=("OK", "Cancel"),
        initial_contents="/obj/geo1",
        title="Select Geometry"
    )

    if sop_result[0] != 0:
        return

    sop_path = sop_result[1].strip()

    # Verify SOP exists
    sop_node = hou.node(sop_path)
    if not sop_node:
        hou.ui.displayMessage(
            f"SOP node not found: {sop_path}",
            severity=hou.severityType.Warning
        )
        return

    # Create stage if needed
    stage = hou.node("/stage")
    if not stage:
        obj = hou.node("/obj")
        stage = obj.createNode("stage", "stage")

    # Create SOP import with custom path prefix
    sopimport = stage.createNode("sopimport", f"import_{component_name}")
    sopimport.parm("soppath").set(sop_path)
    sopimport.parm("pathprefix").set(f"/{component_name}")  # ← KEY SETTING

    # Configure as component
    configure = stage.createNode("configureprimitive", f"configure_{component_name}")
    configure.setInput(0, sopimport)
    configure.parm("primpath").set(f"/{component_name}")
    configure.parm("kind").set("component")
    configure.parm("instanceable").set(True)

    # Layout
    stage.layoutChildren()

    # Set display
    configure.setDisplayFlag(True)

    # Success
    hou.ui.displayMessage(
        f"✓ Component created!\n\n"
        f"Component: {component_name}\n"
        f"Geo path: /{component_name}/geo\n"
        f"SOP source: {sop_path}\n\n"
        f"Created nodes:\n"
        f"  - {sopimport.name()}\n"
        f"  - {configure.name()}",
        severity=hou.severityType.Message,
        title="Success"
    )

    print(f"\n✓ Component created: {component_name}")
    print(f"  Geo path: /{component_name}/geo")
    print(f"  Nodes: {sopimport.path()}, {configure.path()}")


def batch_fix_geo_paths():
    """
    Batch fix multiple /ASSET paths in the network
    """

    print("\n" + "="*70)
    print("BATCH FIX GEO PATHS")
    print("="*70 + "\n")

    # Get selected nodes
    selected = hou.selectedNodes()

    if not selected or len(selected) != 1:
        hou.ui.displayMessage(
            "Please select ONE LOP node to start from!",
            severity=hou.severityType.Warning
        )
        return

    lop_node = selected[0]
    stage = lop_node.stage()

    if not stage:
        hou.ui.displayMessage("No USD stage found!")
        return

    # Find all /ASSET prims
    asset_prims = []
    for prim in stage.Traverse():
        if prim.GetPath().pathString.startswith("/ASSET"):
            asset_prims.append(prim.GetPath().pathString)

    if not asset_prims:
        hou.ui.displayMessage(
            "No /ASSET prims found in stage!",
            severity=hou.severityType.Message
        )
        return

    # Ask for new component name
    result = hou.ui.readInput(
        f"Found {len(asset_prims)} /ASSET prims:\n\n" +
        "\n".join(asset_prims[:5]) +
        ("\n..." if len(asset_prims) > 5 else "") +
        "\n\nEnter new component name:",
        buttons=("OK", "Cancel"),
        initial_contents="MyComponent",
        title="Batch Rename"
    )

    if result[0] != 0:
        return

    component_name = result[1].strip()

    # Create edit node
    parent = lop_node.parent()
    edit_node = parent.createNode("edit", f"batch_rename_{component_name}")
    edit_node.setInput(0, lop_node)
    edit_node.parm("primpattern1").set("/ASSET")
    edit_node.parm("primpath1").set(f"/{component_name}")

    # Position and display
    pos = lop_node.position()
    edit_node.setPosition([pos[0], pos[1] - 1])
    edit_node.setDisplayFlag(True)

    hou.ui.displayMessage(
        f"✓ Batch rename complete!\n\n"
        f"Renamed {len(asset_prims)} prims\n"
        f"/ASSET → /{component_name}",
        severity=hou.severityType.Message
    )

    print(f"✓ Batch renamed {len(asset_prims)} prims")


# =============================================================================
# MENU - Choose Action
# =============================================================================

def main():
    """
    Main menu to choose action
    """

    choice = hou.ui.displayMessage(
        "Change Geometry Path Tool\n\n"
        "Choose an action:",
        buttons=(
            "Change Existing Path",
            "Create New Component",
            "Batch Fix Paths",
            "Cancel"
        ),
        severity=hou.severityType.Message,
        title="Geo Path Tool",
        default_choice=0,
        close_choice=3
    )

    if choice == 0:
        # Change existing
        change_geo_path_ui()
    elif choice == 1:
        # Create new
        create_component_with_custom_geo_path()
    elif choice == 2:
        # Batch fix
        batch_fix_geo_paths()
    else:
        print("Cancelled")


# =============================================================================
# RUN IT
# =============================================================================

if __name__ == "__main__":
    main()


# =============================================================================
# SHELF TOOL CODE
# =============================================================================

"""
To create a shelf tool:

1. Create new Shelf Tool
2. Paste this code in the Script tab:

import sys
sys.path.insert(0, '/home/tushita/houdini21.0/custom_tools/scripts/python/tools/examples')
import change_geo_path_shelf_tool
change_geo_path_shelf_tool.main()

3. Set Label: "Fix Geo Path"
4. Set Icon: NETWORKS_sop (or any icon you like)
5. Save

Now you can click the shelf button to fix geo paths!
"""
