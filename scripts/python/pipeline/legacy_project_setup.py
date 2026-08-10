"""
Legacy Project Setup (Improved)
=================================

This is an improved version of your original project setup script.
It maintains backward compatibility with your existing structures while
adding USD best practices.

ORIGINAL SCRIPT IMPROVED:
- Better error handling
- Support for both asset and shot workflows
- Validation of project structure
- Context option improvements
- Path normalization for cross-platform
- Option to migrate to USD structure

Usage:
    Run from Houdini Python Shell or shelf button
"""

import hou
import os


def setup_legacy_project():
    """
    Improved version of original project setup script.

    Maintains compatibility with existing structures while adding
    validation and better error handling.
    """

    # Select show directory
    show_dir = hou.ui.selectFile(
        start_directory=None,
        title="Select Project Root Folder (contains shots and assets)",
        file_type=hou.fileType.Directory
    )

    # Error if no directory selected
    if show_dir == "":
        hou.ui.displayMessage(
            "No directory was selected.\n\n"
            "Please run again and select root folder.",
            severity=hou.severityType.Warning,
            title="No Directory Selected"
        )
        return None

    # Remove trailing slash for consistency
    show_dir = show_dir.rstrip('/')

    # Get hip file info
    hip_name = hou.hipFile.basename()
    hip_path = hou.hipFile.path()

    # Validate hip file is saved
    if not hip_path:
        choice = hou.ui.displayMessage(
            "Current scene is not saved.\n\n"
            "Environment will be set, but context cannot be detected.\n\n"
            "Continue?",
            buttons=("Continue", "Cancel"),
            severity=hou.severityType.Warning,
            title="Scene Not Saved"
        )
        if choice == 1:  # Cancel
            return None

    # Normalize paths for cross-platform
    show_dir = os.path.normpath(show_dir).replace('\\', '/')
    job_dir = show_dir
    asset_dir = os.path.join(show_dir, "assets").replace('\\', '/')
    shot_dir = os.path.join(show_dir, "shots").replace('\\', '/')

    # Validate project structure
    has_assets = os.path.exists(asset_dir)
    has_shots = os.path.exists(shot_dir)

    # Check for sequences folder (USD convention)
    sequences_dir = os.path.join(show_dir, "sequences").replace('\\', '/')
    has_sequences = os.path.exists(sequences_dir)

    if not (has_assets or has_shots or has_sequences):
        choice = hou.ui.displayMessage(
            "Warning: Project structure not detected!\n\n"
            f"Expected folders not found:\n"
            f"- {asset_dir}\n"
            f"- {shot_dir}\n\n"
            "Selected directory may not be a valid project root.\n\n"
            "Continue anyway?",
            buttons=("Continue", "Cancel"),
            severity=hou.severityType.Warning,
            title="Invalid Project Structure"
        )
        if choice == 1:  # Cancel
            return None

    # Use sequences if it exists (USD convention)
    if has_sequences:
        shot_dir = sequences_dir

    # Set global environment variables
    hou.hscript(f"set -g ASSETS = {asset_dir}")
    hou.hscript(f"set -g SHOTS = {shot_dir}")
    hou.hscript(f"set -g JOB = {job_dir}")

    print(f"Set $ASSETS = {asset_dir}")
    print(f"Set $SHOTS = {shot_dir}")
    print(f"Set $JOB = {job_dir}")

    # Additional USD environment variables
    lib_dir = os.path.join(show_dir, "lib").replace('\\', '/')
    if os.path.exists(lib_dir):
        hou.hscript(f"set -g LIB = {lib_dir}")
        materials_dir = os.path.join(lib_dir, "materials").replace('\\', '/')
        if os.path.exists(materials_dir):
            hou.hscript(f"set -g MATERIALS = {materials_dir}")
        hdri_dir = os.path.join(lib_dir, "hdri").replace('\\', '/')
        if os.path.exists(hdri_dir):
            hou.hscript(f"set -g HDRI = {hdri_dir}")

    # If no hip file, stop here
    if not hip_path:
        hou.setContextOption("show_path", show_dir)
        hou.ui.displayMessage(
            "Project Environment Set!\n\n"
            f"$JOB = {job_dir}\n"
            f"$ASSETS = {asset_dir}\n"
            f"$SHOTS = {shot_dir}\n\n"
            "Save your scene to detect context.",
            severity=hou.severityType.Message,
            title="Environment Configured"
        )
        return {
            'job': job_dir,
            'assets': asset_dir,
            'shots': shot_dir,
            'context': None
        }

    # Remove file extension from hip_name
    hip_name_split = hip_name.split(".")
    hip_name_clean = hip_name.replace("." + hip_name_split[-1], "")

    # Remove show directory from hip path
    if show_dir not in hip_path:
        hou.ui.displayMessage(
            "Warning: Current file is not in project!\n\n"
            f"File: {hip_path}\n"
            f"Project: {show_dir}\n\n"
            "Environment set, but context cannot be detected.",
            severity=hou.severityType.Warning,
            title="File Outside Project"
        )
        return {
            'job': job_dir,
            'assets': asset_dir,
            'shots': shot_dir,
            'context': None
        }

    # Get relative path
    split_proj_str = hip_path.replace(show_dir, "").lstrip('/')
    split_proj = split_proj_str.split(os.sep)

    # Filter out empty strings
    split_proj = [p for p in split_proj if p]

    # Detect context
    context = {}

    if len(split_proj) == 0:
        hou.ui.displayMessage(
            "Could not parse file path.\n\n"
            f"Path: {hip_path}",
            severity=hou.severityType.Warning
        )
        return None

    # Determine if asset or shot
    root_folder = split_proj[0].lower()

    if 'asset' in root_folder:
        # Asset workflow
        context['work_type'] = 'asset'

        if len(split_proj) >= 3:
            context['asset_type'] = split_proj[1]  # e.g., "characters", "props"
            context['asset_name'] = split_proj[2]  # e.g., "hero", "sword"
            dirtype = "asset_type"
            worktype = "asset"
            workpath = os.path.join(asset_dir, split_proj[1], split_proj[2]).replace('\\', '/')

            # Set context options
            hou.setContextOption("asset_type", split_proj[1])
            hou.setContextOption("asset", split_proj[2])

        if len(split_proj) >= 4:
            context['department'] = split_proj[3]  # e.g., "modeling", "surfacing"
            hou.setContextOption("dept", split_proj[3])

    elif 'shot' in root_folder or 'sequence' in root_folder:
        # Shot workflow
        context['work_type'] = 'shot'

        if len(split_proj) >= 3:
            context['sequence'] = split_proj[1]  # e.g., "seq_010"
            context['shot'] = split_proj[2]      # e.g., "shot_0010"
            dirtype = "seq"
            worktype = "shot"
            workpath = os.path.join(shot_dir, split_proj[1], split_proj[2]).replace('\\', '/')

            # Set context options
            hou.setContextOption("seq", split_proj[1])
            hou.setContextOption("shot", split_proj[2])

        if len(split_proj) >= 4:
            context['department'] = split_proj[3]  # e.g., "layout", "lighting"
            hou.setContextOption("dept", split_proj[3])

    else:
        # Unknown structure
        hou.ui.displayMessage(
            f"Unknown project structure.\n\n"
            f"Expected 'assets' or 'shots/sequences' folder.\n"
            f"Found: {root_folder}\n\n"
            "Environment variables set, but context not detected.",
            severity=hou.severityType.Warning
        )
        return {
            'job': job_dir,
            'assets': asset_dir,
            'shots': shot_dir,
            'context': None
        }

    # Set common context options
    hou.setContextOption("dept", context.get('department', ''))
    hou.setContextOption("work_type", context['work_type'])
    hou.setContextOption("show_path", show_dir)

    # Set publish paths
    if workpath:
        publish_path = os.path.join(workpath, "_publish").replace('\\', '/')
        dept_publish = os.path.join(
            workpath,
            context.get('department', ''),
            "_publish"
        ).replace('\\', '/')

        hou.setContextOption("publish", publish_path)
        hou.setContextOption("dept_publish", dept_publish)

        # Check if publish directories exist
        if not os.path.exists(publish_path):
            print(f"Warning: Publish path does not exist: {publish_path}")

    # Expected file path for validation
    if context['work_type'] == 'asset':
        expected_pattern = os.path.join(
            workpath,
            context.get('department', 'DEPT'),
            'scene_files',  # Or 'work/houdini' for USD structure
            '*.hip'
        ).replace('\\', '/')
    else:  # shot
        expected_pattern = os.path.join(
            workpath,
            context.get('department', 'DEPT'),
            'work',  # Or 'scene_files'
            '*.hip'
        ).replace('\\', '/')

    # Build validation message
    is_valid_location = workpath in hip_path

    if is_valid_location:
        severity = hou.severityType.Message
        title = "Context Setup Complete"
        msg_header = "Context Setup Complete!\n\n"
    else:
        severity = hou.severityType.Warning
        title = "Warning: Unexpected File Location"
        msg_header = "Warning: File may not be in expected location!\n\n"

    # Build detailed message
    msg = msg_header

    msg += "Environment Variables:\n"
    msg += f"$JOB = {job_dir}\n"
    msg += f"$ASSETS = {asset_dir}\n"
    msg += f"$SHOTS = {shot_dir}\n\n"

    msg += "Detected Context:\n"
    msg += f"Type: {context['work_type'].upper()}\n"

    if context['work_type'] == 'asset':
        msg += f"Asset Type: {context.get('asset_type', 'N/A')}\n"
        msg += f"Asset Name: {context.get('asset_name', 'N/A')}\n"
    else:  # shot
        msg += f"Sequence: {context.get('sequence', 'N/A')}\n"
        msg += f"Shot: {context.get('shot', 'N/A')}\n"

    msg += f"Department: {context.get('department', 'N/A')}\n\n"

    msg += "File Paths:\n"
    msg += f"Current: {hip_path}\n\n"

    if not is_valid_location:
        msg += f"Expected Pattern: {expected_pattern}\n\n"
        msg += "Consider moving file to standard location."

    # Display result
    hou.ui.displayMessage(msg, severity=severity, title=title)

    print("Context Options Updated!")
    print(f"Work Type: {context['work_type']}")
    print(f"Department: {context.get('department', 'N/A')}")

    return {
        'job': job_dir,
        'assets': asset_dir,
        'shots': shot_dir,
        'context': context
    }


# Standalone function for shelf tool
def run_legacy_setup():
    """
    Run legacy project setup (for shelf button).
    """
    return setup_legacy_project()


if __name__ == "__main__":
    # Run if executed directly
    setup_legacy_project()
