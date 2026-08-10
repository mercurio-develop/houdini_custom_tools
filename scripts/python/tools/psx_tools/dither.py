"""Color dithering and palette quantization (ported from Blender PSX Retro Tools)."""

from __future__ import annotations

from typing import Literal

import numpy as np

DitherMethod = Literal[
    "BAYER",
    "FLOYD_STEINBERG",
    "JJN",
    "STUCKI",
    "BURKES",
    "SIERRA",
    "SIERRA_TWO_ROW",
    "SIERRA_LITE",
    "ATKINSON",
]

_BAYER_MATRIX = np.array(
    [
        [0 / 16, 8 / 16, 2 / 16, 10 / 16],
        [12 / 16, 4 / 16, 14 / 16, 6 / 16],
        [3 / 16, 11 / 16, 1 / 16, 9 / 16],
        [15 / 16, 7 / 16, 13 / 16, 5 / 16],
    ],
    dtype=np.float32,
)


def get_dither_matrix(method: str) -> tuple[list[list[float]], int]:
    """Return error-diffusion kernel and divisor for the given method."""
    matrices: dict[str, tuple[list[list[float]], int]] = {
        "BAYER": (_BAYER_MATRIX.tolist(), 16),
        "FLOYD_STEINBERG": ([[0, 0, 7 / 16], [3 / 16, 5 / 16, 1 / 16]], 16),
        "JJN": (
            [[0, 0, 0, 7 / 48, 5 / 48], [3 / 48, 5 / 48, 7 / 48, 5 / 48, 3 / 48], [1 / 48, 3 / 48, 5 / 48, 3 / 48, 1 / 48]],
            48,
        ),
        "STUCKI": (
            [[0, 0, 0, 8 / 42, 4 / 42], [2 / 42, 4 / 42, 8 / 42, 4 / 42, 2 / 42], [1 / 42, 2 / 42, 4 / 42, 2 / 42, 1 / 42]],
            42,
        ),
        "BURKES": ([[0, 0, 0, 8 / 32, 4 / 32], [2 / 32, 4 / 32, 8 / 32, 4 / 32, 2 / 32]], 32),
        "SIERRA": (
            [[0, 0, 0, 5 / 32, 3 / 32], [2 / 32, 4 / 32, 5 / 32, 4 / 32, 2 / 32], [0, 2 / 32, 3 / 32, 2 / 32, 0]],
            32,
        ),
        "SIERRA_TWO_ROW": ([[0, 0, 0, 4 / 16, 3 / 16], [1 / 16, 2 / 16, 3 / 16, 2 / 16, 1 / 16]], 16),
        "SIERRA_LITE": ([[0, 0, 2 / 4], [1 / 4, 1 / 4, 0]], 4),
        "ATKINSON": ([[0, 0, 1 / 8, 1 / 8], [1 / 8, 1 / 8, 1 / 8, 0], [0, 1 / 8, 0, 0]], 8),
    }
    return matrices.get(method.upper(), matrices["BAYER"])


def _quantize_palette_median_cut(rgb: np.ndarray, palette_size: int) -> np.ndarray:
    """Quantize RGB image to palette_size colors using median-cut (Pillow-compatible)."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError("Pillow is required for PSX dithering. Install with: pip install Pillow") from exc

    h, w, _ = rgb.shape
    img = Image.fromarray(rgb.astype(np.uint8), mode="RGB")
    img = img.quantize(colors=max(2, palette_size), method=Image.MEDIANCUT, dither=Image.NONE)
    return np.array(img.convert("RGB"), dtype=np.float32)


def apply_dithering(
    rgb: np.ndarray,
    method: str = "BAYER",
    palette_size: int = 16,
    dither_scale: float = 0.1,
) -> np.ndarray:
    """
    Apply PSX-style dithering to an HxWx3 float or uint8 RGB array.

    Returns uint8 HxWx3 array.
    """
    if rgb.dtype != np.float32 and rgb.dtype != np.float64:
        pixels = rgb.astype(np.float32)
    else:
        pixels = (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.float32) if rgb.max() <= 1.0 else rgb.astype(np.float32)

    height, width, _ = pixels.shape
    if max(width, height) > 1024:
        raise ValueError(f"Texture too large for dithering ({width}x{height} > 1024)")

    pixel_data = _quantize_palette_median_cut(pixels.astype(np.uint8), palette_size)
    matrix, _ = get_dither_matrix(method)
    step = 255.0 / max(palette_size - 1, 1)

    if method.upper() == "BAYER":
        bayer = np.array(matrix, dtype=np.float32)
        mh, mw = bayer.shape
        tiled = np.tile(bayer, (height // mh + 1, width // mw + 1))[:height, :width] * 255.0 * dither_scale
        for channel in range(3):
            channel_data = pixel_data[:, :, channel]
            dithered = channel_data + tiled
            pixel_data[:, :, channel] = np.clip(np.round(dithered / step) * step, 0, 255)
    else:
        for channel in range(3):
            for y in range(height):
                for x in range(width):
                    old_pixel = pixel_data[y, x, channel]
                    new_pixel = round(old_pixel / step) * step
                    new_pixel = min(max(new_pixel, 0), 255)
                    error = (old_pixel - new_pixel) * dither_scale
                    error = max(min(error, 255.0), -255.0)
                    pixel_data[y, x, channel] = new_pixel
                    for dy, row in enumerate(matrix):
                        for dx, weight in enumerate(row):
                            if weight == 0:
                                continue
                            ny, nx = y + dy, x + dx - (len(row) // 2)
                            if 0 <= ny < height and 0 <= nx < width:
                                pixel_data[ny, nx, channel] += error * weight

    return pixel_data.astype(np.uint8)
