#!/usr/bin/env python3
"""
Valley detection utilities for bird migration pattern analysis.

A valley is defined as a period of absence or very low detection frequency,
indicating when a species is not present in the region.

This module is the single authority for both detecting valleys and labeling
their season. Every pipeline stage that needs a valley's season must call
``classify_valley_season`` / ``valley_is_winter`` here rather than reimplement
winter/summer week ranges — see the note on the constants for why.
"""

try:
    from .constants import (
        WEEKS_PER_YEAR,
        VALLEY_WINTER_WEEKS,
        VALLEY_SUMMER_WEEKS,
        VALLEY_SEASON_MIN_OVERLAP,
    )
except ImportError:  # when scripts/ is on sys.path and this is imported as utils.*
    from constants import (
        WEEKS_PER_YEAR,
        VALLEY_WINTER_WEEKS,
        VALLEY_SUMMER_WEEKS,
        VALLEY_SEASON_MIN_OVERLAP,
    )


def _valley_week_set(valley_start, valley_end):
    """Return the set of week indices covered by a valley, handling year-wrap.

    A valley with start > end wraps the year boundary (e.g. (44, 5) covers
    weeks 44-47 and 0-5).
    """
    if valley_start <= valley_end:
        return set(range(valley_start, valley_end + 1))
    return set(range(valley_start, WEEKS_PER_YEAR)) | set(range(0, valley_end + 1))


def _season_overlaps(valley_start, valley_end):
    """Return (winter_overlap, summer_overlap, total_weeks) for a valley."""
    weeks = _valley_week_set(valley_start, valley_end)
    return (
        len(weeks & VALLEY_WINTER_WEEKS),
        len(weeks & VALLEY_SUMMER_WEEKS),
        len(weeks),
    )


def classify_valley_season(valley_start, valley_end):
    """Label a valley 'winter', 'summer', or 'mixed'.

    A valley is 'winter' or 'summer' when at least VALLEY_SEASON_MIN_OVERLAP of
    its weeks fall in that season's window (winter checked first, matching the
    historical classifier); otherwise 'mixed'.
    """
    winter, summer, total = _season_overlaps(valley_start, valley_end)
    if total == 0:
        return 'mixed'
    if winter >= total * VALLEY_SEASON_MIN_OVERLAP:
        return 'winter'
    if summer >= total * VALLEY_SEASON_MIN_OVERLAP:
        return 'summer'
    return 'mixed'


def valley_is_winter(valley_start, valley_end):
    """Binary winter/summer decision for a valley.

    Returns True when the valley overlaps the winter window at least as much as
    the summer window. Used where a definitive winter-vs-summer split is needed
    (e.g. assigning the two gaps of a two-passage migrant), including valleys
    that ``classify_valley_season`` would call 'mixed'.
    """
    winter, summer, _ = _season_overlaps(valley_start, valley_end)
    return winter >= summer


def serialize_valleys(valleys):
    """Serialize a list of (start, end) valley tuples to a CSV-safe string.

    Format: tuples joined by ';', endpoints joined by '-', e.g. "40-7;18-30".
    Empty list -> "". Round-trips with ``parse_valleys``.
    """
    return ';'.join(f"{start}-{end}" for start, end in valleys)


def parse_valleys(text):
    """Inverse of ``serialize_valleys``: parse a string back to (start, end) tuples."""
    if not text:
        return []
    valleys = []
    for token in text.split(';'):
        token = token.strip()
        if not token:
            continue
        start_str, end_str = token.split('-')
        valleys.append((int(start_str), int(end_str)))
    return valleys


def detect_valleys(frequencies):
    """
    Detect valleys (absence periods) in frequency data.

    A valley is 4+ consecutive weeks below 15% of species' peak frequency,
    with a minimum threshold of 0.5% to ensure consistency with peak classification.

    Args:
        frequencies: List of 48 weekly frequency values (0.0 to 1.0)

    Returns:
        List of (start_week, end_week) tuples for each valley.
        Week indices are 0-indexed (0-47).

    Example:
        >>> frequencies = [0.5] * 10 + [0.01] * 5 + [0.5] * 33
        >>> detect_valleys(frequencies)
        [(10, 14)]
    """
    if not frequencies or len(frequencies) < 5:
        return []

    peak_freq = max(frequencies)
    if peak_freq == 0:
        return []

    # Use the maximum of 15% of peak OR 0.5% absolute threshold
    # This ensures weeks below 0.5% are always considered part of valleys
    threshold = max(peak_freq * 0.15, 0.005)

    valleys = []
    in_valley = False
    valley_start = None

    for i, freq in enumerate(frequencies):
        if freq < threshold:
            if not in_valley:
                # Start of a new valley
                in_valley = True
                valley_start = i
        else:
            if in_valley:
                # End of valley
                valley_length = i - valley_start
                if valley_length >= 4:
                    valleys.append((valley_start, i - 1))
                in_valley = False
                valley_start = None

    # Check if we ended in a valley
    if in_valley:
        valley_length = len(frequencies) - valley_start
        if valley_length >= 4:
            valleys.append((valley_start, len(frequencies) - 1))

    # Merge valleys that wrap around the year
    # If we have a valley at the end (touching week 47) and a valley at the start (touching week 0)
    # they should be merged into a single valley that wraps around
    if len(valleys) >= 2:
        first_valley = valleys[0]
        last_valley = valleys[-1]

        # Check if first valley starts at 0 and last valley ends at 47
        if first_valley[0] == 0 and last_valley[1] == 47:
            # Merge them: new valley goes from last_valley start to first_valley end
            merged_valley = (last_valley[0], first_valley[1])
            # Remove both valleys and add the merged one
            valleys = valleys[1:-1]  # Remove first and last
            valleys.append(merged_valley)

    return valleys
