#!/usr/bin/env python3
"""One-time codemod: make decompiled node setup scripts H22-safe."""

from __future__ import annotations

import re
import sys
from pathlib import Path

IMPORT_LINE = "from modules.houdini_node_utils import safe_parm, safe_parm_tuple, unlock_parm, unlock_parm_tuple, reset_parm\n"

PARM_BLOCK = re.compile(
    r"^([ \t]*)hou_parm = hou_node\.parm\(([^)]+)\)\n"
    r"\1hou_parm\.lock\(False\)\n"
    r"\1hou_parm\.deleteAllKeyframes\(\)\n"
    r"\1hou_parm\.set\((.+)\)\n"
    r"\1hou_parm\.setAutoscope\((.+)\)\n",
    re.MULTILINE,
)

TUPLE_LOCK = re.compile(
    r"^([ \t]*)hou_parm_tuple = hou_node\.parmTuple\(([^)]+)\)\n"
    r"\1hou_parm_tuple\.lock\((.+)\)\n",
    re.MULTILINE,
)

SIMPLE_LOCK = re.compile(
    r"^([ \t]*)hou_parm = hou_node\.parm\(([^)]+)\)\n\1hou_parm\.lock\(False\)\n",
    re.MULTILINE,
)

PARM_TUPLE_REF = re.compile(r"hou_node\.parmTuple\(")
PARM_REF = re.compile(r"hou_node\.parm\(")
KEYFRAME_ON_PARM = re.compile(
    r"^([ \t]*)(hou_parm\.setKeyframe\(hou_keyframe\))\n",
    re.MULTILINE,
)


def _ensure_import(text: str) -> str:
    if "from modules.houdini_node_utils import" in text:
        return text
    if text.startswith("import hou"):
        return text.replace("import hou\n", "import hou\n" + IMPORT_LINE, 1)
    return IMPORT_LINE + text


def _wrap_keyframes(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([ \t]*)hou_parm = (?:safe_parm|hou_node\.parm)\(", line)
        if m:
            indent = m.group(1)
            block_start = len(out)
            out.append(line.replace("hou_node.parm(", "safe_parm(hou_node, ", 1) if "hou_node.parm(" in line else line)
            i += 1
            while i < len(lines):
                cur = lines[i]
                if cur.strip().startswith("hou_parm = ") and "hou_node" in cur:
                    break
                if cur.strip().startswith("# Code for ") and i > block_start + 1:
                    break
                if "hou_parm.setKeyframe" in cur:
                    if not any("if hou_parm is not None" in x for x in out[block_start:]):
                        out.insert(block_start, f"{indent}if hou_parm is not None:\n")
                        for j in range(block_start + 1, len(out)):
                            if out[j].strip() and not out[j].startswith(indent + "if "):
                                out[j] = indent + "    " + out[j].lstrip("\t ")
                        block_start = len(out)
                    out.append(indent + "    " + cur.lstrip())
                    i += 1
                    continue
                if cur.startswith(indent) and cur.strip() and not cur.startswith(indent + "    ") and i > block_start:
                    stripped = cur[len(indent):]
                    if stripped.startswith("hou_parm."):
                        out.append(indent + "    " + stripped)
                        i += 1
                        continue
                break
            continue
        out.append(line.replace("hou_node.parm(", "safe_parm(hou_node, ").replace("hou_node.parmTuple(", "safe_parm_tuple(hou_node, "))
        if "hou_parm.lock(False)" in line:
            out[-1] = out[-1].replace("hou_parm.lock(False)", "unlock_parm(hou_parm)")
        if "hou_parm_tuple.lock(" in line:
            out[-1] = re.sub(
                r"hou_parm_tuple\.lock\((.+)\)",
                r"unlock_parm_tuple(hou_parm_tuple, \1)",
                out[-1],
            )
        i += 1
    return "".join(out)


def transform(text: str) -> str:
    text = _ensure_import(text)

    def repl_block(m: re.Match) -> str:
        indent, name, value, autoscope = m.group(1), m.group(2), m.group(3), m.group(4)
        return (
            f"{indent}reset_parm(safe_parm(hou_node, {name}), {value}, autoscope={autoscope})\n"
        )

    text = PARM_BLOCK.sub(repl_block, text)
    text = TUPLE_LOCK.sub(
        lambda m: f"{m.group(1)}unlock_parm_tuple(safe_parm_tuple(hou_node, {m.group(2)}), {m.group(3)})\n",
        text,
    )
    text = SIMPLE_LOCK.sub(
        lambda m: f"{m.group(1)}unlock_parm(safe_parm(hou_node, {m.group(2)}))\n",
        text,
    )
    text = text.replace("hou_node.parmTuple(", "safe_parm_tuple(hou_node, ")
    text = text.replace("hou_node.parm(", "safe_parm(hou_node, ")
    text = text.replace("hou_parm.lock(False)", "unlock_parm(hou_parm)")
    text = text.replace("hou_parm_tuple.lock(", "unlock_parm_tuple(hou_parm_tuple, ")
    return text


def process_file(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    updated = transform(original)
    path.write_text(updated, encoding="utf-8")
    print(f"Updated {path}")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: codemod_safe_parms.py FILE [FILE ...]")
        return 1
    for arg in argv[1:]:
        process_file(Path(arg))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
