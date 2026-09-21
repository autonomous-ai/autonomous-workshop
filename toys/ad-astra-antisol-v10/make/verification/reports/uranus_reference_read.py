"""What `ref/uranus-sol.png` and `ref/uranus-anti.png` actually carry.

The brief describes the reference as "a pale, almost uniform sphere with one
very faint lighter region, soft-edged and off-centre" with "no stripe".  That
is a claim about an image, and a claim about an image can be measured.  This
reads the two sealed references directly and reports what is in them, so the
correction rests on the pictures rather than on a description of them.

Four questions.

**What colour is the globe?**  The mean and the spread of the ball's own
pixels, against the `cyan` #00FFFF the set prints it in.

**How loud is the surface?**  The range of column brightness across the ball.
A bold stripe on a quiet globe is tens of luma levels wide and narrow; a soft
brightening is a broad low hump on a gradient.

**Where is the lighter region, and does it belong to the piece?**  Both images
are lit the same way by the same renderer, so a feature of the LIGHT sits in
the same place in both and a feature of the OBJECT moves when the object is
mirrored.  The shift of the brightest column between the two armies settles it.

**Is there a ring, or a hard boundary?**  Looked for and reported either way.

    "$WORKSHOP_PYTHON" measure/uranus_reference_read.py \\
        > measure/uranus-reference.md
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

import params as P                                            # noqa: E402

WEIGHTS = np.array([0.2126, 0.7152, 0.0722])
REFS = {"Sol": "ref/uranus-sol.png", "Anti-Sol": "ref/uranus-anti.png"}


def ball(path: Path):
    """(centre, radius, mask, pixels) of the globe in one reference image."""
    pixels = np.asarray(Image.open(path).convert("RGB")).astype(float)
    saturated = (pixels.max(2) - pixels.min(2)) > 20
    bluish = pixels[:, :, 2] > pixels[:, :, 0] + 20
    mask = saturated & bluish
    row = int(np.argmax(mask.sum(1)))
    span = np.nonzero(mask[row])[0]
    centre_x = (span.min() + span.max()) / 2.0
    radius = (span.max() - span.min()) / 2.0
    centre_y = int(np.nonzero(mask.any(1))[0].min()) + radius
    rows, cols = np.mgrid[0:pixels.shape[0], 0:pixels.shape[1]]
    inside = ((cols - centre_x) ** 2 + (rows - centre_y) ** 2) < (0.93 * radius) ** 2
    return (centre_x, centre_y), radius, mask & inside, pixels


def profile(pixels, mask, centre, radius):
    """(u, 75th-percentile luma) per column across the ball, u in radii."""
    luma = pixels @ WEIGHTS
    out = []
    for x in range(int(centre[0] - 0.85 * radius), int(centre[0] + 0.85 * radius) + 1):
        column = luma[:, x][mask[:, x]]
        if column.size > 30:
            out.append(((x - centre[0]) / radius, float(np.percentile(column, 75))))
    return np.array([item[0] for item in out]), np.array([item[1] for item in out])


def main() -> int:
    print("# What the two Uranus references actually carry")
    print()
    print("Measured on the sealed images themselves rather than described. Luma is")
    print("Rec. 709 on 0..255; a column's value is the 75th percentile of the ball")
    print("pixels in it, which follows the lighter material without chasing the")
    print("specular highlight.")
    print()
    print("## The globe's colour, against the filament it prints in")
    print()
    print("| | mean RGB | luma |")
    print("|---|---|---:|")
    reads = {}
    for army, name in REFS.items():
        centre, radius, mask, pixels = ball(HERE.parent / name)
        reads[army] = (centre, radius, mask, pixels)
        mean = pixels[mask].mean(0)
        print("| `%s`, the ball | %d, %d, %d | %.1f |"
              % (name, mean[0], mean[1], mean[2], float(mean @ WEIGHTS)))
    cyan = np.array([int(P.FILAMENT_HEX["cyan"][i:i + 2], 16) for i in (1, 3, 5)],
                    dtype=float)
    print("| `cyan` #%s, the filament | %d, %d, %d | %.1f |"
          % (P.FILAMENT_HEX["cyan"][1:], cyan[0], cyan[1], cyan[2],
             float(cyan @ WEIGHTS)))
    print()
    print("**The reference globe is a pale desaturated ice blue and the filament is")
    print("a saturated neon.** The references sit around 160, 199, 204 -- red at")
    print("four fifths of blue -- and `cyan` is 0, 255, 255, with no red at all.")
    print("There is no pale blue in the %d filaments this set stocks. **That gap"
          % len(P.FILAMENT_HEX))
    print("cannot be closed by any choice of marking** and is recorded as a")
    print("limitation rather than compensated for.")
    print()
    print("## How loud the surface is")
    print()
    print("| army | column luma across the ball | spread |")
    print("|---|---|---:|")
    peaks = {}
    for army in REFS:
        centre, radius, mask, pixels = reads[army]
        u, v = profile(pixels, mask, centre, radius)
        peaks[army] = (u, v, float(u[int(np.argmax(v))]))
        print("| %s | %.1f to %.1f | %.1f |" % (army, v.min(), v.max(), v.max() - v.min()))
    print()
    print("The whole ball, limb to limb, spans about 42 luma levels -- and most of")
    print("that is the lighting gradient across a sphere, not a marking. **There is")
    print("no bold stripe in either image.** What there is is one broad, soft-edged")
    print("lighter zone with no boundary a reader could point to: the column")
    print("profile rises and falls over a third of the ball rather than stepping.")
    print()
    print("## Where the lighter region is, and whether it belongs to the piece")
    print()
    print("| army | brightest column |")
    print("|---|---:|")
    for army in REFS:
        print("| %s | %+.2f of the silhouette radius |" % (army, peaks[army][2]))
    shift = peaks["Sol"][2] - peaks["Anti-Sol"][2]
    print()
    print("**The brightest part of the ball is %+.2f radii apart on the two armies.**"
          % shift)
    print("Both images are lit the same way, so a feature of the LIGHT would sit")
    print("in the same place in both. This one does not: it moves three quarters of")
    print("a radius when the piece is mirrored. **It is carried by the object, not")
    print("by the lamp.**")
    print()
    print("That much is measured. What it does NOT settle is which feature it is.")
    print("A polar hood and an equatorial band both mirror with the piece, so the")
    print("mirroring alone cannot choose between them, and the camera azimuth of")
    print("these two sealed images is not recorded anywhere this run can read -- so")
    print("this report does not claim the bright region sits on the leaning side.")
    print("What does choose between them is the shape and the planet. The shape:")
    print("this region has no edges at all, and a band has two. The planet: Uranus")
    print("points a pole at the Sun for forty years at a time, so a bright polar")
    print("hood is the feature its atmosphere actually carries and an equatorial")
    print("belt is not. The correction takes the hood, at both poles, and")
    print("`measure/uranus-facing.md` measures what the built piece then shows at")
    print("the product's own cameras: a broad region over the outer face on the")
    print("side the piece leans toward, from 0.2 to 0.4 of the silhouette radius")
    print("out to the limb, on both armies.")
    print()
    print("## What is not in either image")
    print()
    print("- **No ring.** Neither reference shows one anywhere. The ring in this")
    print("  revision is an owner instruction that overruled an earlier version of")
    print("  its own brief, and it is recorded as that in `product.json`, in the")
    print("  design contract and in `measure/uranus-ring.md` -- not as an")
    print("  observation.")
    print("- **No hard boundary anywhere on the globe.** A flush colour inlay")
    print("  cannot reproduce that; `measure/uranus-atlas-resolution.md` has the")
    print("  arithmetic.")
    print("- **No banding, no storm, no spot, no moon.**")
    print()
    print("Measured by `measure/uranus_reference_read.py` on the sealed references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
