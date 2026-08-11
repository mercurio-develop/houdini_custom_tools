#!/usr/bin/env python3
"""Unit tests for KB3D USD primary file selection in AssetScanner (no Houdini)."""

import importlib.util
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock

# Mock Houdini / Qt deps before importing batch_asset_builder
for _mod in (
    'hou',
    'PySide6',
    'PySide6.QtWidgets',
    'PySide6.QtCore',
    'PySide6.QtGui',
):
    sys.modules.setdefault(_mod, MagicMock())

sys.modules.setdefault('ui', MagicMock())
sys.modules.setdefault('ui.houdini_theme', MagicMock())

# Stub tools.lops_asset_builder_v3 package so __init__.py (hou) is never loaded
_tools_pkg = types.ModuleType('tools')
_lops_pkg = types.ModuleType('tools.lops_asset_builder_v3')
_lops_pkg.lops_asset_builder_cli = MagicMock()
_cli_mod = types.ModuleType('tools.lops_asset_builder_v3.lops_asset_builder_cli')
_ui_mod = types.ModuleType('tools.lops_asset_builder_v3.asset_builder_ui')
_ui_mod.SimpleProgressDialog = MagicMock()
_tex_mod = types.ModuleType('tools.lops_asset_builder_v3.texture_variant_detector')
_tex_mod.TextureVariantDetector = MagicMock()
sys.modules['tools'] = _tools_pkg
sys.modules['tools.lops_asset_builder_v3'] = _lops_pkg
sys.modules['tools.lops_asset_builder_v3.lops_asset_builder_cli'] = _cli_mod
sys.modules['tools.lops_asset_builder_v3.asset_builder_ui'] = _ui_mod
sys.modules['tools.lops_asset_builder_v3.texture_variant_detector'] = _tex_mod

TOOLS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if TOOLS_ROOT not in sys.path:
    sys.path.insert(0, TOOLS_ROOT)

_PKG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_BATCH_PATH = os.path.join(_PKG_DIR, 'batch_asset_builder.py')
_spec = importlib.util.spec_from_file_location(
    'batch_asset_builder_standalone', _BATCH_PATH
)
_batch_mod = importlib.util.module_from_spec(_spec)
sys.modules['batch_asset_builder_standalone'] = _batch_mod
assert _spec.loader is not None
_spec.loader.exec_module(_batch_mod)
AssetScanner = _batch_mod.AssetScanner


def _touch(folder: str, *names: str) -> list:
    for name in names:
        path = os.path.join(folder, name)
        with open(path, 'w') as f:
            f.write('')
    return list(names)


class TestSelectPrimaryGeometryFile(unittest.TestCase):
    def setUp(self):
        self.scanner = AssetScanner()

    def test_wrapper_beats_geo_and_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'MyAsset')
            os.makedirs(asset_dir)
            files = _touch(
                asset_dir,
                'MyAsset.usd',
                'geo.usd',
                'payload.usd',
                'mtl.usd',
            )
            primary, variants = self.scanner._select_primary_geometry_file(
                asset_dir, files
            )
            self.assertEqual(primary, 'MyAsset.usd')
            self.assertEqual(variants, [])

    def test_geo_beats_payload_when_no_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'MyAsset')
            os.makedirs(asset_dir)
            files = _touch(asset_dir, 'geo.usd', 'payload.usd')
            primary, variants = self.scanner._select_primary_geometry_file(
                asset_dir, files
            )
            self.assertEqual(primary, 'geo.usd')
            self.assertEqual(variants, [])

    def test_mtl_excluded_from_primary_and_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'MyAsset')
            os.makedirs(asset_dir)
            files = _touch(asset_dir, 'geo.usd', 'mtl.usd')
            primary, variants = self.scanner._select_primary_geometry_file(
                asset_dir, files
            )
            self.assertEqual(primary, 'geo.usd')
            self.assertNotIn('mtl.usd', variants)

    def test_lod_variant_usd_in_kb3d_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'MyAsset')
            os.makedirs(asset_dir)
            files = _touch(
                asset_dir,
                'MyAsset.usd',
                'geo.usd',
                'payload.usd',
                'MyAsset_high.usd',
            )
            primary, variants = self.scanner._select_primary_geometry_file(
                asset_dir, files
            )
            self.assertEqual(primary, 'MyAsset.usd')
            self.assertEqual(variants, ['MyAsset_high.usd'])


class TestAnalyzeKb3dFolder(unittest.TestCase):
    def setUp(self):
        self.scanner = AssetScanner()

    def test_one_asset_per_folder_with_wrapper(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'SciFi_Panel_A')
            os.makedirs(asset_dir)
            geo_files = _touch(
                asset_dir,
                'SciFi_Panel_A.usd',
                'geo.usd',
                'payload.usd',
                'mtl.usd',
            )
            self.scanner._analyze_kb3d_folder(asset_dir, geo_files)
            self.assertEqual(len(self.scanner.detected_assets), 1)
            asset = self.scanner.detected_assets[0]
            self.assertEqual(asset.name, 'SciFi_Panel_A')
            self.assertTrue(asset.main_file.endswith('SciFi_Panel_A.usd'))
            self.assertEqual(asset.geo_variants, [])

    def test_folder_name_as_asset_name_fallback_geo(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'MyAsset')
            os.makedirs(asset_dir)
            geo_files = _touch(asset_dir, 'geo.usd', 'payload.usd')
            self.scanner._analyze_kb3d_folder(asset_dir, geo_files)
            self.assertEqual(len(self.scanner.detected_assets), 1)
            asset = self.scanner.detected_assets[0]
            self.assertEqual(asset.name, 'MyAsset')
            self.assertTrue(asset.main_file.endswith('geo.usd'))

    def test_analyze_folder_routes_kb3d_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            asset_dir = os.path.join(tmp, 'Panel_B')
            os.makedirs(asset_dir)
            geo_files = _touch(
                asset_dir,
                'Panel_B.usd',
                'geo.usd',
                'payload.usd',
                'mtl.usd',
            )
            self.scanner._analyze_folder(asset_dir, geo_files)
            self.assertEqual(len(self.scanner.detected_assets), 1)
            self.assertEqual(self.scanner.detected_assets[0].name, 'Panel_B')


class TestIsKb3dUsdLayout(unittest.TestCase):
    def setUp(self):
        self.scanner = AssetScanner()

    def test_detects_role_files(self):
        self.assertTrue(
            self.scanner._is_kb3d_usd_layout(['geo.usd', 'payload.usd'])
        )

    def test_detects_mtl_only(self):
        self.assertTrue(self.scanner._is_kb3d_usd_layout(['mtl.usd']))

    def test_plain_abc_not_kb3d(self):
        self.assertFalse(
            self.scanner._is_kb3d_usd_layout(['MyAsset.abc', 'MyAsset_high.abc'])
        )


if __name__ == '__main__':
    unittest.main()
