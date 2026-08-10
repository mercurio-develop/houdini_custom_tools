"""
Create a TOP network for recursive USD discovery and Iconik upload.

Usage (Houdini Python shell or shelf):
    from tools.iconik_tops.create_iconik_ingest_top import create_iconik_ingest_top
    create_iconik_ingest_top()
"""

from __future__ import annotations

import json
import os
import textwrap

import hou


def _prompt_root_folder(initial: str = "") -> str:
    if initial and os.path.isdir(hou.text.expandString(initial)):
        return hou.text.expandString(initial)
    picked = hou.ui.selectFile(
        title="Select library root folder",
        collapse_sequences=False,
        file_type=hou.fileType.Directory,
    )
    if not picked:
        raise hou.Error("Iconik ingest TOPs: no root folder selected.")
    return hou.text.expandString(picked)


def _top_parent(preferred: hou.Node | None = None) -> hou.Node:
    if preferred is not None:
        return preferred
    sel = hou.selectedNodes()
    if sel:
        node = sel[0]
        if node.type().name() == "topnet":
            return node
        parent = node.parent()
        if parent and parent.type().name() == "topnet":
            return parent
        return node.parent()
    stage = hou.node("/stage")
    if stage is not None:
        return stage
    obj = hou.node("/obj")
    if obj is not None:
        return obj
    raise hou.Error("Could not find a parent network for the Iconik ingest TOP net.")


def _set_parm(node: hou.Node, name: str, value) -> None:
    parm = node.parm(name)
    if parm is not None:
        parm.set(value)


def _processor_generate_code() -> str:
    return textwrap.dedent(
        """
        import os
        import sys

        custom_tools = os.environ.get("CUSTOM_TOOLS", "")
        py_root = os.path.join(custom_tools, "scripts", "python") if custom_tools else ""
        if py_root and py_root not in sys.path:
            sys.path.insert(0, py_root)

        node = hou.pwd()
        root = hou.text.expandString(node.parent().parm("root_folder").evalAsString())
        mode = node.parent().parm("scan_mode").evalAsString()
        recursive = bool(node.parent().parm("recursive").eval())
        include_globs = node.parent().parm("include_globs").evalAsString()
        exclude_globs = node.parent().parm("exclude_globs").evalAsString()
        max_items = int(node.parent().parm("max_items").eval())

        from integrations.usd_discovery import UsdDiscoveryConfig, discover_usd_files

        def _split_globs(text):
            return [p.strip() for p in text.replace(",", ";").split(";") if p.strip()]

        cfg = UsdDiscoveryConfig(
            mode=mode,
            recursive=recursive,
            include_globs=_split_globs(include_globs),
            exclude_globs=_split_globs(exclude_globs),
            max_items=max_items,
        )
        hits = discover_usd_files(root, cfg)
        for index, hit in enumerate(hits):
            wi = item_holder.addWorkItem(index=index)
            wi.setStringAttrib("usd_path", hit.usd_path)
            wi.setStringAttrib("asset_name", hit.asset_name)
            wi.setStringAttrib("folder_path", hit.folder_path)
            wi.setStringAttrib("selection_reason", hit.selection_reason)
            wi.setIntAttrib("file_size", int(hit.file_size))
            code = hit.kb3d_asset_code or ""
            wi.setStringAttrib("kb3d_asset_code", code)
        """
    ).strip()


def _upload_script_code() -> str:
    return textwrap.dedent(
        """
        import os
        import sys

        custom_tools = os.environ.get("CUSTOM_TOOLS", "")
        py_root = os.path.join(custom_tools, "scripts", "python") if custom_tools else ""
        if py_root and py_root not in sys.path:
            sys.path.insert(0, py_root)

        topnet = hou.node("../..")
        dry_run = bool(topnet.parm("dry_run").eval())
        on_exists = topnet.parm("on_exists").evalAsString()
        scan_mode = topnet.parm("scan_mode").evalAsString()
        ftrack_task_id = topnet.parm("ftrack_task_id").evalAsString().strip()

        usd_path = work_item.attribValue("usd_path")
        asset_name = work_item.attribValue("asset_name")
        selection_reason = work_item.attribValue("selection_reason")
        kb3d = work_item.attribValue("kb3d_asset_code")

        from integrations.workflows.ingest_usd_to_iconik import IngestRequest, ingest_usd_to_iconik

        extra = {"selection_reason": selection_reason}
        if kb3d:
            extra["kb3d_asset_code"] = kb3d

        result = ingest_usd_to_iconik(
            IngestRequest(
                usd_path=usd_path,
                asset_name=asset_name,
                discovery_mode=scan_mode,
                dry_run=dry_run,
                on_exists=on_exists,
                ftrack_task_id=ftrack_task_id or None,
                extra_metadata=extra,
            )
        )

        work_item.setStringAttrib("upload_status", "ok" if result.success else "failed")
        work_item.setStringAttrib("upload_message", result.message)
        work_item.setStringAttrib("iconik_asset_id", result.iconik_asset_id or "")
        work_item.setIntAttrib("upload_skipped", 1 if result.skipped else 0)

        if result.success:
            work_item.addResultData("iconik_asset_id", result.iconik_asset_id or "")
            if result.skipped:
                work_item.addWarning(result.message)
            else:
                work_item.addMessage(result.message)
        else:
            work_item.addError(result.message)
        """
    ).strip()


