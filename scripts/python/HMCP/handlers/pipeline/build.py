"""Pipeline build handlers wrapping custom_tools modules."""

from __future__ import annotations

import json

import hou


def run_batch_lops_build(params: dict) -> dict:
    from tools.lops_asset_builder_v3.lops_asset_builder_cli import build_assets_batch

    config_filepath = params.get("config_filepath")
    configs = params.get("configs")
    verbose = params.get("verbose", True)

    if config_filepath:
        config_filepath = hou.text.expandString(config_filepath)
        with open(config_filepath, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError("Batch config file must contain a JSON array of build configs")
        configs = data
    elif not configs:
        raise ValueError("Provide config_filepath or configs array")

    results = build_assets_batch(configs, verbose=verbose)
    summaries = []
    for result in results:
        output_path = None
        if result.output_node:
            try:
                output_path = result.output_node.path()
            except hou.ObjectWasDeleted:
                pass
        summaries.append({
            "success": result.success,
            "message": result.message,
            "duration": result.duration,
            "output_node": output_path,
            "error": str(result.error) if result.error else None,
        })

    success_count = sum(1 for s in summaries if s["success"])
    return {
        "status": "success" if success_count == len(summaries) else "partial",
        "total": len(summaries),
        "success_count": success_count,
        "results": summaries,
    }
