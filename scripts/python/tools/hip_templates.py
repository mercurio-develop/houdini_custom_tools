"""Merge pre-built HIP templates from ``$CUSTOM_TOOLS/templates``."""

from __future__ import annotations

import os

import hou

TEMPLATES = {
    "asset_builder": {
        "label": "Asset Builder",
        "file": "Asset_Builder_Template.hiplc",
        "pattern": "*component* *material* *domelight*",
    },
    "tops": {
        "label": "TOPs (split export)",
        "file": "TEMPLATE_TOPS.hiplc",
        "pattern": "*",
    },
    "tops_kitbash": {
        "label": "Kitbash library TOPs",
        "file": "KITBASH_LIBRARY_TOPS_TEMPLATE.hiplc",
        "pattern": "*",
    },
    "tops_tasks": {
        "label": "TOP tasks",
        "file": "TEMPLATE_TASKS.hiplc",
        "pattern": "*",
    },
    "department_publish": {
        "label": "Department publish",
        "file": "Asset_Department_Publish.hiplc",
        "pattern": "*",
    },
    "turntable": {
        "label": "Turntable render",
        "file": "turntable_template_v004.hiplc",
        "pattern": "*",
    },
}


def templates_dir() -> str:
    return hou.expandString("$CUSTOM_TOOLS/templates")


def template_path(key: str) -> str:
    if key not in TEMPLATES:
        raise KeyError(f"Unknown template key: {key}. Available: {', '.join(TEMPLATES)}")
    return os.path.join(templates_dir(), TEMPLATES[key]["file"])


def merge_template(
    key: str,
    *,
    pattern: str | None = None,
    overwrite: bool = False,
    ignore_warnings: bool = True,
) -> str:
    """Merge a catalogued HIP template into the current scene. Returns merged file path."""
    meta = TEMPLATES[key]
    path = template_path(key)
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"Template not found:\n{path}\n\nCheck CUSTOM_TOOLS and templates/{meta['file']}"
        )

    merge_pattern = pattern if pattern is not None else meta["pattern"]
    hou.hipFile.merge(path, merge_pattern, overwrite, ignore_warnings)
    return path


def merge_template_with_ui(key: str) -> None:
    """Merge template or show a Houdini error dialog."""
    try:
        path = merge_template(key)
    except FileNotFoundError as exc:
        hou.ui.displayMessage(str(exc), severity=hou.severityType.Error, title=TEMPLATES[key]["label"])
        return
    except Exception as exc:
        hou.ui.displayMessage(
            f"Failed to merge {TEMPLATES[key]['label']}:\n{exc}",
            severity=hou.severityType.Error,
            title=TEMPLATES[key]["label"],
        )
        return

    hou.ui.setStatusMessage(f"Merged template: {path}", severity=hou.severityType.Message)


def show_template_menu(keys: tuple[str, ...] | None = None) -> None:
    """Pick a template from a button menu and merge it."""
    keys = keys or tuple(TEMPLATES)
    labels = [TEMPLATES[k]["label"] for k in keys]
    picked = hou.ui.displayMessage(
        "Choose a HIP template to merge into the current scene:",
        buttons=tuple(labels),
        default_choice=0,
        title="Merge HIP Template",
    )
    if picked < 0 or picked >= len(keys):
        return
    merge_template_with_ui(keys[picked])
