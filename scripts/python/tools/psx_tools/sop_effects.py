"""SOP node builders for PSX geometry effects."""

from __future__ import annotations

import hou

from modules.misc_utils import _sanitize
from tools.psx_tools.psx_config import PSXAssetConfig

WOBBLE_VEX = '''
// PSX vertex wobble — ported from Blender PSX Retro Tools geometry-nodes logic
vector pos = @P;
vector seed = pos + set(ch("seed"), ch("seed"), ch("seed"));
float hold = max(ch("hold_frames"), 1.0);
float frame_val = floor(@Frame / hold) * hold * ch("frequency");

vector phase = sin(seed + set(frame_val, frame_val, frame_val));
vector step = set(0.3, 0.3, 0.3);
vector wobble = phase - floor(phase / step) * step - set(0.15, 0.15, 0.15);

int axes_mode = chi("axes_mode"); // 0=Z, 1=XYZ, 2=Custom
float gamp = ch("amplitude");
vector amp;
if (axes_mode == 0) {
    amp = set(0, 0, gamp);
} else if (axes_mode == 1) {
    amp = set(gamp, gamp, gamp);
} else {
    amp = set(ch("amp_x"), ch("amp_y"), ch("amp_z"));
}
@P += wobble * amp;
'''

SCREEN_SNAP_VEX = '''
// PSX vertex screen snapping — snap world positions to camera pixel grid
string cam_path = chs("camera_path");
if (!npoints(0)) return;

// Camera world transform
matrix cam_xform = optransform(cam_path);
matrix cam_inv = invert(cam_xform);

vector Pw = @P;
vector Pl = Pw * cam_inv;

// Simple perspective snap using cam focal and aperture (Karma/GL defaults)
float focal = chf(cam_path, "focal");
float aperture = chf(cam_path, "aperture");
float res = max(ch("snap_size"), 1.0);

float z = -Pl.z;
if (z <= 1e-6) return;

float scale = focal / aperture;
vector ndc;
ndc.x = Pl.x * scale / z;
ndc.y = Pl.y * scale / z;

// Snap in normalized device space then back
float snap = 2.0 / res;
ndc.x = round(ndc.x / snap) * snap;
ndc.y = round(ndc.y / snap) * snap;

Pl.x = ndc.x * z / scale;
Pl.y = ndc.y * z / scale;
@P = Pl * cam_xform;
'''


def _add_parm_float(node: hou.Node, name: str, label: str, default: float) -> None:
    ptg = node.parmTemplateGroup()
    if node.parm(name) is not None:
        return
    ptg.append(hou.FloatParmTemplate(name, label, 1, default_value=(default,)))
    node.setParmTemplateGroup(ptg)


def _add_parm_int(node: hou.Node, name: str, label: str, default: int) -> None:
    ptg = node.parmTemplateGroup()
    if node.parm(name) is not None:
        return
    ptg.append(hou.IntParmTemplate(name, label, 1, default_value=(default,)))
    node.setParmTemplateGroup(ptg)


def _add_parm_string(node: hou.Node, name: str, label: str, default: str) -> None:
    ptg = node.parmTemplateGroup()
    if node.parm(name) is not None:
        return
    ptg.append(hou.StringParmTemplate(name, label, 1, default_value=(default,)))
    node.setParmTemplateGroup(ptg)


def create_decimate_node(parent: hou.Node, ratio: float, name: str = "psx_decimate") -> hou.Node:
    node = parent.createNode("polyreduce::2.0", _sanitize(name))
    node.parm("percentage").set(max(0.1, min(ratio * 100.0, 100.0)))
    return node


def create_triangulate_node(parent: hou.Node, name: str = "psx_triangulate") -> hou.Node:
    node = parent.createNode("divide", _sanitize(name))
    node.parm("convex").set(0)
    node.parm("planar").set(0)
    node.parm("triangulate").set(1)
    return node


def create_wobble_node(parent: hou.Node, config: PSXAssetConfig, name: str = "psx_wobble") -> hou.Node:
    node = parent.createNode("attribwrangle", _sanitize(name))
    node.parm("class").set(0)  # points

    axes_map = {"Z": 0, "XYZ": 1, "Custom": 2}
    _add_parm_float(node, "frequency", "Frequency", config.wobble_frequency)
    _add_parm_float(node, "amplitude", "Amplitude", config.wobble_amplitude)
    _add_parm_float(node, "hold_frames", "Hold Frames", config.wobble_hold_frames)
    _add_parm_float(node, "seed", "Seed", config.wobble_seed)
    _add_parm_int(node, "axes_mode", "Axes Mode", axes_map.get(config.wobble_axes, 0))
    _add_parm_float(node, "amp_x", "Amp X", 0.0)
    _add_parm_float(node, "amp_y", "Amp Y", 0.0)
    _add_parm_float(node, "amp_z", "Amp Z", config.wobble_amplitude)

    node.parm("snippet").set(WOBBLE_VEX)
    return node


def create_screen_snap_node(parent: hou.Node, config: PSXAssetConfig, name: str = "psx_screen_snap") -> hou.Node:
    node = parent.createNode("attribwrangle", _sanitize(name))
    node.parm("class").set(0)
    _add_parm_string(node, "camera_path", "Camera Path", config.camera_path)
    _add_parm_float(node, "snap_size", "Snap Size", config.screen_snap_size)
    node.parm("snippet").set(SCREEN_SNAP_VEX)
    return node
