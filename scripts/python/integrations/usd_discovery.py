"""Headless USD file discovery for Iconik TOPs ingest and batch tools (no hou)."""

from __future__ import annotations

import fnmatch
import json
import os
import re
from dataclasses import dataclass, field
from typing import Iterable, Literal, Optional

USD_EXTENSIONS = (".usd", ".usda", ".usdc")
USD_ROLE_EXCLUDE_DEFAULT = frozenset({"mtl.usd", "mtl.usdc", "mtl.usda"})
USD_ROLE_FILES = frozenset({
    "geo.usd", "geo.usdc", "geo.usda",
    "payload.usd", "payload.usdc", "payload.usda",
})
DEFAULT_USD_PRIMARY_PRIORITY = (
    "{folder_name}.usd",
    "geo.usd", "geo.usdc", "geo.usda",
    "payload.usd", "payload.usdc", "payload.usda",
)

DiscoveryMode = Literal["primary", "all", "glob"]
OnExistsMode = Literal["skip", "update", "new_version"]


@dataclass
class UsdDiscoveryConfig:
    mode: DiscoveryMode = "primary"
    recursive: bool = True
    include_globs: list[str] = field(default_factory=list)
    exclude_globs: list[str] = field(default_factory=list)
    usd_primary_priority: list[str] = field(default_factory=lambda: list(DEFAULT_USD_PRIMARY_PRIORITY))
    usd_exclude: set[str] = field(default_factory=lambda: set(USD_ROLE_EXCLUDE_DEFAULT))
    max_items: int = 0  # 0 = unlimited


@dataclass(frozen=True)
class UsdDiscoveryHit:
    usd_path: str
    asset_name: str
    folder_path: str
    selection_reason: str
    file_size: int = 0

    @property
    def kb3d_asset_code(self) -> Optional[str]:
        from integrations.identifiers.vfx import infer_kb3d_asset_code

        return infer_kb3d_asset_code(self.asset_name, self.usd_path)


