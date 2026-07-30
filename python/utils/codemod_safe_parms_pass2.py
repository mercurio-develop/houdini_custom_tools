#!/usr/bin/env python3
"""Second-pass fix for decompiled node scripts after codemod_safe_parms."""

from __future__ import annotations

import re
import sys
from pathlib import Path

IMPORT = (
    "from modules.houdini_node_utils import safe_parm, safe_parm_tuple, unlock_parm, "
    "unlock_parm_tuple, reset_parm, reset_parm_tuple\n"
)

RESET_INLINE = re.compile(
    r"^([ \t]*)reset_parm\(safe_parm\(hou_node, ([^)]+)\), (.+)\)$",
    re.MULTILINE,
)

TUPLE_BLOCK = re.compile(
    r"^([ \t]*)unlock_parm_tuple\(safe_parm_tuple\(hou_node, ([^)]+)\), (.+)\)\n"
    r"\1hou_parm_tuple\.deleteAllKeyframes\(\)\n"
    r"\1hou_parm_tuple\.set\((.+)\)\n"
    r"\1hou_parm_tuple\.setAutoscope\((.+)\)\n",
    re.MULTILINE,
)

KEYFRAME_USE = re.compile(r"hou_parm\.setKeyframe\(")


def fix_keyframes(text: str) -> str:
    """Ensure hou_parm exists before any setKeyframe call."""
    if not KEYFRAME_USE.search(text):
        return text

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    last_parm_expr: str | None = None

    for line in lines:
        m = re.match(r"^([ \t]*)reset_parm\(safe_parm\(hou_node, ([^)]+)\), (.+)\)\s*$", line)
        if m:
            indent, name, rest = m.group(1), m.group(2), m.group(3)
            last_parm_expr = name
            out.append(f"{indent}hou_parm = safe_parm(hou_node, {name})\n")
            out.append(f"{indent}reset_parm(hou_parm, {rest})\n")
            continue

        m2 = re.match(r"^([ \t]*)hou_parm = safe_parm\(hou_node, ([^)]+)\)\s*$", line)
        if m2:
            last_parm_expr = m2.group(2)
            out.append(line)
            continue

        if "hou_parm.setKeyframe" in line and last_parm_expr:
            indent = re.match(r"^([ \t]*)", line).group(1)
            prev = "".join(out[-6:])
            if f"safe_parm(hou_node, {last_parm_expr})" not in prev.split("hou_parm.setKeyframe")[0][-400:]:
                out.append(f"{indent}hou_parm = safe_parm(hou_node, {last_parm_expr})\n")

        out.append(line)

    return "".join(out)


def transform(text: str) -> str:
    if "reset_parm_tuple" not in text:
        text = text.replace(
            "unlock_parm, unlock_parm_tuple, reset_parm\n",
            "unlock_parm, unlock_parm_tuple, reset_parm, reset_parm_tuple\n",
        )

    text = TUPLE_BLOCK.sub(
        lambda m: (
            f"{m.group(1)}hou_parm_tuple = safe_parm_tuple(hou_node, {m.group(2)})\n"
            f"{m.group(1)}reset_parm_tuple(hou_parm_tuple, {m.group(4)}, autoscope={m.group(5)}, locks={m.group(3)})\n"
        ),
        text,
    )

    text = fix_keyframes(text)
    return text


def process_file(path: Path) -> None:
    updated = transform(path.read_text(encoding="utf-8"))
    path.write_text(updated, encoding="utf-8")
    print(f"Fixed {path}")


def main(argv: list[str]) -> int:
    for arg in argv[1:]:
        process_file(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
