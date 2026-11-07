#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["numpy", "opencv-python-headless==4.10.0.84"]
# ///
"""Make doll portraits and unit art from GFL2 client art, for the rows in tables.py.

Run extract_art.py --dolls first, so the source art is in .cache/.

Per doll (mod/textures/portraits/):

    gfl_<id>_large.dds   536x464  Avatar_Whole art on the shared plate (data/portrait_large_bg.png),
                                  clipped inside the plate's 4px border and orange corners
    gfl_<id>.dds         80x80    Avatar_Head scaled to 72px and cut to a 40px-radius circle

Per unit:

    mod/textures/gfl_<slug>_bg.dds                   536x228  flag image: faction logo over the
                                                              flag colour, fading out downwards
    mod/textures/gui/deploy/gfl_class_icon_<slug>.dds  32x32  white faction logo

The large portrait is placed by the face. An anime face detector finds it in Avatar_Whole,
and the art is scaled and moved so the face lands where the hand-made roster's faces sit.
The ranges below are the spread measured across those 39 portraits. Each doll draws her own
values from them (seeded by her id), so reruns are stable and the set keeps the roster's
slightly uneven placement. When the detector misses (a cap or visor over the face), pass
`face_box` in tables.py.

DK2 reads these DDS files bottom-up, so rows are written flipped, uncompressed, one mip level,
the same layout as the GIMP exports already in the mod.

Run:
    uv run scripts/sprites/make_sprites.py            # every row in tables.py
    uv run scripts/sprites/make_sprites.py kp31 dollcom
    uv run scripts/sprites/make_sprites.py --preview  # also write PNG copies to .cache/preview/
"""

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CACHE = HERE / ".cache"
DATA = HERE / "data"
MOD = REPO / "mod"
sys.path.insert(0, str(HERE))
from tables import DOLLS, UNITS

LARGE_SIZE = (536, 464)
# The plate's border: everything outside this box stays the plate's own frame.
LARGE_INNER = (4, 4, 532, 460)
# Face box (as the detector reports it) in the hand-made large portraits: width, centre x, top.
FACE_WIDTH = (170, 200)
FACE_CX = (255, 285)
FACE_TOP = (125, 155)
# Detector scales: the art is 2048px, faces are 200 to 280px across, and the cascade is most
# reliable when they come out around 60 to 100px.
DETECT_SCALES = (0.5, 0.35, 0.25)

SMALL_SIZE = 80
SMALL_HEAD = 72

FLAG_SIZE = (536, 228)
# Flag alpha runs from top to bottom between these, and the logo adds a little on top.
FLAG_ALPHA = (175, 0)
FLAG_LOGO_ALPHA = 10
# Logo height as a fraction of the flag height, centre as fractions of the size, tilt in degrees.
FLAG_LOGO_HEIGHT = 1.3
FLAG_LOGO_CENTRE = (0.28, 0.55)
FLAG_LOGO_TILT = 15

ICON_SIZE = 32
ICON_BOX = 29


def load_rgba(path):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if im is None:
        raise SystemExit(f"cannot read {path} (run extract_art.py --dolls first)")
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def rng_for(key):
    return np.random.default_rng(
        int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "little")
    )


def premultiplied(im):
    a = im[..., 3:4].astype(np.float32) / 255
    return np.dstack(
        [im[..., :3].astype(np.float32) * a, im[..., 3:4].astype(np.float32)]
    )


def unpremultiplied(pre):
    pre = np.clip(pre, 0, 255)
    alpha = pre[..., 3:4]
    rgb = np.where(alpha > 0, pre[..., :3] / np.maximum(alpha / 255, 1e-6), 0)
    return np.dstack([np.clip(rgb, 0, 255), alpha]).astype(np.uint8)


def warp(im, m, size, flags=cv2.INTER_LANCZOS4):
    """Affine warp with premultiplied alpha, so transparent edges carry no dark fringe."""
    out = cv2.warpAffine(
        premultiplied(im),
        np.float32(m),
        size,
        flags=flags,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )
    return unpremultiplied(out)


