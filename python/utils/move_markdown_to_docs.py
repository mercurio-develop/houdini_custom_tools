import os
import shutil
from pathlib import Path

# Project root assumed to be the scripts/python directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"

# Ensure docs directory exists
DOCS_ROOT.mkdir(parents=True, exist_ok=True)

EXCLUDE_DIRS = {
    str(DOCS_ROOT.resolve()),  # skip anything already inside docs/
}

# Files to skip by exact filename (case-insensitive)
SKIP_FILENAMES = {"readme.md"}

# Gather candidates
moved = []
skipped = []
errors = []

for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
    # Normalize path
    dirpath_p = Path(dirpath)

    # Skip hidden and venv/dist/cache folders to be safe
    parts_lower = {p.lower() for p in dirpath_p.parts}
    if any(p in parts_lower for p in {".git", "__pycache__", ".venv", "venv", "build", "dist"}):
        continue

    # Skip docs directory
    if str(Path(dirpath).resolve()).startswith(str(DOCS_ROOT.resolve())):
        continue

    for fname in filenames:
        if fname.lower().endswith(".md"):
            # Skip top-level or tool readmes explicitly named README.md
            if fname.lower() in SKIP_FILENAMES:
                skipped.append(str(Path(dirpath) / fname))
                continue

            src = Path(dirpath) / fname

            # Build destination path preserving the relative structure from project root
            rel_path = src.relative_to(PROJECT_ROOT)
            dst = DOCS_ROOT / rel_path

            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)

            try:
                # If destination already exists with same content, skip; if different, keep both by renaming
                if dst.exists():
                    try:
                        if src.read_bytes() == dst.read_bytes():
                            # Same content; remove source and skip duplicate
                            src.unlink()
                            skipped.append(f"DUPLICATE-SAME: {src} -> {dst}")
                            continue
                        else:
                            # Different content; create a new filename with suffix
                            stem = dst.stem
                            suffix = dst.suffix
                            i = 1
                            while True:
                                alt = dst.with_name(f"{stem}_moved{i}{suffix}")
                                if not alt.exists():
                                    dst = alt
                                    break
                                i += 1
                    except Exception:
                        # If read fails, fall back to appending suffix
                        stem = dst.stem
                        suffix = dst.suffix
                        i = 1
                        while True:
                            alt = dst.with_name(f"{stem}_moved{i}{suffix}")
                            if not alt.exists():
                                dst = alt
                                break
                            i += 1

                # Move the file
                shutil.move(str(src), str(dst))
                moved.append((str(src), str(dst)))
            except Exception as e:
                errors.append((str(src), str(dst), str(e)))

# Write a small report to console
print(f"Docs root: {DOCS_ROOT}")
print(f"Moved files: {len(moved)}")
for s, d in moved[:50]:
    print(f"  Moved: {s} -> {d}")
if len(moved) > 50:
    print(f"  ... and {len(moved)-50} more")
print(f"Skipped files: {len(skipped)}")
print(f"Errors: {len(errors)}")
for s, d, e in errors[:20]:
    print(f"  Error: {s} -> {d}: {e}")
