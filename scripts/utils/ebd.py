"""Locate the eBird Basic Dataset directory for a region.

eBird ships EBD downloads in a release-named folder (e.g.
``ebd_US-MI-163_smp_relFeb-2026/``). The pipelines expect
``regions/<region>/ebird_basic_dataset/``, so this helper renames a freshly
dropped release folder into place rather than making the user do it by hand.
"""

from pathlib import Path


EBD_DIR_NAME = "ebird_basic_dataset"


def resolve_ebd_dir(region_path: Path) -> Path:
    """Return the region's EBD directory, adopting a release-named folder if needed.

    If ``ebird_basic_dataset/`` exists, return it. Otherwise, if exactly one
    ``ebd_*`` directory exists (the untouched eBird download), rename it to
    ``ebird_basic_dataset/`` and return that. The returned path may not exist —
    callers keep their own "EBD missing" handling.
    """
    ebd_dir = region_path / EBD_DIR_NAME
    if ebd_dir.exists():
        return ebd_dir

    candidates = [p for p in region_path.glob("ebd_*") if p.is_dir()]
    if len(candidates) == 1:
        candidates[0].rename(ebd_dir)
        print(f"✓ Found eBird download folder '{candidates[0].name}' — "
              f"renamed to '{EBD_DIR_NAME}/'")
    elif len(candidates) > 1:
        names = ", ".join(p.name for p in candidates)
        print(f"⚠️  Multiple ebd_* folders found ({names}). "
              f"Rename the one to use to '{EBD_DIR_NAME}/'.")

    return ebd_dir
