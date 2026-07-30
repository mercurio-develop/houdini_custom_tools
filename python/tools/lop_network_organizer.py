"""
LOP Network Organizer

Organizes overlapping LOP nodes and merges component outputs into a clean hierarchy.

Features:
- Auto-layout nodes in a grid pattern
- Find and merge all componentoutput nodes
- Group related nodes into network boxes
- Clean up wire routing

Usage:
    import hou
    from tools import lop_network_organizer

    # Organize current network
    organizer = lop_network_organizer.LOPNetworkOrganizer("/stage")
    organizer.organize_network()

    # Merge all component outputs
    merge_node = organizer.merge_component_outputs()
"""

import hou
from typing import List, Dict, Tuple, Optional
import re


class LOPNetworkOrganizer:
    """Organizes and cleans up LOP networks"""

    def __init__(self, stage_context_path: str = "/stage"):
        """
        Initialize organizer.

        Args:
            stage_context_path: Path to stage LOP network or LOP context (e.g., "/stage")
        """
        self.stage_context = hou.node(stage_context_path)
        if not self.stage_context:
            raise ValueError(f"Stage context not found: {stage_context_path}")

        # Check if this is a LOP network (lopnet) or a LOP context (inside lopnet)
        node_type = self.stage_context.type().name()
        category = self.stage_context.type().category().name()

        # If it's a LOP node (not lopnet), we can work with it directly
        if category == "Lop":
            # This is a LOP context, we can organize its children
            pass
        elif node_type == "lopnet":
            # This is a lopnet container, we can organize its children
            pass
        else:
            raise ValueError(
                f"Node is not a LOP network or LOP context: {stage_context_path}\n"
                f"Type: {node_type}, Category: {category}"
            )

    def find_component_outputs(self) -> List[hou.Node]:
        """Find all componentoutput nodes in the network"""
        component_outputs = []

        for node in self.stage_context.children():
            # Look for componentoutput or componentoutput_custom nodes
            if node.type().name() in ["componentoutput", "componentoutput_custom"]:
                component_outputs.append(node)

        print(f"Found {len(component_outputs)} component output nodes")
        return component_outputs

    def find_subnet_outputs(self) -> List[hou.Node]:
        """Find all subnet nodes that might be component builders"""
        subnets = []

        for node in self.stage_context.children():
            if node.type().name() == "subnet":
                # Check if subnet name suggests it's a component builder
                if any(keyword in node.name().lower() for keyword in
                       ["component", "asset", "builder", "lops_asset"]):
                    subnets.append(node)

        print(f"Found {len(subnets)} subnet nodes")
        return subnets

    def merge_component_outputs(self, merge_name: str = "merge_all_assets") -> hou.Node:
        """
        Create a merge node that combines all component outputs.

        Args:
            merge_name: Name for the merge node

        Returns:
            Created merge node
        """
        component_outputs = self.find_component_outputs()
        subnets = self.find_subnet_outputs()

        # Combine all nodes that should be merged
        nodes_to_merge = component_outputs + subnets

        if not nodes_to_merge:
            print("No component outputs or subnets found to merge!")
            return None

        print(f"\nMerging {len(nodes_to_merge)} nodes...")

        # Find a good position for the merge node (below all inputs)
        max_y = max(node.position()[1] for node in nodes_to_merge)
        avg_x = sum(node.position()[0] for node in nodes_to_merge) / len(nodes_to_merge)

        merge_pos = (avg_x, max_y - 2.0)  # Below all inputs

        # Create merge node
        merge_node = self.stage_context.createNode("merge", merge_name)
        merge_node.setPosition(merge_pos)

        # Set the number of inputs
        merge_node.parm("numconnects").set(len(nodes_to_merge))

        # Connect all nodes to the merge
        for i, node in enumerate(nodes_to_merge):
            merge_node.setInput(i, node)
            print(f"  Connected: {node.name()} -> {merge_name} (input {i})")

        # Set merge node color
        merge_node.setColor(hou.Color((0.3, 0.6, 0.3)))  # Green

        # Create output null for convenience
        output_null = self.stage_context.createNode("null", "FINAL_OUTPUT")
        output_null.setPosition((merge_pos[0], merge_pos[1] - 1.5))
        output_null.setInput(0, merge_node)
        output_null.setColor(hou.Color((1.0, 0.8, 0.0)))  # Gold
        output_null.setDisplayFlag(True)
        output_null.setRenderFlag(True)

        print(f"\nMerge complete! Created: {merge_node.path()}")
        print(f"Final output: {output_null.path()}")

        return merge_node

    def organize_grid_layout(self, nodes: List[hou.Node] = None,
                            spacing_x: float = 3.0,
                            spacing_y: float = 2.5,
                            columns: int = 5):
        """
        Organize nodes in a grid layout.

        Args:
            nodes: List of nodes to organize (None = all nodes in network)
            spacing_x: Horizontal spacing between nodes
            spacing_y: Vertical spacing between nodes
            columns: Number of columns in grid
        """
        if nodes is None:
            nodes = [n for n in self.stage_context.children()
                    if n.type().name() not in ["null"]]  # Skip output nulls

        if not nodes:
            print("No nodes to organize")
            return

        print(f"\nOrganizing {len(nodes)} nodes in grid layout...")
        print(f"  Grid: {columns} columns")
        print(f"  Spacing: {spacing_x} x {spacing_y}")

        # Group nodes by type for better organization
        node_groups = self._group_nodes_by_type(nodes)

        # Organize each group
        current_row = 0
        for group_name, group_nodes in node_groups.items():
            print(f"\n  Group: {group_name} ({len(group_nodes)} nodes)")

            for i, node in enumerate(group_nodes):
                col = i % columns
                row = current_row + (i // columns)

                x = col * spacing_x
                y = -row * spacing_y

                node.setPosition((x, y))

            # Move to next group (add spacing between groups)
            rows_used = (len(group_nodes) + columns - 1) // columns
            current_row += rows_used + 1  # +1 for spacing between groups

        print("\nGrid layout complete!")

    def _group_nodes_by_type(self, nodes: List[hou.Node]) -> Dict[str, List[hou.Node]]:
        """Group nodes by their type/category"""
        groups = {
            "Component Builders": [],
            "Geometry Nodes": [],
            "Material Nodes": [],
            "Transform Nodes": [],
            "Merge Nodes": [],
            "Other": []
        }

        for node in nodes:
            node_type = node.type().name()
            node_name = node.name().lower()

            if "component" in node_name or "subnet" in node_type:
                groups["Component Builders"].append(node)
            elif node_type in ["componentgeometry", "sopimport", "file", "reference"]:
                groups["Geometry Nodes"].append(node)
            elif node_type in ["materiallibrary", "material", "assignmaterial"]:
                groups["Material Nodes"].append(node)
            elif node_type in ["xform", "transform"]:
                groups["Transform Nodes"].append(node)
            elif node_type in ["merge", "collect"]:
                groups["Merge Nodes"].append(node)
            else:
                groups["Other"].append(node)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def create_network_boxes(self, auto_group: bool = True):
        """
        Create network boxes to group related nodes.

        Args:
            auto_group: Automatically group nodes by type/naming
        """
        if not auto_group:
            return

        print("\nCreating network boxes...")

        # Find component builder subnets
        subnets = self.find_subnet_outputs()

        for subnet in subnets:
            # Create network box around subnet and its connected nodes
            connected_nodes = self._get_connected_nodes(subnet, depth=1)
            all_nodes = [subnet] + connected_nodes

            if len(all_nodes) > 1:
                self._create_netbox_around_nodes(all_nodes, subnet.name())

    def _get_connected_nodes(self, node: hou.Node, depth: int = 1) -> List[hou.Node]:
        """Get nodes connected to the given node up to specified depth"""
        connected = []

        if depth <= 0:
            return connected

        # Get inputs
        for input_node in node.inputs():
            if input_node and input_node not in connected:
                connected.append(input_node)
                if depth > 1:
                    connected.extend(self._get_connected_nodes(input_node, depth - 1))

        # Get outputs
        for output_conn in node.outputConnections():
            output_node = output_conn.outputNode()
            if output_node and output_node not in connected:
                connected.append(output_node)
                if depth > 1:
                    connected.extend(self._get_connected_nodes(output_node, depth - 1))

        return list(set(connected))  # Remove duplicates

    def _create_netbox_around_nodes(self, nodes: List[hou.Node], box_name: str):
        """Create a network box around the specified nodes"""
        if not nodes:
            return

        # Calculate bounding box
        positions = [n.position() for n in nodes]
        min_x = min(p[0] for p in positions) - 0.5
        max_x = max(p[0] for p in positions) + 0.5
        min_y = min(p[1] for p in positions) - 0.5
        max_y = max(p[1] for p in positions) + 0.5

        # Create network box
        netbox = self.stage_context.createNetworkBox(f"box_{box_name}")
        netbox.setComment(box_name)

        # Add nodes to box
        for node in nodes:
            netbox.addNode(node)

        # Set bounds
        netbox.setPosition((min_x, min_y))
        netbox.setSize((max_x - min_x, max_y - min_y))

        print(f"  Created network box: {box_name} ({len(nodes)} nodes)")

    def organize_network(self, merge_outputs: bool = True,
                        layout_grid: bool = True,
                        create_boxes: bool = False):
        """
        Full network organization workflow.

        Args:
            merge_outputs: Merge all component outputs
            layout_grid: Organize in grid layout
            create_boxes: Create network boxes
        """
        print("=" * 80)
        print("LOP Network Organizer")
        print("=" * 80)
        print(f"Stage context: {self.stage_context.path()}")
        print(f"Total nodes: {len(self.stage_context.children())}")
        print()

        # Step 1: Organize layout (do this first, before merge)
        if layout_grid:
            # Only layout component builders and their immediate inputs
            component_outputs = self.find_component_outputs()
            subnets = self.find_subnet_outputs()
            nodes_to_layout = component_outputs + subnets

            if nodes_to_layout:
                self.organize_grid_layout(nodes_to_layout, columns=4)

        # Step 2: Create network boxes (optional)
        if create_boxes:
            self.create_network_boxes()

        # Step 3: Merge outputs (do this last)
        if merge_outputs:
            merge_node = self.merge_component_outputs()

        print("\n" + "=" * 80)
        print("Organization complete!")
        print("=" * 80)


def organize_current_stage(merge: bool = True, layout: bool = True, boxes: bool = False):
    """
    Convenience function to organize the current stage network.

    Args:
        merge: Merge component outputs
        layout: Organize in grid
        boxes: Create network boxes
    """
    # Find stage context - try multiple locations
    stage = None

    # Try /stage first
    if hou.node("/stage"):
        stage = hou.node("/stage")
        print(f"Found stage at: {stage.path()}")

    # Try /obj/stage
    elif hou.node("/obj/stage"):
        stage = hou.node("/obj/stage")
        print(f"Found stage at: {stage.path()}")

    # Look for any LOP context with many children
    else:
        print("Looking for LOP contexts...")
        candidates = []

        # Search all nodes
        for node in hou.node("/").allSubChildren():
            if node.type().category().name() == "Lop":
                child_count = len(node.children())
                if child_count > 0:
                    candidates.append((node, child_count))

        if candidates:
            # Sort by child count (most children first)
            candidates.sort(key=lambda x: x[1], reverse=True)
            stage = candidates[0][0]
            print(f"Found LOP context with {candidates[0][1]} nodes: {stage.path()}")

        # Fallback: look for any lopnet in /obj
        if not stage:
            print("Looking for lopnet in /obj...")
            for node in hou.node("/obj").children():
                if node.type().name() == "lopnet":
                    stage = node
                    print(f"Found lopnet: {stage.path()}")
                    break

    if not stage:
        print("ERROR: No LOP network found!")
        print("\nPlease specify the path manually:")
        print("  organizer = LOPNetworkOrganizer('/path/to/your/stage')")
        return None

    print(f"Using stage context: {stage.path()}")
    print(f"Node type: {stage.type().name()}, Category: {stage.type().category().name()}")

    organizer = LOPNetworkOrganizer(stage.path())
    organizer.organize_network(merge_outputs=merge, layout_grid=layout, create_boxes=boxes)

    return organizer


# Standalone execution
if __name__ == "__main__":
    organize_current_stage(merge=True, layout=True, boxes=False)
