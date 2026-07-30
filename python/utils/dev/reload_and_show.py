"""
Reload TexToMtlX V2 and show the window with fresh code.
Run this in Houdini Python Shell:
    execfile("/path/to/reload_and_show.py")
"""

import sys
import importlib

# Force reload of the module
if 'tools.material_tools.TexToMtlX_V2.tex_to_mtlx' in sys.modules:
    print("Reloading existing module...")
    importlib.reload(sys.modules['tools.material_tools.TexToMtlX_V2.tex_to_mtlx'])
else:
    print("Loading module for first time...")

# Import after reload
from tools.material_tools.TexToMtlX_V2 import tex_to_mtlx as to_mt

# Close existing window if any
try:
    if 'win' in globals() and win is not None:
        win.close()
        print("Closed existing window")
except:
    pass

# Create and show new window
print("Creating new window with latest code...")
win = to_mt.TxToMtlx()
win.show()

print("✅ Window shown with reloaded code")
print("\nLook for these checkboxes:")
print("  ☑ Sanitize Material Names")
print("  ☑ Convert to lowercase  ← NEW!")
