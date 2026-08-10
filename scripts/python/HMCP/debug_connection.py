#!/usr/bin/env python3
"""Debug connection to see raw response"""

import socket
import json

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 9876))

request = {
    'id': 1,
    'command': 'get_scene_info',
    'params': {}
}

message = json.dumps(request) + '\n'
print("Sending:", message)
sock.sendall(message.encode('utf-8'))

# Get raw response
response = sock.recv(4096).decode('utf-8')
print("\nRaw response:")
print(response)
print("\nParsed:")
print(json.dumps(json.loads(response.strip()), indent=2))

sock.close()
