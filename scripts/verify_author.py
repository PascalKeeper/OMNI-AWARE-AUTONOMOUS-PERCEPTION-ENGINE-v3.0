#!/usr/bin/env python3
"""Verify that Joseph Rocco Peransi appears in key authorship locations.
Exits with code 1 if the name is missing from required files.
"""
import sys
from pathlib import Path

REQUIRED = [
    "AUTHORS.md",
    "README.md",
    "PRESERVATION.md",
]

NAME = "Joseph Rocco Peransi"
missing = []

for rel in REQUIRED:
    path = Path(rel)
    if not path.exists():
        missing.append(f"{rel} (file missing)")
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    if NAME not in text:
        missing.append(rel)

if missing:
    print("AUTHOR CHECK FAILED — missing or incomplete attribution in:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)

print("AUTHOR CHECK PASSED — Joseph Rocco Peransi is present in required files.")
sys.exit(0)
