#!/usr/bin/env python3
"""
check_magic_header.py
---------------------
Verifies the magic header of a Godot PCK file produced by a Godot Secure
patched build.

Usage:
    python check_magic_header.py <path/to/file.pck> [BASE_TAG]

    BASE_TAG  Optional 4-character ASCII tag passed to the setup job
              (e.g. "BXXY"). When provided the script verifies the PCK
              header matches this exact value rather than just checking
              that it is not the default Godot magic.

Exit codes:
    0 — header matches expected value (or is any non-default value when
        no BASE_TAG is given)
    1 — header is wrong (default Godot value, or does not match BASE_TAG)
    2 — bad arguments or file could not be read
"""

import struct
import sys

DEFAULT_GODOT_MAGIC = 0x43504447  # "GDPC" in little-endian


def tag_to_magic(tag: str) -> int:
    """Convert a 4-char ASCII tag to the little-endian uint32 stored in the PCK."""
    return struct.unpack("<I", tag.encode("ascii"))[0]


def check(pck_path: str, expected_tag: str | None) -> int:
    try:
        with open(pck_path, "rb") as fh:
            raw = fh.read(4)
    except OSError as exc:
        print(f"✗  Cannot read '{pck_path}': {exc}")
        return 2

    if len(raw) < 4:
        print(f"✗  '{pck_path}' is too small to contain a magic header.")
        return 2

    actual = struct.unpack("<I", raw)[0]

    if expected_tag is not None:
        expected = tag_to_magic(expected_tag)
        if actual == expected:
            print(
                f"✓  PASS — PCK magic 0x{actual:08X} matches expected "
                f"base-tag '{expected_tag}'."
            )
            return 0
        elif actual == DEFAULT_GODOT_MAGIC:
            print(
                f"✗  FAIL — PCK has the default Godot magic (0x{actual:08X}). "
                f"The Godot Secure patch was not applied."
            )
        else:
            print(
                f"✗  FAIL — PCK magic 0x{actual:08X} does not match expected "
                f"base-tag '{expected_tag}' (0x{expected:08X}). "
                f"Cross-OS parameter synchronization may have failed."
            )
        return 1

    # No expected tag — just verify it is not the default.
    if actual == DEFAULT_GODOT_MAGIC:
        print(
            f"✗  FAIL — PCK has the default Godot magic (0x{actual:08X}). "
            f"The Godot Secure patch was not applied."
        )
        return 1

    print(
        f"✓  PASS — PCK has a custom magic header (0x{actual:08X}). "
        f"Godot Secure patch confirmed."
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(f"Usage: {sys.argv[0]} <pck_file> [BASE_TAG]")
        sys.exit(2)
    pck = sys.argv[1]
    tag = sys.argv[2] if len(sys.argv) == 3 else None
    if tag is not None and len(tag) != 4:
        print(f"✗  BASE_TAG must be exactly 4 characters, got {len(tag)!r}.")
        sys.exit(2)
    sys.exit(check(pck, tag))
