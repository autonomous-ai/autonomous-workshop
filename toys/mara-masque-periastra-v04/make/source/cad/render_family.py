"""Render the canonical evidence family for this revision.

Every frame the archive being corrected already carried is regenerated here from
the new geometry, and nothing is removed. Two of them are renamed and nothing else
about them changes: `roof/yoke*.png` became `roof/quarter*.png`, at the same camera
and the same crop, because the yoke they were named after has been deleted and no
feature that replaces it is visible from that camera -- at 30 degrees off the
slit's axis the near wall stands in front of the slit floor. They are kept, and are
now named for the camera rather than for a part that is not in them.

The frames this correction adds are marked ADDED: the ones the correction brief
required in the FIRST review round -- a straight side elevation with the camera
level with the dome, three-quarter views into the open slit, close crops of the
telescope's foot taken down the slit's own axis, and the drum photographed all the
way round at four azimuths -- plus the two the previous brief required, which are
carried forward.

No CAD is authored here. Each frame is an exact STEP state rendered by the
shared renderer through render_frames.py, which records its own provenance.
"""
from pathlib import Path
import argparse
import subprocess
import sys

CAD = Path(__file__).resolve().parent
PRODUCT = CAD.parent
STATES = PRODUCT/'evidence-states'
SNAP = CAD/'snap'

# (output, source STEP, azimuth, elevation, crop or None, added-by-this-revision[, size])
FRAMES = [
    ('closed/az0_el8.png',                'periastra.step',        0.0,   8.0, None, False),
    ('closed/az-90_el10.png',             'periastra.step',      -90.0,  10.0, None, False),
    ('playing/iso.png',                   'playing.step',        -45.0,  20.0, None, False),
    ('playing/top_el90.png',              'playing.step',        -90.0,  90.0, None, False),
    ('kings/board_az-90_el45.png',        'kings.step',          -90.0,  45.0, '0.5,0.52,0.6', False),
    ('kings/low-oblique_az-110_el10.png', 'kings.step',         -110.0,  10.0, '0.5,0.55,0.55', False),
    ('roof/down-slit_az-90_el14.png',     'roof.step',           -90.0,  14.0, None, False),
    ('roof/side-on_az0_el6.png',          'roof.step',             0.0,   6.0, None, False),
    ('roof/telescope-close_az-90_el8.png','roof.step',           -90.0,   8.0, '0.5,0.42,0.38', False),
    ('roof/three-quarter_az-135_el28.png','roof.step',          -135.0,  28.0, None, False),
    # Carried forward at the same camera and crop scale; renamed only, because the
    # yoke is gone and the close crop now points at the foot instead.
    ('roof/quarter_az-60_el18.png',       'roof.step',           -60.0,  18.0, None, False),
    ('roof/quarter-close_az-60_el18.png', 'roof.step',           -60.0,  18.0, '0.37,0.46,0.34', False),
    ('counters/sun-plan_el90.png',        'counter-sun.step',    -90.0,  90.0, None, False),
    ('counters/sun-oblique_az-90_el22.png','counter-sun.step',   -90.0,  22.0, None, False),
    ('counters/sun-faces-plan_el90.png',  'faces-sun.step',      -90.0,  90.0, None, False),
    ('counters/sun-faces-oblique_az-90_el14.png','faces-sun.step',-90.0, 14.0, None, False),
    ('counters/sun-flip_az-90_el18.png',  'flip-sun.step',       -90.0,  18.0, '0.5,0.5,0.62', False),
    ('counters/moon-plan_el90.png',       'counter-moon.step',   -90.0,  90.0, None, False),
    ('counters/moon-oblique_az-90_el22.png','counter-moon.step', -90.0,  22.0, None, False),
    ('counters/moon-faces-plan_el90.png', 'faces-moon.step',     -90.0,  90.0, None, False),
    ('counters/moon-faces-oblique_az-90_el14.png','faces-moon.step',-90.0,14.0, None, False),
    ('counters/moon-flip_az-90_el18.png', 'flip-moon.step',      -90.0,  18.0, '0.5,0.5,0.62', False),
    ('counters/moon-symbol-plan.png',     'counter-moon.step',   -90.0,  90.0, '0.5,0.5,0.75', False),
    # ADDED by this revision -- section C of the correction brief.
    ('roof/slit-plan_el90.png',           'roof.step',           -90.0,  90.0, None, True),
    ('roof/slit-plan-close_el90.png',     'roof.step',           -90.0,  90.0, '0.5,0.72,0.26', True),
    # Rendered at 1800 rather than the family's 1200: section C of the brief asks for the
    # board at whole-board scale, and at 1200 the populated frame was byte-identical to the
    # carried-forward playing/top_el90.png and added nothing. --size is applied per frame.
    ('board/empty-plan_el90.png',         'board-empty.step',    -90.0,  90.0, None, True, 1800),
    ('board/populated-plan_el90.png',     'board-populated.step',-90.0,  90.0, None, True, 1800),
    ('board/empty-oblique_az-45_el35.png','board-empty.step',    -45.0,  35.0, None, True),
    ('board/populated-oblique_az-45_el35.png','board-populated.step',-45.0,35.0, None, True),
    ('board/inlay-seat_az-60_el22.png',   'board-empty.step',    -60.0,  22.0, '0.28,0.46,0.3', True),
    # ADDED by this revision -- section F of the correction brief. The silhouette
    # question is judged on the side elevation and nowhere else, so the camera is
    # level with the dome: elevation 0.
    ('roof/side-elevation_az0_el0.png',   'roof.step',             0.0,   0.0, None, True),
    ('roof/side-elevation-close_az0_el0.png','roof.step',          0.0,   0.0, '0.32,0.32,0.30', True),
    # Into the open slit from both quarters: what is holding the tube up, and is
    # anything in there raw, sawn off or unfinished.
    ('roof/into-slit_az-75_el24.png',     'roof.step',           -75.0,  24.0, None, True),
    ('roof/into-slit_az-105_el24.png',    'roof.step',          -105.0,  24.0, None, True),
    ('roof/into-slit_az-90_el28.png',     'roof.step',           -90.0,  28.0, None, True),
    # The foot sits on the slit's own mid-plane at the far end of a 30 mm wide,
    # 90 mm deep slot, so an oblique camera has the near wall in front of it. These
    # two look straight down the slit, which is the only line of sight that reaches
    # the root, and are cropped to it.
    ('roof/foot-in-slit_az-90_el14.png',  'roof.step',           -90.0,  14.0, '0.48,0.58,0.26', True),
    ('roof/foot-macro_az-90_el28.png',    'roof.step',           -90.0,  28.0, '0.505,0.52,0.22', True),
    # The blend at the root is tangent to the slit floor, and a flat-shaded z-buffer
    # dithers that tangency at grazing angles. This is the same root from high above,
    # where the two depths separate and the cove renders clean.
    ('roof/foot-macro_az-90_el55.png',    'roof.step',           -90.0,  55.0, '0.50,0.47,0.22', True),
    # The OTHER elevation, camera at the same height as the side elevation but looking
    # straight into the opening: the full-height shutter and the tube standing in it,
    # at eye level rather than from above.
    ('roof/slit-elevation_az-90_el0.png', 'roof.step',           -90.0,   0.0, None, True),
    # The roof plate drops INSIDE the 184.0 mm opening on a 0.8 mm per-side spigot and
    # lands on four integral corner ledges; the 4.0 mm gap along the sides is the
    # disclosed reveal, not the seat. Shot square to a side that reads as a lid that
    # will not shut, so here is the corner, where the seat is what you see.
    ('closed/corner-seat_az-45_el6.png',  'periastra.step',      -45.0,   6.0, None, True),
    ('closed/corner-seat-close_az-45_el6.png','periastra.step',  -45.0,   6.0, '0.50,0.56,0.34', True),
    # The drum all the way round: four azimuths 90 deg apart with the camera just
    # above the ring, uncropped so the whole circumference stays in frame, and at
    # 1800 rather than 1200 so the 11.7 mm ring is legible. Is there any gap or
    # notch in it anywhere?
    ('roof/drum-ring_az0_el6.png',        'roof.step',             0.0,   6.0, None, True, 1800),
    ('roof/drum-ring_az90_el6.png',       'roof.step',            90.0,   6.0, None, True, 1800),
    ('roof/drum-ring_az180_el6.png',      'roof.step',           180.0,   6.0, None, True, 1800),
    ('roof/drum-ring_az-90_el6.png',      'roof.step',           -90.0,   6.0, None, True, 1800),
]


