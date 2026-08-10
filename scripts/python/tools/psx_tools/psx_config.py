"""Configuration for PSX-style asset processing."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PSXAssetConfig:
    """Options mirroring the Blender PSX Retro Tools feature set."""

    # Geometry
    decimate_ratio: float = 0.5
    triangulate: bool = True
    apply_vertex_wobble: bool = False
    wobble_amplitude: float = 0.07
    wobble_frequency: float = 6.2
    wobble_axes: str = "Z"  # Z | XYZ | Custom
    wobble_hold_frames: float = 0.0
    wobble_seed: float = 1.0
    apply_screen_snap: bool = False
    screen_snap_size: float = 64.0
    camera_path: str = "/obj/cam1"

    # Textures
    texture_size: int = 128
    palette_size: int = 16
    dither_method: str = "BAYER"  # BAYER, FLOYD_STEINBERG, ATKINSON, ...
    dither_scale: float = 0.1
    process_textures: bool = True

    # Render (Karma)
    render_resolution: tuple[int, int] = (320, 240)
    disable_aa: bool = True
    lowres_shadows: bool = True
    disable_denoising: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PSXAssetConfig":
        cfg = cls()
        for key, value in data.items():
            if hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg


@dataclass
class PSXBuildConfig:
    """Wraps asset-builder paths with PSX preprocessing."""

    main_asset_file_path: str = ""
    folder_textures: str = ""
    asset_name: str = ""
    psx: PSXAssetConfig = field(default_factory=PSXAssetConfig)
    run_lops_asset_builder: bool = True
    stage_context_path: str = "/stage"
