#!/usr/bin/env python3
"""Normalize specified UTF-8 text files without changing other file contents."""

import argparse
from pathlib import Path


def normalize_file(path: Path, target: str) -> bool:
    """Convert line endings in a text file; return whether it was changed.

    Refuse binary and non-UTF-8 input rather than risking corrupted artifacts.
    """
    original = path.read_bytes()
    if b"\x00" in original:
        raise ValueError(f"Not a text file (contains NUL bytes): {path}")
    try:
        original.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Not UTF-8 text: {path}") from exc

    normalized = original.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if target == "crlf":
        normalized = normalized.replace(b"\n", b"\r\n")
    if normalized == original:
        return False
    path.write_bytes(normalized)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Text files to normalize")
    parser.add_argument("--to", choices=("lf", "crlf"), default="lf", help="Target newline style")
    parser.add_argument("--if-exists", action="store_true", help="Skip paths that do not exist")
    args = parser.parse_args()

    changed = 0
    for path in args.paths:
        if args.if_exists and not path.exists():
            print(f"Skipping missing file: {path}")
            continue
        if not path.is_file():
            parser.error(f"Not a regular file: {path}")
        try:
            was_changed = normalize_file(path, args.to)
        except ValueError as exc:
            print(f"Skipping: {exc}")
            continue
        if was_changed:
            changed += 1
            print(f"Normalized to {args.to.upper()}: {path}")
        else:
            print(f"Already {args.to.upper()}: {path}")
    print(f"Line-ending normalization complete: {changed} file(s) changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
