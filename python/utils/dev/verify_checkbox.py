"""
Verify that the lowercase checkbox exists in the UI
"""

import sys
import importlib

# Force complete reload
modules_to_clear = [
    'modules.misc_utils',
    'tools.material_tools.TexToMtlX_V2.tex_to_mtlx',
    'tools.material_tools.TexToMtlX_V2.txmtlx_config'
]

for mod in modules_to_clear:
    if mod in sys.modules:
        del sys.modules[mod]

# Import fresh
from tools.material_tools.TexToMtlX_V2 import tex_to_mtlx as to_mt

# Create window
print("Creating TexToMtlX V2 window...")
win = to_mt.TxToMtlx()

# Verify checkbox exists
print("\n" + "="*60)
print("Verification Results:")
print("="*60)

if hasattr(win, 'cb_lowercase'):
    print("✅ cb_lowercase checkbox EXISTS")
    print(f"   Text: {win.cb_lowercase.text()}")
    print(f"   Checked: {win.cb_lowercase.isChecked()}")
    print(f"   Visible: {win.cb_lowercase.isVisible()}")
    print(f"   Tooltip: {win.cb_lowercase.toolTip()}")
else:
    print("❌ cb_lowercase checkbox NOT FOUND")
    print("   This means the module wasn't reloaded properly")

if hasattr(win, 'cb_sanitize'):
    print("✅ cb_sanitize checkbox EXISTS")
    print(f"   Text: {win.cb_sanitize.text()}")
else:
    print("❌ cb_sanitize checkbox NOT FOUND")

# Check the layout
print("\n" + "="*60)
print("Checking UI Layout:")
print("="*60)

# Find the sanitize row
for i in range(win.main_layout.count()):
    item = win.main_layout.itemAt(i)
    if item and item.layout():
        layout = item.layout()
        if isinstance(layout, type(win.cb_sanitize.parent().layout())):
            print(f"\nFound layout with {layout.count()} widgets:")
            for j in range(layout.count()):
                widget_item = layout.itemAt(j)
                if widget_item and widget_item.widget():
                    widget = widget_item.widget()
                    widget_type = type(widget).__name__
                    widget_text = getattr(widget, 'text', lambda: 'N/A')()
                    print(f"  [{j}] {widget_type}: {widget_text}")

print("\n" + "="*60)
print("Showing window...")
print("="*60)
win.show()

print("\nWindow is now visible. Check for 'Convert to lowercase' checkbox!")
