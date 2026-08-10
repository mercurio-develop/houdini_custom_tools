"""
Diagnostic script to check Houdini MCP Server status from inside Houdini.

Run this in Houdini's Python Shell to diagnose server issues.
"""

import hou
import sys


def diagnose_server():
    """Run complete diagnostic of the MCP server."""
    print("=" * 80)
    print("HOUDINI MCP SERVER DIAGNOSTIC")
    print("=" * 80)

    # Check 1: Module import
    print("\n[1/6] Checking HMCP module...")
    try:
        import HMCP
        print("✓ HMCP module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import HMCP: {e}")
        return False

    # Check 2: Server functions available
    print("\n[2/6] Checking server functions...")
    try:
        from HMCP import start_server, stop_server, is_server_running, get_server
        print("✓ Server functions available")
    except Exception as e:
        print(f"✗ Failed to import server functions: {e}")
        return False

    # Check 3: Session variable
    print("\n[3/6] Checking hou.session for server...")
    if hasattr(hou.session, 'houdini_mcp_server'):
        server = hou.session.houdini_mcp_server
        print(f"✓ Server object exists in hou.session: {server}")
    else:
        print("✗ No server object in hou.session")
        print("  → Server was never started or was cleaned up")
        return False

    # Check 4: Server running status
    print("\n[4/6] Checking server running status...")
    server = get_server()
    if server:
        print(f"  Server instance: {server}")
        print(f"  is_running attribute: {server.is_running}")
        print(f"  Host: {server.host}")
        print(f"  Port: {server.port}")

        if hasattr(server, 'server_socket') and server.server_socket:
            print(f"  Server socket: {server.server_socket}")
            try:
                print(f"  Socket bound to: {server.server_socket.getsockname()}")
            except Exception as e:
                print(f"  Socket error: {e}")
        else:
            print("  ✗ No server socket!")

        if hasattr(server, 'listen_thread') and server.listen_thread:
            print(f"  Listen thread: {server.listen_thread}")
            print(f"  Thread alive: {server.listen_thread.is_alive()}")
        else:
            print("  ✗ No listen thread!")
    else:
        print("✗ No server instance found")
        return False

    # Check 5: Try to test the socket
    print("\n[5/6] Testing socket connection...")
    try:
        import socket
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.settimeout(2)
        result = test_sock.connect_ex(('localhost', 9876))
        test_sock.close()

        if result == 0:
            print("✓ Port 9876 is accepting connections")
        else:
            print(f"✗ Port 9876 is not accepting connections (error code: {result})")
            return False
    except Exception as e:
        print(f"✗ Socket test failed: {e}")
        return False

    # Check 6: Try to send a test command
    print("\n[6/6] Sending test command...")
    try:
        import socket
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

        # Try to receive response
        response = sock.recv(4096).decode('utf-8')
        sock.close()

        if response:
            print(f"✓ Received response: {response[:100]}...")
            data = json.loads(response.strip())
            if data.get('status') == 'success':
                print("✓ Server is working correctly!")
                return True
            else:
                print(f"⚠ Server returned: {data}")
        else:
            print("✗ No response received")
            return False

    except Exception as e:
        print(f"✗ Test command failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    return True


def restart_server():
    """Stop and restart the server."""
    print("\nRestarting server...")
    from HMCP import stop_server, start_server
    stop_server()
    import time
    time.sleep(1)
    server = start_server()
    print("Server restarted")
    return server


if __name__ == "__main__":
    success = diagnose_server()

    if not success:
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print("1. Try restarting the server:")
        print("   >>> from HMCP.diagnose_server import restart_server")
        print("   >>> restart_server()")
        print("\n2. Check Houdini console for error messages")
        print("\n3. Try starting fresh:")
        print("   >>> from HMCP import start_server")
        print("   >>> start_server()")
