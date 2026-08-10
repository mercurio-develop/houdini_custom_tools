"""Shared configuration for GUI, CLI, and batch LOPS Asset Builder runs."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


def derive_asset_name(path: str) -> str:
    """Derive a node-safe asset name from a geometry file path."""
    base = os.path.basename(path) if path else ""
    if not base:
        return "ASSET"
    if base.endswith(".bgeo.sc"):
        return base[: -len(".bgeo.sc")] or "ASSET"
    if "." in base:
        base = base.split(".", 1)[0]
    return base or "ASSET"


@dataclass
class AssetBuilderConfig:
    """Single source of truth for asset builder options (GUI + CLI + batch)."""

    main_asset_file_path: str
    folder_textures: str

    asset_name: str = ""
    asset_variants: List[str] = field(default_factory=list)
    create_geo_variants: bool = True
    asset_vset_name: str = "geo_variant"
    mtl_variants: List[str] = field(default_factory=list)
    mtl_vset_name: str = "mtl_variant"
    create_lookdev: bool = False
    create_light_rig: bool = False
    enable_env_lights: bool = False
    env_light_paths: List[str] = field(default_factory=list)
    create_network_boxes: bool = False
    skip_matchsize: bool = False
    stage_context_path: str = "/stage"
    verbose: bool = True
    lowercase_material_names: bool = False
    use_custom_component_output: bool = True
    validate_materials: bool = True
    skip_geometry_scan: bool = False
    expected_material_names: List[str] | None = None

    def __post_init__(self) -> None:
        if not self.asset_name:
            self.asset_name = derive_asset_name(self.main_asset_file_path)
        if not os.path.isfile(self.main_asset_file_path):
            raise ValueError(f"Main asset file does not exist: {self.main_asset_file_path}")
        if not os.path.isdir(self.folder_textures):
            raise ValueError(f"Texture folder does not exist: {self.folder_textures}")

    @classmethod
    def from_dialog(cls, data: Dict[str, Any]) -> "AssetBuilderConfig":
        """Build config from AssetMaterialVariantsDialog.data()."""
        return cls(
            main_asset_file_path=(data.get("main_asset_file_path") or "").strip(),
            folder_textures=(data.get("main_textures") or "").strip(),
            asset_name=(data.get("asset_name_input") or "").strip() or derive_asset_name(
                data.get("main_asset_file_path") or ""
            ),
            asset_variants=list(data.get("asset_variants") or []),
            create_geo_variants=bool(data.get("create_geo_variants", True)),
            asset_vset_name=(data.get("asset_variant_set") or "geo_variant").strip() or "geo_variant",
            mtl_variants=list(data.get("material_variants") or []),
            mtl_vset_name=(data.get("material_variant_set") or "mtl_variant").strip() or "mtl_variant",
            create_lookdev=bool(data.get("create_lookdev_setup", True)),
            create_light_rig=bool(data.get("create_light_rig", True)),
            enable_env_lights=bool(data.get("enable_env_lights", False)),
            env_light_paths=list(data.get("env_light_paths") or []),
            create_network_boxes=True,
            validate_materials=True,
            skip_geometry_scan=False,
            lowercase_material_names=bool(data.get("lowercase_material_names", False)),
            verbose=True,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetBuilderConfig":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)

    @classmethod
    def from_json_file(cls, filepath: str) -> "AssetBuilderConfig":
        with open(filepath, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json_file(self, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
