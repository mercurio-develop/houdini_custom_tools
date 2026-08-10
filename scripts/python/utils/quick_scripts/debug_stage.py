"""
Debug Stage Network

Run this to see what LOP contexts exist in your scene.
"""

import hou


def debug_stage():
    """Print information about all LOP contexts in the scene"""

    print("=" * 80)
    print("STAGE NETWORK DEBUG")
    print("=" * 80)

    # Check /stage
    print("\n1. Checking /stage:")
    stage = hou.node("/stage")
    if stage:
        print(f"   ✓ Found: {stage.path()}")
        print(f"   Type: {stage.type().name()}")
        print(f"   Category: {stage.type().category().name()}")
        print(f"   Children: {len(stage.children())}")
    else:
        print("   ✗ Not found")

    # Check /obj/stage
    print("\n2. Checking /obj/stage:")
    obj_stage = hou.node("/obj/stage")
    if obj_stage:
        print(f"   ✓ Found: {obj_stage.path()}")
        print(f"   Type: {obj_stage.type().name()}")
        print(f"   Category: {obj_stage.type().category().name()}")
        print(f"   Children: {len(obj_stage.children())}")
    else:
        print("   ✗ Not found")

    # Find all LOP contexts
    print("\n3. Searching for all LOP contexts...")
    lop_contexts = []

    for node in hou.node("/").allSubChildren():
        if node.type().category().name() == "Lop":
            child_count = len(node.children())
            if child_count > 0:
                lop_contexts.append((node, child_count))

    if lop_contexts:
        print(f"   Found {len(lop_contexts)} LOP contexts with children:")
        # Sort by child count
        lop_contexts.sort(key=lambda x: x[1], reverse=True)

        for i, (node, count) in enumerate(lop_contexts[:10], 1):  # Show top 10
            print(f"   {i}. {node.path()}")
            print(f"      Type: {node.type().name()}")
            print(f"      Children: {count}")

            # Show first few children
            if count > 0 and count <= 5:
                print(f"      Child nodes:")
                for child in node.children()[:5]:
                    print(f"        - {child.name()} ({child.type().name()})")
            elif count > 5:
                print(f"      Child nodes (first 3):")
                for child in node.children()[:3]:
                    print(f"        - {child.name()} ({child.type().name()})")
    else:
        print("   ✗ No LOP contexts found")

    # Find lopnets
    print("\n4. Looking for lopnet containers...")
    lopnets = []
    for node in hou.node("/obj").children():
        if node.type().name() == "lopnet":
            lopnets.append(node)

    if lopnets:
        print(f"   Found {len(lopnets)} lopnet(s):")
        for lopnet in lopnets:
            print(f"   - {lopnet.path()} ({len(lopnet.children())} children)")
    else:
        print("   ✗ No lopnets found in /obj")

    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)

    # Recommend which one to use
    if lop_contexts:
        best = lop_contexts[0][0]
        print(f"Use this path: {best.path()}")
        print(f"Has {lop_contexts[0][1]} nodes to organize")
        print("\nRun this code:")
        print(f"  from tools.lop_network_organizer import LOPNetworkOrganizer")
        print(f"  organizer = LOPNetworkOrganizer('{best.path()}')")
        print(f"  organizer.organize_network()")
    else:
        print("No LOP contexts found! Create a LOP network first.")

    print("=" * 80)


if __name__ == "__main__":
    debug_stage()
