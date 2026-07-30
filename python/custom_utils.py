import logging
import os


def _reload_module_path_to_name(folder_path: str, py_path: str) -> str:
    rel = os.path.relpath(py_path, folder_path).replace(os.sep, "/")
    if rel.endswith("/__init__.py"):
        return rel[: -len("/__init__.py")].replace("/", ".")
    if rel.endswith(".py"):
        return rel[:-3].replace("/", ".")
    return rel.replace("/", ".")


def _should_skip_module_path(module_path: str, folder_path: str, exclude_names, exclude_paths) -> bool:
    norm = module_path.replace(os.sep, "/")
    rel = os.path.relpath(module_path, folder_path).replace(os.sep, "/")
    parts = rel.split("/")
    if any(part in exclude_names for part in parts):
        return True
    if any(part.startswith(".") and part not in (".", "..") for part in parts):
        return True
    full = os.path.normpath(module_path)
    for ex in exclude_paths:
        ex_norm = os.path.normpath(ex)
        if full == ex_norm or full.startswith(ex_norm + os.sep):
            return True
    excluded_segments = ("/site-packages/", "/dist-packages/", "/.venv/", "/venv/", "/env/")
    return any(seg in norm for seg in excluded_segments)


def reload_packages(kwargs):
    """
    Reload the custom_tools Houdini package and (on Alt+click) Python modules.

    Args:
        kwargs (dict): Houdini shelf kwargs; Alt+click sets ``altclick`` to reload modules.
    """
    import hou
    import importlib
    import os
    import sys
    import json

    folder_path = hou.text.expandString("$CUSTOM_TOOLS/scripts/python")
    package_path = hou.text.expandString("$HOUDINI_USER_PREF_DIR/packages/") + "custom_tools.json"
    hou.ui.reloadPackage(package_path)

    altclick = bool(kwargs.get("altclick"))
    if not altclick:
        hou.hscript("menurefresh")
        _reload_shelves()
        return

    settings = {}
    candidate_paths = [
        os.path.join(folder_path, "reload_settings.json"),
        hou.text.expandString("$HOUDINI_USER_PREF_DIR/custom_tools_reload.json"),
        os.environ.get("CUSTOM_TOOLS_RELOAD_SETTINGS") or os.environ.get("RBW_RELOAD_SETTINGS") or "",
    ]
    for p in candidate_paths:
        if not p:
            continue
        try:
            if os.path.isfile(p):
                with open(p, "r") as f:
                    settings = json.load(f) or {}
                print(f"reload_packages: using settings from {p}")
                break
        except Exception as e:
            print(f"reload_packages: failed to read settings file {p}: {e}")

    exclude_list = settings.get("reload_exclude_dirs", settings.get("exclude_folders", []))
    exclude_names = set()
    exclude_paths = []
    if isinstance(exclude_list, list):
        for item in exclude_list:
            if not isinstance(item, str) or not item.strip():
                continue
            item = item.strip()
            if ("/" not in item) and ("\\" not in item):
                exclude_names.add(item)
            else:
                p = item if os.path.isabs(item) else os.path.normpath(os.path.join(folder_path, item))
                exclude_paths.append(os.path.normpath(p))

    exclude_names |= {".venv", "venv", "env", "site-packages", "dist-packages", "__pycache__"}
    print(
        "reload_packages: excluding folders by name "
        f"{sorted(exclude_names)} and paths {exclude_paths}"
    )

    module_files = []
    package_inits = []
    for root, dirs, files in os.walk(folder_path):
        pruned = []
        for d in dirs:
            full_d = os.path.normpath(os.path.join(root, d))
            if d in exclude_names:
                continue
            if any(full_d.startswith(p) for p in exclude_paths):
                continue
            pruned.append(d)
        dirs[:] = pruned

        for file in files:
            if not file.endswith(".py"):
                continue
            module_path = os.path.join(root, file)
            if _should_skip_module_path(module_path, folder_path, exclude_names, exclude_paths):
                continue
            module_name = _reload_module_path_to_name(folder_path, module_path)
            if module_name.startswith("."):
                continue
            if file == "__init__.py":
                package_inits.append((module_name, module_path))
            else:
                module_files.append((module_name, module_path))

    # Ensure top-level packages exist before reloading submodules.
    for pkg in ("tools", "pipeline", "modules", "ui"):
        pkg_init = os.path.join(folder_path, pkg, "__init__.py")
        if os.path.isfile(pkg_init):
            try:
                importlib.import_module(pkg)
            except Exception as e:
                print(f"reload_packages: warning: could not import package {pkg}: {e}")

    def _reload_one(module_name: str) -> None:
        mod = sys.modules.get(module_name)
        if mod is not None:
            importlib.reload(mod)
            print(f"Reloaded Module: {module_name}")
        else:
            importlib.import_module(module_name)
            print(f"Imported Module: {module_name}")

    # Reload leaf modules first (deepest dotted names), then package __init__ files.
    module_files.sort(key=lambda item: item[0].count("."), reverse=True)
    package_inits.sort(key=lambda item: item[0].count("."), reverse=True)

    for module_name, _path in module_files:
        try:
            _reload_one(module_name)
        except Exception as error:
            print(f"Failed to import or reload the module {module_name}: {error}")

    for module_name, _path in package_inits:
        try:
            _reload_one(module_name)
        except Exception as error:
            print(f"Failed to import or reload the package {module_name}: {error}")

    hou.hscript("menurefresh")
    _reload_shelves()