def source_path(name):
    return CAD/name if name == 'periastra.step' else STATES/name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--only', default=None, help='substring filter on the output path')
    parser.add_argument('--size', type=int, default=1200)
    # 0.05 was the archive's value. The cove at the telescope's root is tangent to
    # the slit floor, and at that tangency a z-buffer renderer with flat shading
    # dithers the two near-coincident depths; a finer triangulation also removes the
    # visible banding on the dome. This changes only how the exact STEP is
    # triangulated for display, never the geometry.
    parser.add_argument('--tolerance', type=float, default=0.01)
    args = parser.parse_args()
    for out, source, az, el, crop, added, *size in FRAMES:
        if args.only and args.only not in out:
            continue
        target = SNAP/out
        target.parent.mkdir(parents=True, exist_ok=True)
        argv = [sys.executable, str(CAD/'render_frames.py'),
                '--renderer', str(args.renderer), '--source', str(source_path(source)),
                '--out', str(target), '--azimuth', str(az), '--elevation', str(el),
                '--size', str(size[0] if size else args.size),
                '--tolerance', str(args.tolerance), '--provenance', str(target.with_suffix('.json'))]
        if crop:
            argv += ['--crop', crop]
        subprocess.run(argv, check=True, stdout=subprocess.DEVNULL)
        print(('ADDED ' if added else '      ') + out)


if __name__ == '__main__':
    main()