def over(base, top):
    """Alpha-composite top onto base, both BGRA uint8 of the same size."""
    t, b = top.astype(np.float32), base.astype(np.float32)
    ta, ba = t[..., 3:4] / 255, b[..., 3:4] / 255
    oa = ta + ba * (1 - ta)
    rgb = (t[..., :3] * ta + b[..., :3] * ba * (1 - ta)) / np.maximum(oa, 1e-6)
    return np.clip(np.dstack([rgb, oa * 255]), 0, 255).astype(np.uint8)


def write_dds(path, im):
    """Uncompressed DDS, bottom-up rows. BGRA, or BGR when given three channels."""
    h, w, c = im.shape
    bits = c * 8
    pf_flags = 0x41 if c == 4 else 0x40  # DDPF_RGB, plus DDPF_ALPHAPIXELS
    header = struct.pack(
        "<4s7I44x2I4s5I5I",
        b"DDS ",
        124,
        0x100F,
        h,
        w,
        w * c,
        0,
        1,
        32,
        pf_flags,
        b"\0\0\0\0",
        bits,
        0xFF0000,
        0xFF00,
        0xFF,
        0xFF000000 if c == 4 else 0,
        0x1000,
        0,
        0,
        0,
        0,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header + np.ascontiguousarray(im[::-1]).tobytes())


def detect_face(whole):
    """Face box (x, y, width) in the art, voted across detector scales."""
    cascade = cv2.CascadeClassifier(str(DATA / "lbpcascade_animeface.xml"))
    a = whole[..., 3:4].astype(np.float32) / 255
    flat = (whole[..., :3] * a + 128 * (1 - a)).astype(np.uint8)
    boxes = []
    for k in DETECT_SCALES:
        small = cv2.resize(flat, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        g = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        for x, y, w, _ in cascade.detectMultiScale(g, 1.03, 3, minSize=(24, 24)):
            boxes.append((x / k, y / k, w / k))
    if not boxes:
        return None
    # Group boxes whose centres lie within half a face of each other, keep the best-supported
    # group, and prefer the higher one on a tie (a face on a held prop sits lower).
    groups = []
    for b in boxes:
        for g in groups:
            r = g[0]
            if (
                abs((b[0] + b[2] / 2) - (r[0] + r[2] / 2)) < r[2] / 2
                and abs(b[1] - r[1]) < r[2] / 2
            ):
                g.append(b)
                break
        else:
            groups.append([b])
    best = max(groups, key=lambda g: (len(g), -g[0][1]))
    return tuple(np.median(np.array(best), axis=0))


def large_portrait(doll, row, whole):
    if "face_box" in row:
        fx, fy, fw = row["face_box"]
    else:
        face = detect_face(whole)
        if face is None:
            raise SystemExit(
                f"{doll}: no face found in Avatar_Whole_{row['gfl2']}, set face_box in tables.py"
            )
        fx, fy, fw = face
        print(f"{doll}: face x={fx:.0f} y={fy:.0f} width={fw:.0f}")

    rng = rng_for(doll)
    width, cx, top = (rng.uniform(*r) for r in (FACE_WIDTH, FACE_CX, FACE_TOP))
    s = width / fw
    m = [[s, 0, cx - (fx + fw / 2) * s], [0, s, top - fy * s]]
    figure = warp(whole, m, LARGE_SIZE)

    x0, y0, x1, y1 = LARGE_INNER
    inside = np.zeros(figure.shape[:2], np.float32)
    inside[y0:y1, x0:x1] = 1
    figure[..., 3] = (figure[..., 3] * inside).astype(np.uint8)

    plate = load_rgba(DATA / "portrait_large_bg.png")
    return over(plate, figure)[..., :3]


def small_portrait(head):
    s = SMALL_HEAD / head.shape[1]
    off = (SMALL_SIZE - SMALL_HEAD) / 2
    out = warp(
        head, [[s, 0, off], [0, s, off]], (SMALL_SIZE, SMALL_SIZE), cv2.INTER_AREA
    )
    # Antialiased circle: supersample the mask then shrink it.
    k = 8
    yy, xx = np.mgrid[: SMALL_SIZE * k, : SMALL_SIZE * k]
    r = SMALL_SIZE * k / 2
    disc = ((xx + 0.5 - r) ** 2 + (yy + 0.5 - r) ** 2 <= r * r).astype(np.float32)
    disc = cv2.resize(disc, (SMALL_SIZE, SMALL_SIZE), interpolation=cv2.INTER_AREA)
    out[..., 3] = (out[..., 3] * disc).astype(np.uint8)
    return out


def trim(im):
    ys, xs = np.where(im[..., 3] > 12)
    return im[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]


def fit_centred(im, box, size, angle=0.0, centre=None):
    """Scale im to fit box (w, h) and place its centre at centre (default the middle)."""
    h, w = im.shape[:2]
    s = min(box[0] / w, box[1] / h)
    cx, cy = centre or (size[0] / 2, size[1] / 2)
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, s)
    m[0, 2] += cx - w / 2
    m[1, 2] += cy - h / 2
    return warp(im, m, size, cv2.INTER_AREA)


