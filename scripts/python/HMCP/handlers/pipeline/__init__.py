"""Pipeline build handlers."""

from HMCP.handlers.pipeline.build import run_batch_lops_build

COMMANDS = {
    "run_batch_lops_build": run_batch_lops_build,
}

__all__ = list(COMMANDS.keys())
