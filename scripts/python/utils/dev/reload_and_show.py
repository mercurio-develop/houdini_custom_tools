"""
Reload TexToMtlX V2 and show the window with fresh code.

Run from Houdini Python Shell:
    exec(open(".../reload_and_show.py").read())
"""

import sys
import importlib


def main():
    mod_name = "tools.material_tools.TexToMtlX_V2.tex_to_mtlx"
    if mod_name in sys.modules:
        print("Reloading existing module...")
        importlib.reload(sys.modules[mod_name])
    else:
        print("Loading module for first time...")

    from tools.material_tools.TexToMtlX_V2 import tex_to_mtlx as to_mt

    print("Creating new window with latest code...")
    win = to_mt.TxToMtlx()
    win.show()
    print("✅ Window shown with reloaded code")


if __name__ == "__main__":
    main()
