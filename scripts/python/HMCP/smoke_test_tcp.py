#!/usr/bin/env python3
"""
TCP smoke test for HMCP — run inside Houdini via hython or from an active session.

Usage:
  /opt/hfs22.0.368/bin/hython smoke_test_tcp.py
"""

import json
import socket
import sys
import time


HOST = "localhost"
PORT = 9876


def send_command(sock, command, params=None, request_id=1):
    request = {
        "id": request_id,
        "command": command,
        "params": params or {},
    }
    sock.sendall((json.dumps(request) + "\n").encode("utf-8"))
    buffer = ""
    while "\n" not in buffer:
        data = sock.recv(65536).decode("utf-8")
        if not data:
            raise RuntimeError("Connection closed before response")
        buffer += data
    response_str, _ = buffer.split("\n", 1)
    return json.loads(response_str)


def port_open():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        return sock.connect_ex((HOST, PORT)) == 0
    finally:
        sock.close()


def run_tests():
    import hou
    from HMCP import is_server_running, start_server

    print("=" * 60)
    print("HMCP TCP Smoke Test")
    print("=" * 60)

    if not is_server_running():
        print("Starting HMCP server...")
        start_server()
        time.sleep(0.5)
    else:
        print("HMCP server already running")

    if not port_open():
        print("FAIL: port 9876 not accepting connections")
        return 1

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
    sock.connect((HOST, PORT))

    tests = [
        ("get_scene_info", {}),
        ("get_stage_summary", {}),
        ("get_server_health", {}),
        ("list_component_variants", {}),
        (
            "execute_code",
            {"code": "print(hou.applicationVersionString())"},
        ),
        ("reload_custom_tools", {"reload_modules": True}),
    ]

    failed = 0
    for idx, (command, params) in enumerate(tests, start=1):
        print(f"\n[{idx}/{len(tests)}] {command}")
        try:
            response = send_command(sock, command, params, request_id=idx)
            status = response.get("status")
            if status != "success":
                print(f"  FAIL: {response.get('error', response)}")
                failed += 1
                continue
            result = response.get("result", {})
            if command == "get_scene_info":
                print(f"  hip: {result.get('hip_name')}")
                print(f"  selected: {len(result.get('selected_nodes', []))}")
            elif command == "get_stage_summary":
                print(f"  stage: {result.get('stage_path')}")
                print(f"  children: {result.get('child_count')}")
                print(f"  component_outputs: {len(result.get('component_outputs', []))}")
            elif command == "get_server_health":
                print(f"  houdini: {result.get('houdini_version')}")
                print(f"  port_open: {result.get('port_open')}")
                print(f"  selected: {result.get('selected_count')}")
            elif command == "search_assets":
                print(f"  count: {result.get('count')}")
                print(f"  root: {result.get('root_path')}")
            elif command == "list_component_variants":
                print(f"  node: {result.get('node_path')}")
                print(f"  variant_sets: {list((result.get('variant_sets') or {}).keys())}")
            elif command == "execute_code":
                stdout = (result.get("stdout") or "").strip()
                print(f"  stdout: {stdout or '(empty)'}")
                if result.get("error"):
                    print(f"  exec error: {result['error']}")
                    failed += 1
            elif command == "reload_custom_tools":
                print(f"  reload_modules: {result.get('reload_modules')}")
            print("  OK")
        except Exception as exc:
            print(f"  FAIL: {exc}")
            failed += 1

    sock.close()

    print("\n" + "=" * 60)
    if failed:
        print(f"SMOKE TEST FAILED ({failed} command(s))")
        return 1
    print("SMOKE TEST PASSED")
    print(f"Houdini: {hou.applicationVersionString()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(run_tests())
    except Exception as exc:
        print(f"Smoke test error: {exc}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
