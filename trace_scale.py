"""Trace the scale outline from the top photo -> ref/outline_mm.json.

Pixel scale comes from LENGTH in params.py; WIDTH_MAX is printed as a check.
"""
import json

import cv2
import numpy as np

from params import LENGTH, WIDTH_MAX

PHOTO = "ref/scale_top.jpeg"
GREEN_THRESH = 67  # Otsu value for this photo
HOLES_PX = {  # approx centers, refined below
    "pivot": (1182, 1595),
    "spine_screw": (2434, 1379),
    "butt_screw": (2736, 1549),
    "butt_ring": (2859, 1550),
}


def green_mask(im):
    im = im.astype(np.int16)
    d = np.clip(im[..., 1] - np.maximum(im[..., 2], im[..., 0]) * 0.75, 0, 255)
    return cv2.GaussianBlur(d.astype(np.uint8), (5, 5), 0) >= GREEN_THRESH


def resample(pts, n):
    closed = np.vstack([pts, pts[:1]]).astype(float)
    seg = np.hypot(*np.diff(closed, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n, endpoint=False)
    return np.column_stack([np.interp(t, s, closed[:, 0]), np.interp(t, s, closed[:, 1])])


def smooth(pts, k=3):
    pad = np.vstack([pts[-k:], pts, pts[:k]])
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    return np.column_stack([np.convolve(pad[:, i], ker, "valid") for i in (0, 1)])


def main():
    im = cv2.imread(PHOTO)
    m = green_mask(im).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    outer = max(cs, key=cv2.contourArea)[:, 0, :]
    (_, _), (w, h), ang = cv2.minAreaRect(outer)
    px_per_mm = max(w, h) / LENGTH
    print(f"px/mm {px_per_mm:.3f}  width check {min(w, h) / px_per_mm:.2f} vs {WIDTH_MAX}")

    # Dark regions inside the outline = through-holes / lanyard slot
    inside = np.zeros(m.shape, np.uint8)
    cv2.fillPoly(inside, [outer], 1)
    inside = cv2.erode(inside, np.ones((9, 9), np.uint8))
    dark = ((m == 0) & (inside > 0)).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark)
    comps = [i for i in range(1, n) if st[i, 4] > 600]

    holes = {}
    for name, p in HOLES_PX.items():
        i = min(comps, key=lambda i: np.hypot(*(cen[i] - p)))
        holes[name] = {"c": cen[i], "d": 2 * np.sqrt(st[i, 4] / np.pi)}
        comps.remove(i)
    slot_i = max(comps, key=lambda i: st[i, 4])
    sc, _ = cv2.findContours((lab == slot_i).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Pixel -> mm: origin at pivot, de-rotate, flip Y so +Y is up (spine)
    origin = holes["pivot"]["c"]
    a = np.deg2rad(ang if abs(ang) < 45 else ang - 90)
    R = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])

    def to_mm(p):
        q = (np.asarray(p, float) - origin) @ R.T / px_per_mm
        return q * [1, -1]

    out = {
        "px_per_mm": px_per_mm,
        "outline": to_mm(smooth(resample(outer, 480), 2)).round(3).tolist(),
        "lanyard": to_mm(smooth(resample(sc[0][:, 0, :], 60), 2)).round(3).tolist(),
        "holes": {k: {"c": to_mm(v["c"]).round(3).tolist(), "d_photo": round(float(v["d"] / px_per_mm), 2)}
                  for k, v in holes.items()},
    }
    json.dump(out, open("ref/outline_mm.json", "w"), indent=1)
    for k, v in out["holes"].items():
        print(k, v)


if __name__ == "__main__":
    main()
