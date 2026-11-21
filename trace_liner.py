"""Trace the liner from ref/knife_liner.jpeg -> ref/liner_mm.json (scale coords).

Registration: liner pivot hole -> scale pivot, liner tail hole -> scale hole A
(similarity transform). The photo edge includes the steel's side wall/shadow,
so the outline is shrunk by EDGE_PX top/bottom only, fitted to the caliper
widths (collar 25.52, mid 8.48, tail 6.28). The ends have no rim: unshrunk
length matches the caliper length 86.72.
"""
import json

import cv2
import numpy as np

from geometry import A, PIVOT
from trace_scale import resample, smooth

PHOTO = "ref/knife_liner.jpeg"
ROI = (950, 1550, 900, 2550)  # y0, y1, x0, x1
THRESH = 161
EDGE_PX = 9


def main():
    pivot_mm, a_mm = np.array(PIVOT), np.array(A)

    y0, y1, x0, x1 = ROI
    g = cv2.cvtColor(cv2.imread(PHOTO), cv2.COLOR_BGR2GRAY)
    sub = cv2.GaussianBlur(g[y0:y1, x0:x1], (5, 5), 0)
    m = (sub < THRESH).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cs, h = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    outer_i = max(range(len(cs)), key=lambda k: cv2.contourArea(cs[k]))
    holes = [cs[k] for k in range(len(cs)) if h[0][k][3] == outer_i and cv2.contourArea(cs[k]) > 100]
    centers = sorted((cv2.minEnclosingCircle(c)[0] for c in holes), key=lambda p: p[0])
    big = max(holes, key=cv2.contourArea)
    piv_px = np.array(cv2.minEnclosingCircle(big)[0])
    small = [np.array(p) for p in centers if np.hypot(*(np.array(p) - piv_px)) > 20]
    tail_px = small[-1]

    # shrink outline vertically by the side-wall/shadow rim
    fill = np.zeros_like(m)
    cv2.drawContours(fill, [cs[outer_i]], -1, 255, -1)
    fill = cv2.erode(fill, np.ones((2 * EDGE_PX + 1, 1), np.uint8))
    outer = max(cv2.findContours(fill, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0, :]

    # similarity transform px -> mm (flip Y so +Y = spine)
    def flip(p):
        return np.asarray(p, float) * [1, -1]

    v_px = flip(tail_px) - flip(piv_px)
    v_mm = a_mm - pivot_mm
    k = np.hypot(*v_mm) / np.hypot(*v_px)
    ang = np.arctan2(v_mm[1], v_mm[0]) - np.arctan2(v_px[1], v_px[0])
    R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])

    def to_mm(p):
        return (flip(np.asarray(p, float) + [x0, y0]) - flip(piv_px + [x0, y0])) @ R.T * k + pivot_mm

    print(f"px/mm {1 / k:.2f}  rotation {np.degrees(ang):.2f} deg")

    out = {
        "outline": to_mm(smooth(resample(outer, 400), 2)).round(3).tolist(),
        "pins": [to_mm(p).round(3).tolist() for p in small[:-1]],
    }
    json.dump(out, open("ref/liner_mm.json", "w"), indent=1)
    o = np.array(out["outline"])
    print(f"  liner length {np.ptp(o[:, 0]):.2f} (calipers 86.72)")
    for x in (0, 20, 40, 60):
        s = o[np.abs(o[:, 0] - x) < 0.5]
        print(f"  liner width at x={x}: {s[:, 1].max() - s[:, 1].min():.2f}")
    print("  pins (photo):", out["pins"])


if __name__ == "__main__":
    main()
