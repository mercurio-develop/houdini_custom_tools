"""
BGEO → KB3D-style USD conversion.

Usage::

    from tools.kb3d_tools.bgeo import analyze_bgeo_folder, convert_bgeo_to_usd
"""

__version__ = "1.0.0"

from .bgeo_analyzer import BGEOAnalyzer, analyze_bgeo_file, analyze_bgeo_folder, print_bgeo_analysis
from .usd_component_builder import USDComponentBuilder, create_component_from_bgeo
from .usd_assembly_builder import USDAssemblyBuilder, create_assembly_from_components

try:
    from .bgeo_to_usd_converter import BGEOtoUSDConverter, convert_bgeo_to_usd
except ImportError:
    BGEOtoUSDConverter = None
    convert_bgeo_to_usd = None

__all__ = [
    "BGEOAnalyzer",
    "USDComponentBuilder",
    "USDAssemblyBuilder",
    "BGEOtoUSDConverter",
    "analyze_bgeo_file",
    "analyze_bgeo_folder",
    "print_bgeo_analysis",
    "create_component_from_bgeo",
    "create_assembly_from_components",
    "convert_bgeo_to_usd",
]
