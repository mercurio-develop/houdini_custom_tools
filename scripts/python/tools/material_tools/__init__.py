"""
Material Tools — canonical import surface.

Prefer:
    from tools.material_tools import MtlxMaterial, TextureFolderScanner, TxToMtlx

Legacy (still supported):
    from tools.tex_to_mtlx import TxToMtlx
"""

from tools.material_tools.TexToMtlX_V2.tex_to_mtlx import (
    MtlxMaterial,
    TextureFolderScanner,
    TxToMtlx,
)

__all__ = ["MtlxMaterial", "TextureFolderScanner", "TxToMtlx"]
