#!/usr/bin/env python3
"""
Merge translated batch files back into a single markdown file.

Usage:
    python merge_md.py <manifest.json> [--output <output.md>]

Reads the manifest.json produced by split_md.py, assembles frontmatter
(if any) and all translated batches in order, and writes the final file.
"""

import argparse
import json
import os
import sys


def read_file(path: str) -> str:
    """Read file with UTF-8 fallback."""
    for encoding in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"Cannot read file with any encoding: {path}")


def main():
    parser = argparse.ArgumentParser(description="Merge translated batches into final markdown")
    parser.add_argument("manifest", help="Path to manifest.json from split_md.py")
    parser.add_argument("--output", default=None, help="Output file path (default: <source>_zh.md in batch dir)")
    args = parser.parse_args()

    if not os.path.isfile(args.manifest):
        print(f"Error: Manifest not found: {args.manifest}", file=sys.stderr)
        sys.exit(1)

    # Load manifest
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    batch_dir = os.path.dirname(args.manifest)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        source_name = manifest.get("source_file", "output.md")
        base = os.path.splitext(source_name)[0]
        output_path = os.path.join(batch_dir, f"{base}_zh.md")

    parts = []

    # Add frontmatter if present
    fm_file = manifest.get("frontmatter_file")
    if fm_file:
        fm_path = os.path.join(batch_dir, fm_file)
        if os.path.isfile(fm_path):
            fm_content = read_file(fm_path)
            parts.append(fm_content.rstrip("\n"))
        else:
            print(f"Warning: Frontmatter file not found: {fm_path}", file=sys.stderr)

    # Assemble batches in order
    batch_entries = sorted(manifest.get("batches", []), key=lambda b: b["index"])

    for entry in batch_entries:
        batch_file = entry["file"]
        batch_path = os.path.join(batch_dir, batch_file)

        if not os.path.isfile(batch_path):
            print(f"Warning: Batch file not found: {batch_path}", file=sys.stderr)
            continue

        content = read_file(batch_path)
        parts.append(content.rstrip("\n"))

    # Join with double newlines
    final_content = "\n\n".join(parts)
    if not final_content.endswith("\n"):
        final_content += "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(final_content)

    print(f"Merged {len(batch_entries)} batch(es) into: {output_path}")


if __name__ == "__main__":
    main()
