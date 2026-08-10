"""Backward-compatible entry point for the Houdini MaterialX UI (TexToMtlX V2).

Canonical import:
    from tools.material_tools import MtlxMaterial, TextureFolderScanner, TxToMtlx
"""

from tools.material_tools import MtlxMaterial, TextureFolderScanner, TxToMtlx

__all__ = ["MtlxMaterial", "TextureFolderScanner", "TxToMtlx"]
