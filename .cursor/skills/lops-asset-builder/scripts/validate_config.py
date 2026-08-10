#!/usr/bin/env python3
"""Validate a JSON config against AssetBuilderConfig fields (no hou required)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_REPO_PYTHON = Path(__file__).resolve().parents[4] / "scripts" / "python"
_CONFIG = _REPO_PYTHON / "tools" / "lops_asset_builder_v3" / "asset_builder_config.py"


def _load_asset_builder_config_class():
    if not _CONFIG.is_file():
        raise ImportError(f"Not found: {_CONFIG}")
    spec = importlib.util.spec_from_file_location("asset_builder_config", _CONFIG)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod.AssetBuilderConfig


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate_config.py <config.json>", file=sys.stderr)
        return 1

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    try:
        AssetBuilderConfig = _load_asset_builder_config_class()
    except ImportError as exc:
        print(f"Could not load AssetBuilderConfig: {exc}", file=sys.stderr)
        return 1

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    valid_fields = set(AssetBuilderConfig.__dataclass_fields__)
    unknown = set(data) - valid_fields
    if unknown:
        print(f"Warning: unknown keys (ignored by from_dict): {sorted(unknown)}")

    try:
        cfg = AssetBuilderConfig.from_dict(data)
        print(f"OK: asset_name={cfg.asset_name!r}")
        print(f"  geo: {cfg.main_asset_file_path}")
        print(f"  tex: {cfg.folder_textures}")
        return 0
    except (ValueError, TypeError) as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
