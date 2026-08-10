#!/usr/bin/env python3
"""Discover what methods the existing server supports"""

import socket
import json

common_methods = [
    'ping',
    'get_scene',
    'scene_info',
    'create_node',
    'execute_code',
    'execute_python',
    'run_code',
    'eval',
    'list_methods',
    'help',
]

print("Testing common method names...")
print("="*80)

for method in common_methods:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('localhost', 9876))
        message = json.dumps({'method': method, 'params': {}}) + '\n'
        sock.sendall(message.encode('utf-8'))
        response = sock.recv(4096).decode('utf-8').strip()

        if response:
            parsed = json.loads(response)
            status = parsed.get('status', 'unknown')

            if 'unknown method' not in parsed.get('message', '').lower():
                print(f"✓ {method:20s} - {status}")
                if status == 'success':
                    print(f"  Response: {json.dumps(parsed, indent=2)}")
            else:
                print(f"✗ {method:20s} - not recognized")
    except Exception as e:
        print(f"✗ {method:20s} - error: {e}")
    finally:
        sock.close()
