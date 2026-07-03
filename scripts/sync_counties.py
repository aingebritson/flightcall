#!/usr/bin/env python3
"""
Sync the shared county app files to every county directory.

The county app (HTML/JS/CSS) is county-agnostic: pages derive the county slug
from the URL path and the display name from the root counties.json manifest.
washtenaw/ is the canonical copy — edit the app there, then run this script
to propagate the files to every other county listed in counties.json.

Everything is copied except data/ (per-county pipeline output) and junk files.

Usage:
    python3 scripts/sync_counties.py           # sync all counties
    python3 scripts/sync_counties.py --check   # report differences, change nothing
"""

import argparse
import filecmp
import json
import shutil
import sys
from pathlib import Path

CANONICAL = "washtenaw"
EXCLUDE_DIRS = {"data"}
EXCLUDE_FILES = {".DS_Store"}


def project_root():
    return Path(__file__).resolve().parent.parent


def app_files(source):
    """Yield county-app file paths relative to the county directory."""
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(source)
        if rel.parts[0] in EXCLUDE_DIRS or rel.name in EXCLUDE_FILES:
            continue
        yield rel


def main():
    parser = argparse.ArgumentParser(description="Sync county app files from the canonical copy")
    parser.add_argument("--check", action="store_true",
                        help="Report out-of-sync files without changing anything")
    args = parser.parse_args()

    root = project_root()
    source = root / CANONICAL

    manifest_path = root / "counties.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    slugs = [c["slug"] for c in manifest["counties"] if c["slug"] != CANONICAL]

    rel_files = list(app_files(source))
    print(f"Canonical app: {CANONICAL}/ ({len(rel_files)} files)")

    out_of_sync = 0
    for slug in slugs:
        dest = root / slug
        dest.mkdir(exist_ok=True)
        (dest / "data").mkdir(exist_ok=True)

        changed = []
        for rel in rel_files:
            src_file = source / rel
            dst_file = dest / rel
            if dst_file.exists() and filecmp.cmp(src_file, dst_file, shallow=False):
                continue
            changed.append(rel)
            if not args.check:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)

        # Remove stray app files that no longer exist in the canonical copy
        for rel in app_files(dest):
            if rel not in rel_files:
                changed.append(rel)
                if not args.check:
                    (dest / rel).unlink()

        out_of_sync += len(changed)
        status = "would update" if args.check else "updated"
        detail = f"{status} {len(changed)}" if changed else "in sync"
        print(f"  {slug}: {detail}")

    if args.check and out_of_sync:
        print(f"\n{out_of_sync} file(s) out of sync. Run without --check to fix.")
        sys.exit(1)
    print("\n✓ Done")


if __name__ == "__main__":
    main()
