"""What each world's surface actually shows.

Every marking is a flush colour inlay in the globe's own sphere, described in
the planet's own frame: latitude, longitude and angular size.  Describing them
as angles rather than millimetres is what lets one minimum outline width hold
from Mercury to Jupiter, and it is what makes the same marking correct when the
planet is leaning at its true obliquity.

Each entry is (colour, [region specs]).  A region spec is one of
    ("blob",  [(lat, lon, angular_radius), ...])
    ("band",  lat_low, lat_high)
and a marking may subtract another one, which is how Earth's dryland sits
inside Earth's land rather than beside it.  Those subtractions happen while the
regions are still plain balls and cylinders, never after they have been sliced
into shells: two slices of one shell share its spherical faces, and a boolean
between coincident faces is the one that fails silently.
"""

from __future__ import annotations

# name -> ordered list of (marking key, filament, regions, subtract_keys)
MARKINGS = {
    "mercury": [
        # Two-tone albedo map: smooth plains and the Caloris basin.  Not
        # craters -- at this radius a crater reads as a print defect, while the
        # albedo map is what Mercury actually looks like from a distance.
        ("plains", "dark_gray", [
            ("blob", [(18, 24, 22), (6, 48, 20), (-22, 118, 22), (-10, 138, 16),
                      (38, 205, 21), (-6, 255, 18), (2, 162, 14)]),
        ], ()),
    ],
    "mars": [
        ("albedo", "cocoa_brown", [
            # Syrtis Major, Mare Acidalia and their neighbours.
            ("blob", [(6, 70, 19), (44, 330, 22), (-24, 176, 20), (-28, 196, 18),
                      (0, 243, 17), (-12, 15, 14)]),
        ], ()),
        ("caps", "white", [
            ("blob", [(90, 0, 23), (-90, 0, 21)]),
        ], ("albedo",)),
    ],
    "venus": [
        # The Mariner-10 ultraviolet cloud Y.  Venus is upside down at 177.36
        # degrees, so this is the only pattern in the set that reads inverted,
        # and the planet frame is what inverts it.
        # Longitudes carry a -135 degree offset from the pattern's own meridian.
        # Venus has no fixed prime meridian in this set, and at the two frames
        # the product is photographed from -- the iso at -45/35.3 and the Wish's
        # fixed frame at -35/22 -- the unoffset pattern sat on the far
        # hemisphere and no view in the evidence showed any of it.  Measured
        # after the shift: eight of the ten patches face the camera in both
        # frames on both armies, worst patch 0.03 against the view axis.
        ("ypattern", "orange", [
            ("blob", [(-46, -135, 13), (-30, -135, 13), (-14, -135, 13), (0, -135, 13),
                      (14, -117, 12), (26, -101, 11), (36, -83, 10),
                      (14, -153, 12), (26, -169, 11), (36, 173, 10)]),
        ], ()),
    ],
    "earth": [
        ("land", "green", [
            ("blob", [
                # Africa and Arabia
                (8, 20, 19), (-14, 24, 16), (-30, 26, 10), (26, 12, 13),
                # Eurasia
                (48, 40, 20), (52, 78, 20), (50, 96, 18), (44, 124, 18), (56, 12, 13),
                # the Americas
                (44, -106, 19), (38, -86, 17), (18, -100, 12), (-2, -60, 15), (-22, -60, 14),
                (-40, -66, 8),
                # Australia
                (-26, 134, 12),
            ]),
        ], ("dryland",)),
        ("dryland", "beige", [
            # Sahara and Arabia, the Kalahari, inner Asia, the American
            # southwest, the Australian outback.
            ("blob", [(20, 12, 13), (24, 45, 8), (-22, 22, 7),
                      (42, 85, 12), (34, -110, 7), (-26, 132, 9)]),
        ], ()),
        ("ice", "white", [
            ("blob", [(90, 0, 23), (74, -70, 12), (72, 90, 11)]),
        ], ("land", "dryland")),
    ],
    "neptune": [
        ("spot", "dark_gray", [
            ("blob", [(-22, 0, 17), (-20, 14, 12)]),
        ], ()),
        ("streaks", "white", [
            ("band", -46, -41),
            ("band", 11, 15),
            ("band", 30, 33),
        ], ()),
    ],
    "uranus": [
        # One faint band.  It runs pole to pole on the visible face because the
        # pole lies 7.77 degrees past horizontal -- the band itself is an
        # ordinary latitude band, and the obliquity turns it upright.
        ("band", "white", [
            ("band", -9, 9),
        ], ()),
    ],
    "saturn": [
        ("bands", "cocoa_brown", [
            ("band", -51, -39),
            ("band", -21, -9),
            ("band", 9, 21),
            ("band", 39, 51),
        ], ()),
    ],
    "jupiter": [
        ("bands", "cocoa_brown", [
            ("band", -56, -44),
            ("band", -36, -24),
            ("band", -16, -4),
            ("band", 4, 16),
            ("band", 24, 36),
            ("band", 44, 56),
        ], ("spot",)),
        # The Great Red Spot's latitude is the real one; its longitude is free,
        # because Jupiter turns in ten hours and this set fixes no meridian.
        # Carried -110 degrees from where it started so that it faces the
        # camera in both photographed frames: measured 0.49 against the view
        # axis at worst, against -0.49 before the shift, where it sat squarely
        # on the hidden hemisphere of both Jupiters in every rendered view.
        ("spot", "red", [
            ("blob", [(-22, -48, 13), (-22, -36, 11), (-22, -60, 11)]),
        ], ()),
    ],
}
