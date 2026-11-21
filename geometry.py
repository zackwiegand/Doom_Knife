"""Derived 2D geometry of the scale (mm), shared by build + trace scripts."""
import json

import numpy as np

from params import *

_ref = json.load(open("ref/outline_mm.json"))
OUTLINE = np.array(_ref["outline"])
LANYARD = np.array(_ref["lanyard"])
_photo = {k: v["c"] for k, v in _ref["holes"].items()}  # photo hole centers (x used)


def spine_y(x, band=1.5):
    """Top edge of the outline directly above x."""
    near = OUTLINE[np.abs(OUTLINE[:, 0] - x) < band]
    return near[:, 1].max()


def below_spine(x, top_edge_dist, d):
    """Hole center from its top edge's distance below the spine."""
    return (x, float(spine_y(x) - top_edge_dist - d / 2))


# Straight section of the spine (pivot -> step), used for the pin row
SPINE_FLAT_Y = float(np.median([spine_y(x) for x in np.arange(5, 40, 1.0)]))

PIVOT = below_spine(0.0, PIVOT_TOP_FROM_SPINE, PIVOT_D)
A = below_spine(_photo["spine_screw"][0], A_TOP_FROM_SPINE, SCREW_D)
B = below_spine(_photo["butt_screw"][0], B_TOP_FROM_SPINE, SCREW_D)
C = (B[0] + BC_EDGE_GAP + SCREW_D, B[1])

# Pins: x from the liner photo (ref/liner_mm.json), y from calipers
_pin_x = [p[0] for p in json.load(open("ref/liner_mm.json"))["pins"]]
PINS = [(x, SPINE_FLAT_Y - PIN_TOP_FROM_SPINE - PIN_HOLE_D / 2) for x in _pin_x]
