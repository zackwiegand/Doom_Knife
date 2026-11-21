"""Phase 1: one Arcade Lite scale. Run: .venv/bin/python scale.py <version>

Z=0 is the inside face (liner side), Z=THICKNESS the outside face.
"""
import json
import sys

import numpy as np
from build123d import *

from geometry import A, B, C, LANYARD, OUTLINE, PINS, PIVOT
from params import *

LINER = np.array(json.load(open("ref/liner_mm.json"))["outline"])

# Where the liner is exposed at the spine (blade side), the pocket runs out
# past the spine instead of following the traced liner edge: that edge weaves
# within +/-0.5 mm of the spine, which breaks the boolean cut.
SPINE_CUT_Y = 16.0  # below the spine (~17.1), above the tail channel top (~15.2)
SPINE_CUT_X1 = float(LINER[(LINER[:, 1] > SPINE_CUT_Y + 0.5) & (LINER[:, 0] > 0)][:, 0].max())
SPINE_CUT_X0 = -20.0  # past the blade end


def spline_face(pts):
    with BuildSketch() as sk:
        with BuildLine():
            Spline(*[tuple(p) for p in pts], periodic=True)
        make_face()
    return sk.sketch.face()


def offset_pts(pts, d):
    """Offset a closed point loop outward by d along vertex normals.

    Done on points (not with offset()) so the result is one plain spline:
    OCC offset curves don't survive STEP export.
    """
    pts = np.asarray(pts, float)
    tang = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
    norm = np.column_stack([tang[:, 1], -tang[:, 0]]) / np.hypot(*tang.T)[:, None]
    x, y = pts.T
    ccw = np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) > 0
    return pts + norm * d * (1 if ccw else -1)


def liner_pocket():
    with BuildSketch() as sk:
        insert(spline_face(offset_pts(LINER, LINER_CLEARANCE)))
        with Locations(((SPINE_CUT_X0 + SPINE_CUT_X1) / 2, SPINE_CUT_Y + 5)):
            Rectangle(SPINE_CUT_X1 - SPINE_CUT_X0, 10)
    return sk.sketch


def build():
    with BuildPart() as scale:
        with BuildSketch():
            insert(spline_face(OUTLINE))
        extrude(amount=THICKNESS)
        if EDGE_ROUND:
            fillet(scale.faces().sort_by(Axis.Z)[-1].outer_wire().edges(), EDGE_ROUND)

        top = Plane.XY.offset(THICKNESS)
        with BuildSketch(top):
            insert(spline_face(LANYARD))
            with Locations(PIVOT):
                Circle(PIVOT_D / 2)
            with Locations(A, B, C):
                Circle(SCREW_D / 2)
        extrude(amount=-THICKNESS, mode=Mode.SUBTRACT)

        with BuildSketch(top):
            with Locations(PIVOT):
                Circle(PIVOT_CB_D / 2)
        extrude(amount=-PIVOT_CB_DEPTH, mode=Mode.SUBTRACT)

        with Locations(*[top * Location(p) for p in (A, C)]):
            CounterBoreHole(SCREW_D / 2, CB_D / 2, CB_DEPTH)

        with BuildSketch():
            insert(liner_pocket())
        extrude(amount=LINER_RECESS_DEPTH, mode=Mode.SUBTRACT)

        with BuildSketch(Plane.XY.offset(LINER_RECESS_DEPTH)):
            with Locations(*PINS):
                Circle(PIN_HOLE_D / 2)
        extrude(amount=PIN_HOLE_DEPTH, mode=Mode.SUBTRACT)
    part = scale.part
    part.color = Color(*COLOR_RGBA)
    return part


def check(part):
    """Fail loudly on broken/open solids (is_valid alone missed one)."""
    bb = part.bounding_box()
    print(f"valid={part.is_valid}  volume={part.volume:.1f} mm3  solids={len(part.solids())}")
    print(f"  size X={bb.size.X:.2f} Y={bb.size.Y:.2f} Z={bb.size.Z:.2f}  (target {LENGTH} x {WIDTH_MAX} x {THICKNESS})")
    inside = [f for f in part.faces().filter_by(Axis.Z) if f.center().Z < 0.01]
    print(f"  inside-face area={sum(f.area for f in inside):.1f} mm2")
    assert part.is_valid and len(part.solids()) == 1 and part.volume > 1000 and inside, "broken solid"
    bad = [e for e in part.edges() if e.geom_type == GeomType.OFFSET]
    assert not bad, f"{len(bad)} offset edges: STEP export would drop faces"
    for name, (x, y) in zip(["pivot", "A", "B", "C", "pin1", "pin2", "pin3"], [PIVOT, A, B, C, *PINS]):
        print(f"  {name:5s} x={x:7.2f} y={y:6.2f}")


if __name__ == "__main__":
    version = sys.argv[1]
    part = build()
    check(part)
    export_step(part, f"out/scale_{version}.step")
    export_stl(part, f"out/scale_{version}.stl")
    back = import_step(f"out/scale_{version}.step")
    assert len(back.solids()) == 1 and abs(back.volume - part.volume) < 1, "STEP round-trip lost geometry"
    print(f"STEP round-trip ok: volume {back.volume:.1f} mm3")
    print(f"wrote out/scale_{version}.step / .stl")
