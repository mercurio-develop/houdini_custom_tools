"""Batch texture processing for PSX assets."""

from __future__ import annotations

import os
from typing import Callable, Iterable

from tools.psx_tools.dither import apply_dithering

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".tga", ".exr"}


def _load_rgb(path: str):
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Pillow is required for PSX texture processing.") from exc
    img = Image.open(path).convert("RGB")
    return img, __import__("numpy").array(img)


def _save_rgb(path: str, rgb_array) -> None:
    from PIL import Image

    Image.fromarray(rgb_array, mode="RGB").save(path)


def process_texture_file(
    path: str,
    *,
    palette_size: int = 16,
    dither_method: str = "BAYER",
    dither_scale: float = 0.1,
    max_size: int | None = 128,
    output_suffix: str = "_psx",
    overwrite: bool = False,
) -> str | None:
    """
    Dither and optionally downscale a texture file.

    Returns output path when processed, else None when skipped.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in _IMAGE_EXTENSIONS:
        return None

    base, _ = os.path.splitext(path)
    out_path = f"{base}{output_suffix}{ext}"
    if os.path.exists(out_path) and not overwrite:
        return out_path

    _img, rgb = _load_rgb(path)
    if max_size and max(rgb.shape[0], rgb.shape[1]) > max_size:
        from PIL import Image

        pil = Image.fromarray(rgb)
        pil = pil.resize((max_size, max_size), Image.Resampling.NEAREST)
        rgb = __import__("numpy").array(pil)

    result = apply_dithering(rgb, method=dither_method, palette_size=palette_size, dither_scale=dither_scale)
    _save_rgb(out_path, result)
    return out_path


def process_texture_folder(
    folder: str,
    *,
    palette_size: int = 16,
    dither_method: str = "BAYER",
    dither_scale: float = 0.1,
    max_size: int | None = 128,
    output_suffix: str = "_psx",
    overwrite: bool = False,
    progress: Callable[[str], None] | None = None,
) -> list[str]:
    """Process all image files under folder (non-recursive). Returns list of output paths."""
    if not folder or not os.path.isdir(folder):
        return []

    outputs: list[str] = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if not os.path.isfile(path):
            continue
        if progress:
            progress(f"PSX texture: {name}")
        out = process_texture_file(
            path,
            palette_size=palette_size,
            dither_method=dither_method,
            dither_scale=dither_scale,
            max_size=max_size,
            output_suffix=output_suffix,
            overwrite=overwrite,
        )
        if out:
            outputs.append(out)
    return outputs


def resolve_psx_texture_folder(original_folder: str, psx_suffix: str = "_psx") -> str:
    """
    If PSX-processed textures exist alongside originals, prefer the PSX folder.

    Looks for sibling folder named `{basename}{psx_suffix}` or files with `_psx` suffix in-place.
    """
    if not original_folder:
        return original_folder
    parent = os.path.dirname(original_folder.rstrip("/"))
    base = os.path.basename(original_folder.rstrip("/"))
    sibling = os.path.join(parent, f"{base}{psx_suffix}")
    if os.path.isdir(sibling):
        return sibling
    return original_folder
