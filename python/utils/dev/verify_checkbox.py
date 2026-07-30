"""
Verify that the lowercase checkbox exists in the UI.

Run from Houdini Python Shell:
    exec(open(".../verify_checkbox.py").read())
"""

import sys
import importlib


def main():
    modules_to_clear = [
        "modules.misc_utils",
        "tools.material_tools.TexToMtlX_V2.tex_to_mtlx",
        "tools.material_tools.TexToMtlX_V2.txmtlx_config",
    ]

    for mod in modules_to_clear:
        if mod in sys.modules:
            del sys.modules[mod]

    from tools.material_tools.TexToMtlX_V2 import tex_to_mtlx as to_mt

    print("Creating TexToMtlX V2 window...")
    win = to_mt.TxToMtlx()

    print("\n" + "=" * 60)
    print("Verification Results:")
    print("=" * 60)

    if hasattr(win, "cb_lowercase"):
        print("✅ cb_lowercase checkbox EXISTS")
        print(f"   Text: {win.cb_lowercase.text()}")
        print(f"   Checked: {win.cb_lowercase.isChecked()}")
    else:
        print("❌ cb_lowercase checkbox NOT FOUND")

    win.show()
    print("\nWindow is now visible.")


if __name__ == "__main__":
    main()
