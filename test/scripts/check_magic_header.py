#!/usr/bin/env python3
"""
check_magic_header.py
---------------------
Verifies that a Godot PCK file produced by a Godot Secure patched build
does NOT carry the default Godot pack header magic (0x43504447 / "GDPC").

Usage:
    python check_magic_header.py <path/to/file.pck>

Exit codes:
    0 — magic is non-default (Godot Secure patch confirmed)
    1 — magic matches default Godot value (patch was not applied)
    2 — file could not be read or is too small
"""

import struct
import sys

DEFAULT_GODOT_MAGIC = 0x43504447  # "GDPC" in little-endian


def check(pck_path: str) -> int:
    try:
        with open(pck_path, "rb") as fh:
            raw = fh.read(4)
    except OSError as exc:
        print(f"✗  Cannot read '{pck_path}': {exc}")
        return 2

    if len(raw) < 4:
        print(f"✗  File '{pck_path}' is too small to contain a magic header.")
        return 2

    magic = struct.unpack("<I", raw)[0]

    if magic == DEFAULT_GODOT_MAGIC:
        print(
            f"✗  FAIL — PCK has the default Godot magic header "
            f"(0x{magic:08X}). The Godot Secure patch was not applied."
        )
        return 1

    print(
        f"✓  PASS — PCK has a custom magic header "
        f"(0x{magic:08X}). Godot Secure patch confirmed."
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pck_file>")
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
