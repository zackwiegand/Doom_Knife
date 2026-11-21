"""Caliper measurements for one Arcade Lite scale (mm).

Origin = pivot center (from photo). +X runs toward the butt, +Y toward the
spine. Z=0 is the inside face (against the liner), Z=THICKNESS the outside.
"Down from spine" = distance from the outline's top edge directly above.
"""

# --- Outline (calipers; outline itself traced from ref/scale_top.jpeg) ---
LENGTH = 113.66          # overall length, longest point
WIDTH_MAX = 29.05        # widest point, blade end
WIDTH_GRIP = 23.83       # grip section
THICKNESS = 3.94         # modelled flat (real scale is slightly contoured)
EDGE_ROUND = 1.0         # fillet on outside-face perimeter (0 = sharp)

# --- Pivot ---
PIVOT_D = 6.04           # through
PIVOT_CB_D = 9.02        # recess from outside face
PIVOT_CB_DEPTH = 1.0
PIVOT_TOP_FROM_SPINE = 14.24   # hole top edge -> spine

# --- Screw holes A, B, C (left->right from pivot; screw thread OD 2.46) ---
SCREW_D = 2.66
A_TOP_FROM_SPINE = 3.98      # A: near spine
B_TOP_FROM_SPINE = 12.52     # B: butt pair, nearer the pivot
BC_EDGE_GAP = 4.2            # closest edges of B and C
C_EDGE_TO_BUTT = 5.67        # check only: C edge -> butt edge (model: 5.54 horiz)
CB_D = 4.29                  # straight counterbore on A and C, outside face
CB_DEPTH = 1.0               # estimated

# --- Inside face: liner recess (outline traced from ref/knife_liner.jpeg) ---
LINER_T = 1.20               # liner thickness (calipers)
LINER_RECESS_DEPTH = 1.20    # scale recess depth, ~= liner thickness
LINER_CLEARANCE = 0.26       # per side: 6.28 tail -> 6.80 channel (measured)

# --- Display only (STEP color; viewers may ignore alpha) ---
COLOR_RGBA = (110 / 255, 255 / 255, 20 / 255, 0.31)

# --- Inside face: blind pin holes (3 identical, in the liner pocket floor) ---
PIN_HOLE_D = 2.80            # measured on scale (pin is 2.90: snug/press fit)
PIN_TOP_FROM_SPINE = 3.22    # hole top edge -> straight spine
# Pins A, B, C from blade side: x of hole centers (mm from pivot).
# Least-squares fit to all caliper checks (nearest edges, 2.80 holes):
#   pin A-B 12.88, pin B-C 26.14, pin A-C 42.06, pivot-pin B 10.82,
#   pin C-screw A 29.04/29.19, pin A-liner corner 1.45  -> worst miss 0.34
PIN_X = (-7.30, 8.56, 37.68)
# Pin 7.90 long, center collar 3.85 -> 2.025 per side through liner (1.20)
PIN_HOLE_DEPTH = (7.90 - 3.85) / 2 - LINER_T + 0.10  # +0.10 so pins don't bottom out
