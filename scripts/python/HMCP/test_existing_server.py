#!/usr/bin/env python3
"""Test the existing Houdini MCP server that's already running"""

import socket
import json


def send_command(method, params=None):
    """Send a command to the existing Houdini MCP server."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9876))

    # Try different message formats
    formats = [
        # Format 1: Direct method/params
        {'method': method, 'params': params or {}},
        # Format 2: With ID
        {'id': 1, 'method': method, 'params': params or {}},
        # Format 3: As command
        {'command': method, 'params': params or {}},
    ]

    for fmt in formats:
        message = json.dumps(fmt) + '\n'
        print(f"\nTrying format: {fmt}")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 9876))
        sock.sendall(message.encode('utf-8'))

        response = sock.recv(4096).decode('utf-8')
        print(f"Response: {response}")

        try:
            parsed = json.loads(response.strip())
            if parsed.get('status') == 'success' or 'error' not in parsed.get('status', ''):
                print("✓ This format works!")
                return parsed
        except:
            pass

        sock.close()

    return None


# Try to get scene info
print("="*80)
print("Testing existing Houdini MCP server on port 9876")
print("="*80)

result = send_command('get_scene_info')

if result:
    print("\n" + "="*80)
    print("SUCCESS!")
    print("="*80)
    print(json.dumps(result, indent=2))
