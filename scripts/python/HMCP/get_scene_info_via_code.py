#!/usr/bin/env python3
"""Get Houdini scene info using the existing MCP server's execute_code method"""

import socket
import json


def execute_code(code):
    """Execute Python code in Houdini via existing MCP server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9876))

    request = {
        'method': 'execute_code',
        'params': {'code': code}
    }

    message = json.dumps(request) + '\n'
    sock.sendall(message.encode('utf-8'))

    response = sock.recv(8192).decode('utf-8').strip()
    sock.close()

    return json.loads(response)


# Code to get scene info
code = """
import hou
import json

# Get scene information
scene_info = {
    'hip_file': hou.hipFile.path(),
    'hip_name': hou.hipFile.basename(),
    'frame': hou.frame(),
    'fps': hou.fps(),
    'nodes': []
}

# Get all nodes
for node in hou.node('/').allSubChildren():
    scene_info['nodes'].append({
        'path': node.path(),
        'type': node.type().name(),
        'name': node.name()
    })

# Return as JSON
print(json.dumps(scene_info, indent=2))
"""

print("="*80)
print("CONNECTING TO HOUDINI VIA EXISTING MCP SERVER")
print("="*80)
print("\nExecuting scene info query...\n")

result = execute_code(code)

print("="*80)
print("RESPONSE FROM HOUDINI")
print("="*80)
print(json.dumps(result, indent=2))

# Try to extract the actual data from output
if result.get('status') == 'ok' and 'output' in result:
    print("\n" + "="*80)
    print("HOUDINI SCENE INFO")
    print("="*80)

    output = result['output']
    try:
        # The output contains the JSON we printed
        scene_data = json.loads(output)

        print(f"\n📁 Hip File: {scene_data.get('hip_file', 'N/A')}")
        print(f"📄 Hip Name: {scene_data.get('hip_name', 'N/A')}")
        print(f"🎬 Current Frame: {scene_data.get('frame', 'N/A')}")
        print(f"⏱️  FPS: {scene_data.get('fps', 'N/A')}")

        nodes = scene_data.get('nodes', [])
        print(f"\n🔧 Total Nodes: {len(nodes)}")

        if nodes:
            print("\n📋 Node List (first 30):")
            for i, node in enumerate(nodes[:30]):
                print(f"  {i+1:3d}. {node['path']:50s} ({node['type']})")

            if len(nodes) > 30:
                print(f"\n  ... and {len(nodes) - 30} more nodes")

        print("\n✓ Successfully connected to Houdini and retrieved scene info!")

    except json.JSONDecodeError:
        print(f"\nRaw output:\n{output}")
