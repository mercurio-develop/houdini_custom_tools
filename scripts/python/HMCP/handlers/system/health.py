"""Server health and static reference helpers."""

from __future__ import annotations

import os
import socket

import hou


def get_server_health(params: dict) -> dict:
    port = int(params.get("port", 9876))
    sock_ok = False
    try:
        test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test.settimeout(1)
        sock_ok = test.connect_ex(("localhost", port)) == 0
        test.close()
    except Exception:
        pass

    return {
        "houdini_version": hou.applicationVersionString(),
        "hip_file": hou.hipFile.path(),
        "frame": hou.frame(),
        "fps": hou.fps(),
        "port_open": sock_ok,
        "selected_count": len(hou.selectedNodes()),
    }


def get_asset_builder_example(params: dict) -> dict:
    custom_tools = os.environ.get("CUSTOM_TOOLS", "")
    example_name = params.get("name", "simple_config.json")
    if not custom_tools:
        raise ValueError("CUSTOM_TOOLS environment variable is not set")

    example_path = os.path.join(
        custom_tools,
        "scripts",
        "python",
        "tools",
        "lops_asset_builder_v3",
        "examples",
        example_name,
    )
    if not os.path.isfile(example_path):
        raise ValueError(f"Example not found: {example_path}")

    with open(example_path, encoding="utf-8") as handle:
        content = handle.read()

    return {"name": example_name, "path": example_path, "content": content}
