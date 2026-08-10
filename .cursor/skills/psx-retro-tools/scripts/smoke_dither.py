#!/usr/bin/env python3
"""Smoke-test PSX dither without hou."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_PYTHON = Path(__file__).resolve().parents[4] / "scripts" / "python"
_DITHER = _REPO_PYTHON / "tools" / "psx_tools" / "dither.py"


def main() -> int:
    if not _DITHER.is_file():
        print(f"Not found: {_DITHER}", file=sys.stderr)
        return 1

    spec = importlib.util.spec_from_file_location("psx_dither", _DITHER)
    dither = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dither)

    import numpy as np

    rgb = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    out = dither.apply_dithering(rgb, method="BAYER", palette_size=16, dither_scale=0.1)
    print(f"OK: shape={out.shape} dtype={out.dtype}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
