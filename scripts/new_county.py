#!/usr/bin/env python3
"""
Scaffold a new county: region config, app directory, and manifest entry.

This replaces the manual "before data arrives" checklist. It:
1. Writes regions/<slug>/config.json
2. Adds the county to counties.json with status "soon" (the landing page
   cards, map, and deploy workflow all read the manifest, so no HTML or
   workflow edits are needed)
3. Copies the shared county app into <slug>/ via sync_counties.py

Usage:
    python3 scripts/new_county.py <slug> <ebird_code> [--name "Display Name"]

Examples:
    python3 scripts/new_county.py emmet US-MI-047
    python3 scripts/new_county.py grand-traverse US-MI-055 --name "Grand Traverse"

When the eBird data arrives:
    1. Barchart .txt          -> regions/<slug>/
    2. EBD download folder    -> regions/<slug>/ebird_basic_dataset/
    3. python3 scripts/run_all.py <slug>
    4. Flip "status" to "live" in counties.json
    5. Commit and push
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path


def project_root():
    return Path(__file__).resolve().parent.parent


def title_case(slug):
    return re.sub(r'(^|[-_])([a-z])',
                  lambda m: (' ' if m.group(1) else '') + m.group(2).upper(),
                  slug)


def build_region_config(slug, name, ebird_code):
    return {
        "region_id": slug,
        "display_name": f"{name} County, Michigan",
        "description": f"Bird occurrence data for {name} County in Michigan.",
        "ebird_region_code": ebird_code,
        "timezone": "America/Detroit",
        "paths": {
            "input_pattern": "ebird_*.txt",
            "output_file": "{region_id}_species_data.json",
            "intermediate_dir": "intermediate",
            "hotspots_dir": "hotspots"
        },
        "thresholds": {},
        "seasonal_weeks": {},
        "display_settings": {
            "copyright_year": datetime.date.today().year,
            "theme_name": "Kirtland's Warbler",
            "about_text": (
                f"Flightcall helps you discover which birds are present in "
                f"{name} County throughout the year, based on eBird observation data."
            )
        },
        "hotspot_guide": {
            "enabled": True,
            "min_checklists_threshold": 10,
            "high_confidence_min": 100,
            "medium_confidence_min": 30
        }
    }


def write_manifest(manifest_path, manifest):
    """Write counties.json keeping the one-line-per-county format."""
    counties = sorted(manifest["counties"], key=lambda c: c["slug"])
    width_slug = max(len(c["slug"]) for c in counties) + 4   # quotes + comma + space
    width_name = max(len(c["name"]) for c in counties) + 4
    lines = []
    for i, c in enumerate(counties):
        slug = f'"{c["slug"]}",'.ljust(width_slug)
        name = f'"{c["name"]}",'.ljust(width_name)
        comma = "," if i < len(counties) - 1 else ""
        lines.append(
            f'    {{ "slug": {slug}"name": {name}'
            f'"ebird_code": "{c["ebird_code"]}", "status": "{c["status"]}" }}{comma}'
        )
    text = (
        '{\n'
        f'  "state": "{manifest["state"]}",\n'
        '  "counties": [\n'
        + "\n".join(lines) + "\n"
        '  ]\n'
        '}\n'
    )
    json.loads(text)  # sanity check before writing
    manifest_path.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new county")
    parser.add_argument("slug", help="County slug, lowercase (e.g. emmet, grand-traverse)")
    parser.add_argument("ebird_code", help="eBird region code (e.g. US-MI-047)")
    parser.add_argument("--name", help='Display name (default: title-cased slug)')
    args = parser.parse_args()

    slug = args.slug
    if not re.fullmatch(r"[a-z][a-z0-9-]*", slug):
        sys.exit(f"❌ Invalid slug '{slug}': use lowercase letters, digits, and hyphens")
    if not re.fullmatch(r"US-[A-Z]{2}-\d{3}", args.ebird_code):
        sys.exit(f"❌ Invalid eBird code '{args.ebird_code}': expected format US-MI-047")

    name = args.name or title_case(slug)
    root = project_root()

    manifest_path = root / "counties.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if any(c["slug"] == slug for c in manifest["counties"]):
        sys.exit(f"❌ County '{slug}' is already in counties.json")

    region_dir = root / "regions" / slug
    config_path = region_dir / "config.json"
    if config_path.exists():
        sys.exit(f"❌ {config_path.relative_to(root)} already exists")

    # 1. Region config
    region_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(build_region_config(slug, name, args.ebird_code), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"✓ Created regions/{slug}/config.json")

    # 2. Manifest entry (status: soon)
    manifest["counties"].append({
        "slug": slug, "name": name,
        "ebird_code": args.ebird_code, "status": "soon",
    })
    write_manifest(manifest_path, manifest)
    print(f"✓ Added {name} County to counties.json (status: soon)")

    # 3. County app directory
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "sync_counties.py")], cwd=root
    )
    if result.returncode != 0:
        sys.exit("❌ sync_counties.py failed")

    print(f"""
✓ {name} County scaffolded. The landing page card, map status, and deploy
  workflow all follow from counties.json — nothing else to edit.

When the eBird data arrives:
  1. Barchart .txt        -> regions/{slug}/
  2. EBD download folder  -> regions/{slug}/ebird_basic_dataset/
  3. python3 scripts/run_all.py {slug}
  4. Flip "status" to "live" in counties.json
  5. Commit and push
""")


if __name__ == "__main__":
    main()
