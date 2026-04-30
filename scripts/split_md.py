#!/usr/bin/env python3
"""
Split a markdown file into batches for incremental translation.

Usage:
    python split_md.py <input.md> [--output-dir <dir>] [--batch-size <lines>]

Default batch size: 80 lines (adjustable for large documents).
Outputs numbered batch files and a manifest.json with metadata.

Respects code block (```) and table (|...|) boundaries — never splits
inside a fenced code block or a markdown table.
"""

import argparse
import json
import os
import re
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


def extract_frontmatter(text: str) -> tuple[str, str]:
    """Separate YAML frontmatter from body content."""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[: end + 3], text[end + 3 :].lstrip("\n")
    return "", text


def _is_code_fence(line: str) -> bool:
    """Check if a line opens or closes a fenced code block (``` or ~~~)."""
    stripped = line.strip()
    return bool(re.match(r"^(```|~~~)", stripped))


def _is_table_row(line: str) -> bool:
    """Check if a line belongs to a markdown table."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    # At minimum: | <cell | — must have at least one inner pipe or content
    inner = stripped[1:-1].strip()
    return len(inner) > 0


def _is_table_separator(line: str) -> bool:
    """Check if a line is a table separator row like |---|---|."""
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return False
    inner = stripped[1:-1]
    return bool(re.match(r"^[\s:\-|]+$", inner))


def scan_block_spans(lines: list[str]) -> dict[int, str]:
    """
    Scan all lines and return a mapping: line_index -> block_type.

    block_type is one of:
      - "code"  : inside a fenced code block
      - "table" : inside a markdown table
      - ""      : regular line (not inside any protected block)

    This is used to prevent splitting inside code blocks or tables.
    """
    spans: dict[int, str] = {}
    in_code = False
    in_table = False

    for i, line in enumerate(lines):
        # --- Code fence detection (highest priority) ---
        if _is_code_fence(line):
            if in_code:
                # Closing fence — mark this line as code, then exit
                spans[i] = "code"
                in_code = False
            else:
                # Opening fence — mark this line as code, then enter
                spans[i] = "code"
                in_code = True
            continue

        if in_code:
            spans[i] = "code"
            continue

        # --- Table detection ---
        if _is_table_row(line):
            if in_table:
                spans[i] = "table"
            else:
                # Potential table start — only if next non-blank line is
                # also a table row or a separator (heuristic)
                in_table = True
                spans[i] = "table"
            continue

        if _is_table_separator(line):
            # Separator belongs to the table
            spans[i] = "table"
            continue

        # Blank or non-table line ends the table
        if in_table:
            in_table = False

        spans[i] = ""

    return spans


def find_protected_ranges(lines: list[str], spans: dict[int, str]) -> list[tuple[int, int, str]]:
    """
    Find contiguous ranges of protected blocks.

    Returns a sorted list of (start, end_exclusive, block_type) tuples.
    """
    ranges: list[tuple[int, int, str]] = []
    i = 0
    while i < len(lines):
        btype = spans.get(i, "")
        if btype:
            start = i
            while i < len(lines) and spans.get(i, "") == btype:
                i += 1
            ranges.append((start, i, btype))
        else:
            i += 1
    return ranges


def split_into_sections(lines: list[str], batch_size: int) -> list[list[str]]:
    """
    Split lines into batches, respecting heading, code block, and table boundaries.

    Strategy:
    1. Pre-scan the document to identify code block and table spans.
    2. Accumulate lines until batch_size is reached.
    3. If a heading is encountered and the current batch is ≥60% full,
       split before the heading to keep heading + content together.
    4. NEVER split inside a code block or table — extend the current batch
       to include the entire protected block even if it exceeds batch_size.
    5. Hard boundary at 1.5× batch_size, but only at non-protected boundaries.
    """
    if not lines:
        return []

    # Pre-scan for protected blocks
    spans = scan_block_spans(lines)
    protected_ranges = find_protected_ranges(lines, spans)
    # Build a fast lookup: for any line index, find the protected range it belongs to
    line_to_range: dict[int, tuple[int, int]] = {}
    for start, end, _ in protected_ranges:
        for idx in range(start, end):
            line_to_range[idx] = (start, end)

    batches = []
    current_batch: list[int] = []  # indices into `lines`
    current_len = 0

    def flush_batch():
        nonlocal current_batch, current_len
        if current_batch:
            batches.append([lines[i] for i in current_batch])
            current_batch = []
            current_len = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        is_heading = line.startswith("#")

        # Check if we're at a natural split point (heading) and batch is big enough
        if is_heading and current_len >= batch_size * 0.6 and current_batch:
            flush_batch()
            current_batch.append(i)
            current_len = 1
            i += 1
            continue

        # Check if adding this line would cross into a protected block
        if i in line_to_range:
            rng_start, rng_end = line_to_range[i]
            protected_line_count = rng_end - rng_start

            # If we're at the START of a protected block:
            if i == rng_start:
                # If the protected block alone is huge, we may need to flush
                # the current batch and put the protected block in its own batch
                if current_len + protected_line_count > batch_size * 1.5 and current_len > 0:
                    # Flush current, then add entire protected block to a new batch
                    flush_batch()
                    for j in range(rng_start, rng_end):
                        current_batch.append(j)
                    current_len = rng_end - rng_start
                    i = rng_end
                    # Flush the protected block into its own batch
                    flush_batch()
                    continue
                else:
                    # Add entire protected block to current batch
                    for j in range(rng_start, rng_end):
                        current_batch.append(j)
                    current_len += protected_line_count
                    i = rng_end
                    # Check hard boundary after adding
                    if current_len >= batch_size * 1.5:
                        flush_batch()
                    continue
            else:
                # We're inside a protected block but not at its start —
                # this shouldn't happen with our logic, but handle gracefully
                current_batch.append(i)
                current_len += 1
                i += 1
                continue
        else:
            # Normal line
            current_batch.append(i)
            current_len += 1
            i += 1

        # Hard boundary: if we've exceeded batch_size by a lot, force split
        if current_len >= batch_size * 1.5:
            # Don't split if next line is inside a protected block
            if i < len(lines) and i in line_to_range:
                # Will extend — don't flush yet
                pass
            else:
                flush_batch()

    # Flush remaining
    if current_batch:
        batches.append([lines[idx] for idx in current_batch])

    return batches


def main():
    parser = argparse.ArgumentParser(description="Split markdown into translation batches")
    parser.add_argument("input", help="Input markdown file path")
    parser.add_argument("--output-dir", default=None, help="Directory for batch output files")
    parser.add_argument("--batch-size", type=int, default=80, help="Approximate lines per batch (default: 80)")
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.output_dir:
        out_dir = args.output_dir
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        out_dir = os.path.join(os.path.dirname(args.input) or ".", f"{base}_batches")

    os.makedirs(out_dir, exist_ok=True)

    # Read and parse
    text = read_file(args.input)
    frontmatter, body = extract_frontmatter(text)
    lines = body.split("\n") if body else []

    # Split into batches
    batches = split_into_sections(lines, args.batch_size)
    total_batches = len(batches)

    if total_batches == 0:
        print("Warning: File is empty, no batches created.", file=sys.stderr)
        sys.exit(0)

    # Write batch files
    manifest = {
        "source_file": os.path.basename(args.input),
        "total_batches": total_batches,
        "batch_size": args.batch_size,
        "has_frontmatter": bool(frontmatter),
        "frontmatter_file": None,
        "batches": [],
    }

    # Save frontmatter separately if present
    if frontmatter:
        fm_path = os.path.join(out_dir, "000_frontmatter.md")
        with open(fm_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        manifest["frontmatter_file"] = "000_frontmatter.md"

    for idx, batch_lines in enumerate(batches, 1):
        filename = f"{idx:03d}_batch.md"
        filepath = os.path.join(out_dir, filename)
        content = "\n".join(batch_lines)
        # Ensure trailing newline
        if not content.endswith("\n"):
            content += "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        manifest["batches"].append({
            "index": idx,
            "file": filename,
            "lines": len(batch_lines),
            "status": "pending",  # pending | translating | translated | merged
        })

    # Write manifest
    manifest_path = os.path.join(out_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Split into {total_batches} batch(es)")
    print(f"Output directory: {out_dir}")
    print(f"Manifest: {manifest_path}")
    for b in manifest["batches"]:
        print(f"  Batch {b['index']}: {b['file']} ({b['lines']} lines) [{b['status']}]")


if __name__ == "__main__":
    main()
