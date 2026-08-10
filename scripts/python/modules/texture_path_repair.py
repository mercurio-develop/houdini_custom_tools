"""Texture path repair and manifest comparison utilities."""

from __future__ import annotations

import os
import shutil

def find_texture_repair_candidate(
    broken_path: str,
    search_roots: list[str],
    basename: str | None = None,
) -> str | None:
    """Find a replacement file by basename under search roots."""
    name = basename or os.path.basename(broken_path.replace("\\", "/"))
    if not name:
        return None

    for root in search_roots:
        if not root or not os.path.isdir(root):
            continue
        direct = os.path.join(root, name)
        if os.path.isfile(direct):
            return os.path.abspath(direct)
        for dirpath, _dirs, files in os.walk(root):
            if name in files:
                return os.path.abspath(os.path.join(dirpath, name))
    return None


def repair_texture_map(
    textures: dict[str, str],
    search_roots: list[str],
    *,
    copy_to: str | None = None,
) -> dict:
    """Return repaired paths and a change log."""
    repaired: dict[str, str] = {}
    changes = []
    missing = []

    for channel, path in textures.items():
        norm = path.replace("\\", "/")
        if os.path.isfile(path):
            repaired[channel] = path
            continue

        candidate = find_texture_repair_candidate(path, search_roots)
        if candidate is None:
            missing.append({"channel": channel, "original": path})
            continue

        final_path = candidate
        if copy_to:
            os.makedirs(copy_to, exist_ok=True)
            dest = os.path.join(copy_to, os.path.basename(candidate))
            if not os.path.isfile(dest):
                shutil.copy2(candidate, dest)
            final_path = dest

        repaired[channel] = final_path
        changes.append({"channel": channel, "from": path, "to": final_path})

    return {
        "repaired_textures": repaired,
        "changes": changes,
        "still_missing": missing,
        "repaired_count": len(changes),
        "missing_count": len(missing),
    }


def compare_texture_manifests(
    expected: dict[str, str],
    found: dict[str, str],
) -> dict:
    """Compare folder/validator textures vs USD-extracted textures."""
    expected_keys = set(expected.keys())
    found_keys = set(found.keys())
    matched = {}
    missing_in_usd = []
    extra_in_usd = []
    path_mismatch = []

    for key in sorted(expected_keys & found_keys):
        exp = expected.get(key, "")
        got = found.get(key, "")
        if os.path.normpath(exp) == os.path.normpath(got):
            matched[key] = got
        else:
            path_mismatch.append({"channel": key, "expected": exp, "found": got})

    for key in sorted(expected_keys - found_keys):
        missing_in_usd.append({"channel": key, "expected": expected[key]})

    for key in sorted(found_keys - expected_keys):
        extra_in_usd.append({"channel": key, "found": found[key]})

    return {
        "matched_count": len(matched),
        "missing_in_usd_count": len(missing_in_usd),
        "extra_in_usd_count": len(extra_in_usd),
        "path_mismatch_count": len(path_mismatch),
        "matched": matched,
        "missing_in_usd": missing_in_usd,
        "extra_in_usd": extra_in_usd,
        "path_mismatch": path_mismatch,
    }