def _load_geo_variant_config() -> dict:
    """Load optional geo_variant_config.json from lops_asset_builder_v3."""
    cfg_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "tools",
        "lops_asset_builder_v3",
        "geo_variant_config.json",
    )
    cfg_path = os.path.normpath(cfg_path)
    if not os.path.isfile(cfg_path):
        return {}
    try:
        with open(cfg_path, encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def default_discovery_config(**overrides) -> UsdDiscoveryConfig:
    """Build config with KB3D defaults from geo_variant_config.json when present."""
    data = _load_geo_variant_config()
    cfg = UsdDiscoveryConfig()
    if isinstance(data.get("usd_exclude"), list):
        cfg.usd_exclude = {str(x).lower() for x in data["usd_exclude"] if str(x)}
    if isinstance(data.get("usd_primary_priority"), list):
        pri = [str(x) for x in data["usd_primary_priority"] if str(x)]
        if pri:
            cfg.usd_primary_priority = pri
    for key, value in overrides.items():
        if hasattr(cfg, key):
            setattr(cfg, key, value)
    return cfg


def _is_usd_file(filename: str) -> bool:
    lower = filename.lower()
    return lower.endswith(USD_EXTENSIONS)


def _usd_basename_lower(filename: str) -> str:
    return filename.lower()


def _is_usd_excluded(filename: str, usd_exclude: set[str]) -> bool:
    return _usd_basename_lower(filename) in usd_exclude


def _is_usd_role_file(filename: str) -> bool:
    return _usd_basename_lower(filename) in USD_ROLE_FILES


def _is_folder_wrapper_usd(filename: str, folder_name: str) -> bool:
    if not _is_usd_file(filename):
        return False
    stem = os.path.splitext(filename)[0]
    return stem.lower() == folder_name.lower()


def _is_kb3d_usd_layout(filenames: list[str], usd_exclude: set[str]) -> bool:
    for filename in filenames:
        if _is_usd_role_file(filename) or _is_usd_excluded(filename, usd_exclude):
            return True
    return False


def select_primary_usd_file(
    folder_path: str,
    usd_files: list[str],
    *,
    usd_primary_priority: list[str],
    usd_exclude: set[str],
) -> Optional[str]:
    """Pick one primary USD for a KB3D-style folder."""
    folder_name = os.path.basename(folder_path.rstrip("/\\"))
    eligible = [f for f in usd_files if not _is_usd_excluded(f, usd_exclude)]

    for pattern in usd_primary_priority:
        pat_lower = pattern.lower()
        if "{folder_name}" in pat_lower:
            for candidate in eligible:
                if _is_folder_wrapper_usd(candidate, folder_name):
                    return candidate
        else:
            for candidate in eligible:
                if _usd_basename_lower(candidate) == pat_lower:
                    return candidate
    return None


def _glob_match(path: str, patterns: Iterable[str]) -> bool:
    from pathlib import PurePath

    norm = path.replace(os.sep, "/")
    pure = PurePath(norm)
    for pattern in patterns:
        pat = pattern.strip().replace("\\", "/")
        if not pat:
            continue
        try:
            if pure.match(pat) or pure.match(f"**/{pat.lstrip('/')}"):
                return True
        except Exception:
            if fnmatch.fnmatch(norm, pat) or fnmatch.fnmatch(os.path.basename(norm), pat):
                return True
    return False


def _should_exclude_path(path: str, cfg: UsdDiscoveryConfig) -> bool:
    if cfg.exclude_globs and _glob_match(path, cfg.exclude_globs):
        return True
    return False


def _hit_from_path(path: str, reason: str) -> UsdDiscoveryHit:
    folder = os.path.dirname(path)
    name = os.path.splitext(os.path.basename(path))[0]
    size = 0
    try:
        size = os.path.getsize(path)
    except OSError:
        pass
    return UsdDiscoveryHit(
        usd_path=os.path.normpath(path),
        asset_name=name,
        folder_path=os.path.normpath(folder),
        selection_reason=reason,
        file_size=size,
    )


def _discover_primary(root: str, cfg: UsdDiscoveryConfig) -> list[UsdDiscoveryHit]:
    hits: list[UsdDiscoveryHit] = []
    seen_paths: set[str] = set()

    def walk(base: str) -> None:
        if cfg.max_items and len(hits) >= cfg.max_items:
            return
        try:
            entries = os.listdir(base)
        except OSError:
            return

        usd_in_folder = [f for f in entries if _is_usd_file(f)]
        if usd_in_folder and _is_kb3d_usd_layout(usd_in_folder, cfg.usd_exclude):
            primary = select_primary_usd_file(
                base,
                usd_in_folder,
                usd_primary_priority=cfg.usd_primary_priority,
                usd_exclude=cfg.usd_exclude,
            )
            if primary:
                full = os.path.normpath(os.path.join(base, primary))
                if not _should_exclude_path(full, cfg) and full not in seen_paths:
                    seen_paths.add(full)
                    hits.append(_hit_from_path(full, "primary_kb3d"))
                    if cfg.max_items and len(hits) >= cfg.max_items:
                        return

        if not cfg.recursive:
            return
        for name in entries:
            if cfg.max_items and len(hits) >= cfg.max_items:
                return
            child = os.path.join(base, name)
            if os.path.isdir(child):
                walk(child)

    walk(os.path.normpath(root))
    return hits


def _discover_all_usd(root: str, cfg: UsdDiscoveryConfig) -> list[UsdDiscoveryHit]:
    hits: list[UsdDiscoveryHit] = []
    root = os.path.normpath(root)

    if cfg.recursive:
        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in filenames:
                if not _is_usd_file(filename):
                    continue
                if _is_usd_excluded(filename, cfg.usd_exclude):
                    continue
                full = os.path.normpath(os.path.join(dirpath, filename))
                if _should_exclude_path(full, cfg):
                    continue
                hits.append(_hit_from_path(full, "all"))
                if cfg.max_items and len(hits) >= cfg.max_items:
                    return hits
    else:
        try:
            filenames = os.listdir(root)
        except OSError:
            return hits
        for filename in filenames:
            if not _is_usd_file(filename):
                continue
            if _is_usd_excluded(filename, cfg.usd_exclude):
                continue
            full = os.path.normpath(os.path.join(root, filename))
            if _should_exclude_path(full, cfg):
                continue
            hits.append(_hit_from_path(full, "all"))
            if cfg.max_items and len(hits) >= cfg.max_items:
                break
    return hits


def _discover_glob(root: str, cfg: UsdDiscoveryConfig) -> list[UsdDiscoveryHit]:
    if not cfg.include_globs:
        return []
    import glob

    hits: list[UsdDiscoveryHit] = []
    seen: set[str] = set()
    root = os.path.normpath(root)

    for pattern in cfg.include_globs:
        pat = pattern.strip()
        if not pat:
            continue
        if not os.path.isabs(pat):
            search = os.path.join(root, pat)
        else:
            search = pat
        for match in glob.glob(search, recursive=cfg.recursive or "**" in pat):
            if not _is_usd_file(os.path.basename(match)):
                continue
            full = os.path.normpath(match)
            if not os.path.isfile(full):
                continue
            if _should_exclude_path(full, cfg):
                continue
            if full in seen:
                continue
            seen.add(full)
            hits.append(_hit_from_path(full, "glob"))
            if cfg.max_items and len(hits) >= cfg.max_items:
                return hits
    return hits


def discover_usd_files(root: str, cfg: Optional[UsdDiscoveryConfig] = None) -> list[UsdDiscoveryHit]:
    """Discover USD files under root according to config mode."""
    cfg = cfg or UsdDiscoveryConfig()
    expanded = os.path.expanduser(os.path.expandvars(root))
    expanded = os.path.normpath(expanded)
    if not os.path.isdir(expanded):
        return []

    if cfg.mode == "primary":
        return _discover_primary(expanded, cfg)
    if cfg.mode == "glob":
        return _discover_glob(expanded, cfg)
    return _discover_all_usd(expanded, cfg)


def content_hash(path: str, *, chunk_size: int = 1024 * 1024) -> str:
    """SHA256 hex digest for idempotent ingest checks."""
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk_size)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()
