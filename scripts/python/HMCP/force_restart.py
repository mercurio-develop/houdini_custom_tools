"""
Force restart the Houdini MCP Server with detailed error logging.

This script completely stops and restarts the server, capturing all errors.
"""

import hou
import sys
import socket


def force_restart_server():
    """Stop and restart the server with full error details."""
    print("=" * 80)
    print("FORCE RESTARTING HOUDINI MCP SERVER")
    print("=" * 80)

    # Step 1: Stop existing server
    print("\n[Step 1] Stopping existing server...")
    try:
        from HMCP import stop_server
        stop_server()
        print("✓ Existing server stopped")
    except Exception as e:
        print(f"⚠ Error stopping server (may not have been running): {e}")

    # Clean up session
    if hasattr(hou.session, 'houdini_mcp_server'):
        hou.session.houdini_mcp_server = None
        print("✓ Cleaned up hou.session")

    # Step 2: Check if port is available
    print("\n[Step 2] Checking if port 9876 is available...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind(('localhost', 9876))
        test_socket.close()
        print("✓ Port 9876 is available")
    except OSError as e:
        print(f"✗ Port 9876 is not available: {e}")
        print("  This might mean another process is using it.")
        print("  Try running: lsof -i :9876")
        return None

    # Step 3: Import server class
    print("\n[Step 3] Importing server class...")
    try:
        from HMCP.server import HoudiniMCPServer
        print("✓ Server class imported")
    except Exception as e:
        print(f"✗ Failed to import server: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Step 4: Create server instance with error catching
    print("\n[Step 4] Creating server instance...")
    try:
        # Redirect server startup output
        print("  Creating HoudiniMCPServer(host='localhost', port=9876)...")
        server = HoudiniMCPServer(host='localhost', port=9876)

        # Give it a moment to start
        import time
        time.sleep(0.5)

        print(f"  Server object created: {server}")
        print(f"  is_running: {server.is_running}")
        print(f"  host: {server.host}")
        print(f"  port: {server.port}")

        if hasattr(server, 'server_socket') and server.server_socket:
            try:
                addr = server.server_socket.getsockname()
                print(f"  Socket bound to: {addr}")
            except Exception as e:
                print(f"  Socket error: {e}")

        if hasattr(server, 'listen_thread'):
            if server.listen_thread:
                print(f"  Listen thread exists: {server.listen_thread}")
                print(f"  Thread is alive: {server.listen_thread.is_alive()}")
            else:
                print("  ✗ No listen thread created!")

        if server.is_running:
            print("✓ Server created and running")
            hou.session.houdini_mcp_server = server
            print("✓ Server stored in hou.session")
        else:
            print("✗ Server created but is_running = False")
            print("  Check the console for error messages from _start()")
            return None

    except Exception as e:
        print(f"✗ Failed to create server: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Step 5: Test the connection
    print("\n[Step 5] Testing connection...")
    try:
        import time
        time.sleep(0.5)  # Give server time to start listening

        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(2)
        result = test_sock.connect_ex(('localhost', 9876))
        test_sock.close()

        if result == 0:
            print("✓ Port 9876 is accepting connections!")
        else:
            print(f"✗ Port 9876 not accepting connections (error: {result})")
            return None
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return None

    # Step 6: Send test command
    print("\n[Step 6] Sending test command...")
    try:
        import json

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 9876))

        request = {
            'id': 1,
            'command': 'get_scene_info',
            'params': {}
        }

        message = json.dumps(request) + '\n'
        sock.sendall(message.encode('utf-8'))

        response = sock.recv(4096).decode('utf-8')
        sock.close()

        if response:
            data = json.loads(response.strip())
            if data.get('status') == 'success':
                print("✓ Server responds correctly!")
                print(f"  Scene: {data.get('result', {}).get('hip_name', 'N/A')}")
            else:
                print(f"⚠ Server responded with: {data.get('status')}")

    except Exception as e:
        print(f"✗ Test command failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("✓ SERVER RESTART COMPLETE!")
    print("=" * 80)
    print("\nServer is running on localhost:9876")
    print("You can now connect your MCP agent (e.g. Cursor) via the bridge.")

    return server


if __name__ == "__main__":
    server = force_restart_server()

    if not server:
        print("\n" + "=" * 80)
        print("❌ SERVER RESTART FAILED")
        print("=" * 80)
        print("\nPlease check the error messages above.")
        print("The console may have additional error details.")