def create_iconik_ingest_top(
    root_folder: str = "",
    parent: hou.Node | None = None,
    *,
    scan_mode: str = "primary",
    recursive: bool = True,
    include_globs: str = "",
    exclude_globs: str = "**/mtl.usd;**/mtl.usdc",
    max_items: int = 0,
    dry_run: bool = True,
    on_exists: str = "update",
    ftrack_task_id: str = "",
) -> hou.Node:
    """Build Iconik USD ingest TOP network under parent."""
    root = root_folder or _prompt_root_folder()
    parent = _top_parent(parent)

    topnet = parent.createNode("topnet", "iconik_usd_ingest")
    topnet.setColor(hou.Color(0.2, 0.45, 0.75))

    # Spare parms on topnet for artist control
    ptg = topnet.parmTemplateGroup()
    folder = hou.FolderParmTemplate("ingest_folder", "Iconik Ingest", (
        hou.StringParmTemplate("root_folder", "Root Folder", 1, default_value=(root,)),
        hou.MenuParmTemplate(
            "scan_mode",
            "Scan Mode",
            menu_items=("primary", "all", "glob"),
            menu_labels=("Primary KB3D USD", "All USD", "Glob"),
            default_value=0 if scan_mode == "primary" else (1 if scan_mode == "all" else 2),
        ),
        hou.ToggleParmTemplate("recursive", "Recursive", default_value=recursive),
        hou.StringParmTemplate("include_globs", "Include Globs", 1, default_value=(include_globs,)),
        hou.StringParmTemplate("exclude_globs", "Exclude Globs", 1, default_value=(exclude_globs,)),
        hou.IntParmTemplate("max_items", "Max Items (0=all)", 1, default_value=(max_items,)),
        hou.ToggleParmTemplate("dry_run", "Dry Run", default_value=dry_run),
        hou.MenuParmTemplate(
            "on_exists",
            "On Exists",
            menu_items=("skip", "update", "new_version"),
            menu_labels=("Skip", "Update", "New Version"),
            default_value=1 if on_exists == "update" else 0,
        ),
        hou.StringParmTemplate("ftrack_task_id", "ftrack Task ID (optional)", 1, default_value=(ftrack_task_id,)),
    ))
    ptg.addParmTemplate(folder)
    topnet.setParmTemplateGroup(ptg)

    scan = topnet.createNode("pythonprocessor", "scan_usd")
    upload = topnet.createNode("pythonscript", "upload_iconik")
    try:
        manifest = topnet.createNode("csvoutput", "manifest_csv")
    except hou.OperationFailed:
        manifest = topnet.createNode("null", "manifest_out")

    upload.setInput(0, scan)
    manifest.setInput(0, upload)

    _set_parm(scan, "generate", _processor_generate_code())

    _set_parm(upload, "python", _upload_script_code())

    manifest_path = os.path.join(hou.text.expandString("$HIP"), "iconik_ingest_manifest.csv")
    if manifest.type().name() == "csvoutput":
        _set_parm(manifest, "outputfile", manifest_path)
        for parm_name, value in (
            ("addframecolumn", 0),
            ("addinputcolumn", 0),
            ("addoutputfilecolumn", 0),
        ):
            _set_parm(manifest, parm_name, value)

        attr_map = (
            ("usd_path", "usd_path"),
            ("asset_name", "asset_name"),
            ("iconik_asset_id", "iconik_asset_id"),
            ("upload_status", "upload_status"),
            ("upload_message", "upload_message"),
            ("selection_reason", "selection_reason"),
        )
        for index, (attr, _label) in enumerate(attr_map):
            pname = f"attribute{index + 1}"
            if manifest.parm(pname) is not None:
                _set_parm(manifest, pname, attr)
    else:
        manifest_path = "(work item attributes on upload_iconik — csvoutput unavailable)"

    topnet.layoutChildren()
    manifest.setDisplayFlag(True)
    manifest.setRenderFlag(True)

    hou.ui.displayMessage(
        "Iconik USD Ingest TOP network created.\\n\\n"
        f"Root: {root}\\n"
        f"Manifest: {manifest_path}\\n\\n"
        "Dry run is ON by default — disable on the topnet to upload.\\n"
        "Cook the manifest_csv node when ready.",
        title="Iconik Ingest TOPs",
        severity=hou.severityType.Message,
    )
    return topnet


if __name__ == "__main__":
    create_iconik_ingest_top()
