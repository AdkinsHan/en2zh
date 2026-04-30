#!/usr/bin/env python3
"""
Update manifest.json batch status after translation.

Usage:
    python update_manifest.py <manifest.json> <batch_index> <status>

Status values: pending | translating | translated | merged

Example:
    python update_manifest.py ./notes_batches/manifest.json 1 translated
"""

import json
import os
import sys


def main():
    if len(sys.argv) < 4:
        print("Usage: update_manifest.py <manifest.json> <batch_index> <status>")
        print("Status: pending | translating | translated | merged")
        sys.exit(1)

    manifest_path = sys.argv[1]
    batch_index = int(sys.argv[2])
    new_status = sys.argv[3]

    valid_statuses = {"pending", "translating", "translated", "merged"}
    if new_status not in valid_statuses:
        print(f"Error: Invalid status '{new_status}'. Must be one of: {valid_statuses}")
        sys.exit(1)

    if not os.path.isfile(manifest_path):
        print(f"Error: Manifest not found: {manifest_path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    updated = False
    for batch in manifest.get("batches", []):
        if batch["index"] == batch_index:
            batch["status"] = new_status
            updated = True
            break

    if not updated:
        print(f"Error: Batch index {batch_index} not found in manifest", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"Batch {batch_index} status updated to: {new_status}")

    # Print progress summary
    total = len(manifest["batches"])
    done = sum(1 for b in manifest["batches"] if b["status"] in ("translated", "merged"))
    pending = sum(1 for b in manifest["batches"] if b["status"] == "pending")
    translating = sum(1 for b in manifest["batches"] if b["status"] == "translating")
    print(f"Progress: {done}/{total} translated, {translating} in progress, {pending} pending")


if __name__ == "__main__":
    main()
