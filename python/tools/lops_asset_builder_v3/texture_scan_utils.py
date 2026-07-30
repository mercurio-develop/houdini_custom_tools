"""Shared texture folder resolution for LOPS Asset Builder (KB3D library layouts)."""

from __future__ import annotations

import os

_TEXTURE_WALK_SKIP = frozenset({"geo", "Models", "parts", ".git", "__pycache__"})
_TEXTURE_RES_PRIORITY = ("png4k", "png2k", "jpg4k", "jpg2k", "png1k", "jpg1k", "exr4k", "exr2k")


def resolve_texture_search_roots(folder_textures: str) -> list[str]:
    """Resolve texture scan roots; avoid walking entire KB3D library geo/ trees."""
    folder = os.path.normpath(folder_textures or "")
    if not folder or not os.path.isdir(folder):
        return [folder] if folder else []

    textures_dir = os.path.join(folder, "Textures")
    if os.path.isdir(textures_dir):
        for res in _TEXTURE_RES_PRIORITY:
            candidate = os.path.join(textures_dir, res)
            if os.path.isdir(candidate):
                return [candidate]
        return [textures_dir]

    if os.path.basename(folder).lower() == "textures":
        for res in _TEXTURE_RES_PRIORITY:
            candidate = os.path.join(folder, res)
            if os.path.isdir(candidate):
                return [candidate]
        return [folder]

    basename = os.path.basename(folder).lower()
    if basename in _TEXTURE_RES_PRIORITY:
        return [folder]

    return [folder]


def walk_texture_dirs(search_root: str):
    """Walk a texture root, skipping geometry/model subtrees."""
    if not search_root or not os.path.isdir(search_root):
        return
    for root, dirs, files in os.walk(search_root):
        dirs[:] = [
            d for d in dirs
            if d not in _TEXTURE_WALK_SKIP and not d.startswith(".")
        ]
        yield root, dirs, files