def _reload_shelves() -> None:
    import hou

    path_shelves = hou.text.expandString("$CUSTOM_TOOLS/toolbar")
    for root, _dir, files in os.walk(path_shelves):
        for file in files:
            if file.endswith(".shelf"):
                hou.shelves.loadFile(os.path.join(root, file))


def check_path_valid(path):
    '''
    This is a fuction that checks if the path is valid.
    :Args:
        path: The path to check
    :return:
        True: if the path is valid
    '''
    import hou
    import os

    ## FIX the path if is using a env variable - $HIP, $HOME, $CUSTOM_TOOLS
    path = os.path.dirname(hou.text.expandString(path))

    ## Check if the path exists
    if os.path.exists(path) and os.access(path, os.R_OK):
        print(f"The path {path} is valid")
        return path
    else:
        print(f"The path {path} is not valid")
        hou.ui.displayMessage(f"The path {path} is not valid. Please try again.", title="Error")

def clean_log():
    print("\n" * 100)



# IF YOU NEED RESET THE LOGGER RUN
# logger.handlers.clear()

def get_logger(name="houdini_debug",log_file_name="houdini_debug.log",level=logging.DEBUG):
    import hou
    import logging
    import os
    import sys


    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.hasHandlers():
        return logger


    active_project = hou.getenv("PROJECT")
    project_path = hou.getenv("JOB")
    project_base_path = os.path.basename(project_path)

    if (active_project and project_base_path) and active_project.lower() == project_base_path.lower():
        folder_path = os.path.join(project_path, "logs")
    else:
        # Ask user to choose a folder if no match
        btn_pressed, values = hou.ui.readMultiInput(
            "Choose Log Folder",
            ("LOG PATH",),
            buttons=('Create', 'Cancel'),
            severity=hou.severityType.Message,
            help="Please provide a path for your logs.",
            title="Select log path",
            initial_contents=("Untitled",)
        )

        if btn_pressed != 0:  # 0 = 'Create' button
            return logger  # Return empty logger if canceled

        folder_path = os.path.join(values[0], "logs")

    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path)
        except Exception as e:
            hou.ui.displayMessage(f"Failed to create log folder: {e}")
            return logger

    log_file_path = os.path.join(folder_path, log_file_name)

    # File Handler
    try:
        file_handler = logging.FileHandler(log_file_path, mode='w')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
        logger.addHandler(file_handler)
    except Exception as e:
        hou.ui.displayMessage(f"FileHandler error: {e}")

    # Console Stream Handler (to Python Shell)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(stream_handler)

    logger.info(f"Logging started in: {log_file_path}")
    return logger
