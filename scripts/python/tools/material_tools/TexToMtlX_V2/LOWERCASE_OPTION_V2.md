# Tex To Mtlx V2 - Lowercase Option

## Feature Added

Added a "Convert to lowercase" checkbox to TexToMtlX V2 to control whether material names preserve their original case.

## UI Changes

**Before**:
```
☑ Sanitize Material Names | Drop tokens: base,bake,baked,bake1,pbr
```

**After**:
```
☑ Sanitize Material Names | ☑ Convert to lowercase | Drop tokens: base,bake,baked,bake1,pbr
```

### New Checkbox

**Label**: "Convert to lowercase"
**Default**: Checked (maintains legacy behavior)
**Tooltip**: "When unchecked, preserves original case (e.g., KB3D_MTM_MetalPanelYellowTrimStrapsA)"

## Behavior

| Sanitize | Lowercase | Input | Output |
|----------|-----------|-------|--------|
| ☑ | ☑ | `KB3D_MTM_MetalPanelYellow` | `kb3d_mtm_metalpanelyellow` |
| ☑ | ☐ | `KB3D_MTM_MetalPanelYellow` | `KB3D_MTM_MetalPanelYellow` |
| ☐ | - | `KB3D_MTM_MetalPanelYellow` | `KB3D_MTM_MetalPanelYellow` |

## Code Changes

### 1. UI - Added Checkbox (line 116-118)

```python
self.cb_lowercase = QtWidgets.QCheckBox("Convert to lowercase")
self.cb_lowercase.setChecked(True)
self.cb_lowercase.setToolTip("When unchecked, preserves original case (e.g., KB3D_MTM_MetalPanelYellowTrimStrapsA)")
```

### 2. Updated sanitize_options (line 399-403)

```python
self.sanitize_options = {
    "enabled": self.cb_sanitize.isChecked(),
    "lowercase": self.cb_lowercase.isChecked(),  # NEW
    "drop_tokens": drop_tokens
}
```

### 3. Default Instance Variable (line 62-63)

```python
# Default sanitize options (will be updated from UI when scanning/creating)
self.sanitize_options = {'enabled': True, 'lowercase': True, 'drop_tokens': None}
```

### 4. Updated Material Creation (line 626-627)

```python
lowercase = self.sanitize_options.get('lowercase', True)
canonical = slugify_name_material(self.material_to_create, self.sanitize_options['drop_tokens'], lowercase=lowercase)
```

### 5. Updated Node Creation (line 774-776)

```python
lowercase = self.sanitize_options.get('lowercase', True)
mtlx_standard_surf = subnet_context.createNode("mtlxstandard_surface", slugify_name_material(self.material_to_create + "_mtlxSurface", self.sanitize_options['drop_tokens'], lowercase=lowercase))
mtlx_displacement = subnet_context.createNode("mtlxdisplacement", slugify_name_material(self.material_to_create + "_mtlxDisplacement", self.sanitize_options['drop_tokens'], lowercase=lowercase))
```

### 6. Updated Scanning (line 320-325)

```python
if self.cb_sanitize.isChecked():
    lowercase = self.cb_lowercase.isChecked()
    drop_tokens = None
    if self.le_drop_tokens.text().strip():
        drop_tokens = {t.strip().lower() for t in self.le_drop_tokens.text().split(',') if t.strip()}
    material_name = slugify(material_name, drop_tokens, lowercase=lowercase)
```

### 7. Updated MtlxMaterial Default (line 474)

```python
self.sanitize_options = sanitize_options or {'enabled': True, 'lowercase': True, 'drop_tokens': None}
```

## Updated Functions in misc_utils.py

### slugify_name_material()

Added `lowercase` parameter:

```python
def slugify_name_material(value: str, drop_tokens: Optional[Iterable[str]] = None, lowercase: bool = True) -> str:
    v = (value or "").strip()

    # Optionally convert to lowercase
    if lowercase:
        v = v.lower()

    # ... rest of sanitization ...

    # Preserve uppercase in regex if lowercase=False
    if lowercase:
        v = re.sub(r"[^a-z0-9]+", "_", v)
    else:
        v = re.sub(r"[^a-zA-Z0-9]+", "_", v)
```

## Usage

### Via UI

1. Open TexToMtlX V2
2. Select texture folder
3. **Before scanning**: Set checkboxes:
   - ☑ Sanitize Material Names
   - ☐ **Uncheck "Convert to lowercase"** to preserve case
4. Scan folder - materials will appear with preserved case
5. Select materials and create

### Programmatic

```python
sanitize_options = {
    'enabled': True,
    'lowercase': False,  # Preserve case
    'drop_tokens': {'base', 'bake'}
}

material = MtlxMaterial(
    mat="KB3D_MTM_MetalPanelYellow",
    ...
    sanitize_options=sanitize_options
)
```

## Differences from V1

| Feature | V1 (tex_to_mtlx.py) | V2 (TexToMtlX_V2) |
|---------|---------------------|-------------------|
| **UI Location** | Dialog on create | Main window checkboxes |
| **When Set** | On material creation | Before scanning + creating |
| **Scanning** | Uses instance var | Uses current UI state |
| **Function Used** | `slugify()` | `slugify_name_material()` |

## Integration

Works seamlessly with:
- **Asset Library Builder v1.1.0** - Direct name matching
- **LOPS Asset Builder v3** - FBX naming preservation
- **Complete Pipeline** - 1:1 naming throughout

## Backward Compatibility

✅ **Fully backward compatible**:
- Checkbox defaults to checked (lowercase)
- Existing workflows unchanged
- Legacy behavior preserved

## Files Modified

1. **tools/material_tools/TexToMtlX_V2/tex_to_mtlx.py**
   - Added lowercase checkbox (line 116-118)
   - Updated sanitize_options (line 399-403, 474)
   - Updated material creation (line 626-627)
   - Updated node creation (line 774-776)
   - Updated scanning (line 320-325)

2. **modules/misc_utils.py**
   - Updated `slugify_name_material()` with lowercase parameter

## Summary

TexToMtlX V2 now has the same lowercase control as V1, allowing users to preserve FBX naming conventions throughout the entire pipeline while maintaining full backward compatibility.

---

**Added**: 2025-10-31
**Version**: V2
**Backward Compatible**: Yes (defaults to lowercase)
