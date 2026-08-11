#!/usr/bin/env python3
"""
Quick test script to verify Houdini MCP server connection
"""

import socket
import json
import sys


def test_connection(host='localhost', port=9876):
    """Test connection to Houdini MCP server and get scene info."""
    try:
        print(f"Attempting to connect to Houdini MCP Server at {host}:{port}...")

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))

        print("✓ Connected successfully!")

        # Send get_scene_info command
        request = {
            'id': 1,
            'command': 'get_scene_info',
            'params': {}
        }

        print("\nSending get_scene_info command...")
        message = json.dumps(request) + '\n'
        sock.sendall(message.encode('utf-8'))

        # Receive response
        print("Waiting for response...")
        buffer = ""
        while True:
            data = sock.recv(4096).decode('utf-8')
            if not data:
                break
            buffer += data
            if '\n' in buffer:
                response_str, _ = buffer.split('\n', 1)
                response = json.loads(response_str)
                break

        sock.close()

        # Display results
        print("\n" + "="*80)
        print("HOUDINI SCENE INFO")
        print("="*80)

        if response.get('status') == 'success':
            result = response.get('result', {})
            print(f"\n📁 Hip File: {result.get('hip_file', 'N/A')}")
            print(f"📄 Hip Name: {result.get('hip_name', 'N/A')}")
            print(f"🎬 Current Frame: {result.get('frame', 'N/A')}")
            print(f"⏱️  FPS: {result.get('fps', 'N/A')}")

            nodes = result.get('nodes', [])
            print(f"\n🔧 Total Nodes: {len(nodes)}")

            if nodes:
                print("\n📋 Node List (first 20):")
                for i, node in enumerate(nodes[:20]):
                    print(f"  {i+1}. {node['path']} ({node['type']})")

                if len(nodes) > 20:
                    print(f"  ... and {len(nodes) - 20} more nodes")

            print("\n✓ Successfully retrieved scene information!")
            return True
        else:
            print(f"\n✗ Error: {response.get('error', 'Unknown error')}")
            return False

    except socket.timeout:
        print(f"\n✗ Connection timeout - server not responding")
        return False
    except ConnectionRefusedError:
        print(f"\n✗ Connection refused - server not running on port {port}")
        print("\nTo start the server, run in Houdini Python Shell:")
        print(">>> from HMCP import start_server")
        print(">>> start_server()")
        return False
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
