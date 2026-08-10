"""Pipeline build handlers."""

from HMCP.handlers.pipeline.build import build_library_from_parts, run_batch_lops_build

COMMANDS = {
    "run_batch_lops_build": run_batch_lops_build,
    "build_library_from_parts": build_library_from_parts,
}

__all__ = list(COMMANDS.keys())