def flag_colour(slug):
    xml = (MOD / "units" / f"gfl_unit_{slug}.xml").read_text()
    m = re.search(r'flagColor="([0-9A-Fa-f]{6})"', xml)
    if not m:
        raise SystemExit(f"no flagColor in gfl_unit_{slug}.xml")
    r, g, b = (int(m.group(1)[i : i + 2], 16) for i in (0, 2, 4))
    return np.array([b, g, r], np.float32)


def flag(slug, logo):
    w, h = FLAG_SIZE
    colour = flag_colour(slug)
    # A light flag colour takes a dark logo, as the hand-made DEFY and Frost flags do.
    ink = 0.0 if colour.mean() > 180 else 255.0
    lh = h * FLAG_LOGO_HEIGHT
    placed = fit_centred(
        logo,
        (lh * 10, lh),
        FLAG_SIZE,
        FLAG_LOGO_TILT,
        (w * FLAG_LOGO_CENTRE[0], h * FLAG_LOGO_CENTRE[1]),
    )
    la = placed[..., 3:4].astype(np.float32) / 255
    rgb = colour * (1 - la) + ink * la
    ramp = np.linspace(*FLAG_ALPHA, h, dtype=np.float32)[:, None, None]
    # The logo boost fades with the ramp, so the bottom edge reaches fully transparent.
    alpha = np.clip(ramp * (1 + FLAG_LOGO_ALPHA / FLAG_ALPHA[0] * la), 0, 255)
    return np.clip(np.dstack([rgb, alpha]), 0, 255).astype(np.uint8)


def class_icon(logo):
    icon = fit_centred(logo, (ICON_BOX, ICON_BOX), (ICON_SIZE, ICON_SIZE))
    icon[..., :3] = 255
    return icon


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "only", nargs="*", help="doll ids or unit slugs to make (default: every row)"
    )
    ap.add_argument(
        "--preview", action="store_true", help="also write PNGs to .cache/preview/"
    )
    args = ap.parse_args()
    unknown = set(args.only) - DOLLS.keys() - UNITS.keys()
    if unknown:
        ap.error(f"not in tables.py: {', '.join(sorted(unknown))}")

    outputs = []
    for doll, row in DOLLS.items():
        if args.only and doll not in args.only:
            continue
        whole = load_rgba(CACHE / f"Avatar_Whole_{row['gfl2']}.png")
        head = load_rgba(CACHE / f"Avatar_Head_{row['gfl2']}.png")
        portraits = MOD / "textures" / "portraits"
        outputs.append(
            (portraits / f"gfl_{doll}_large.dds", large_portrait(doll, row, whole))
        )
        outputs.append((portraits / f"gfl_{doll}.dds", small_portrait(head)))

    for slug, row in UNITS.items():
        if args.only and slug not in args.only:
            continue
        logo = trim(load_rgba(CACHE / f"Img_CampLogo_{row['logo']}.png"))
        outputs.append((MOD / "textures" / f"gfl_{slug}_bg.dds", flag(slug, logo)))
        outputs.append(
            (
                MOD / "textures" / "gui" / "deploy" / f"gfl_class_icon_{slug}.dds",
                class_icon(logo),
            )
        )

    for path, im in outputs:
        write_dds(path, im)
        print(f"wrote {path.relative_to(REPO)}")
        if args.preview:
            preview = CACHE / "preview" / f"{path.stem}.png"
            preview.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(preview), im)


if __name__ == "__main__":
    main()
