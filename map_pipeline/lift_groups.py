"""Shared classification of OSM aerialway lifts into display groups.

Used by build_lift_density.py and build_lift_index.py so the density counts and
the drill-in list always agree on categories.

Groups:
- cable_car   — aerial ropeway with cabins (cable_car, mixed_lift, funicular)
- gondola     — circulating gondola
- chair_lift  — chairlift
- surface_tow — ground tows (drag/t-bar/platter/j-bar/rope_tow/magic_carpet)
- water_ski   — wakeboard / water-ski cable tow (special: these reuse ski-tow
                tags but are NOT mountain transport; kept, but labelled clearly)
Anything else (station, goods, zip_line, pylon, …) classifies to None = dropped.
"""
import re

# raw aerialway=* value -> base display group
BASE_GROUP = {
    "chair_lift": "chair_lift",
    "gondola": "gondola",
    "mixed_lift": "gondola",
    "cable_car": "cable_car",
    "cablecar": "cable_car",
    "funicular": "cable_car",
    "drag_lift": "surface_tow",
    "t-bar": "surface_tow",
    "platter": "surface_tow",
    "j-bar": "surface_tow",
    "rope_tow": "surface_tow",
    "magic_carpet": "surface_tow",
    "zip_line": "zip_line",
}

# Ordered by emphasis: real aerial ropeways first, then tows, zip lines, water-ski.
GROUPS = ["cable_car", "gondola", "chair_lift", "surface_tow", "zip_line", "water_ski"]

# Names that reveal a wakeboard / water-ski cable tow rather than a ski lift.
_WATER_SKI = re.compile(
    r"wake|wasserski|water[ \-]?ski|вейк|водн\w*\s*лыж|wodne\s*narty|cable\s*park",
    re.I,
)


def classify(aerialway_type, name=None):
    """Return the display group for a lift, or None if it is not passenger transport."""
    base = BASE_GROUP.get(aerialway_type)
    if base is None:
        return None
    if name and _WATER_SKI.search(name):
        return "water_ski"
    return base
