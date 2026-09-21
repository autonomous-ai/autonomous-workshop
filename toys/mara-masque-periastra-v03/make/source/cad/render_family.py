"""Render the canonical evidence family for this revision.

Every frame the archive being corrected already carried is regenerated here from
the new geometry, and nothing is removed. The frames this correction adds are
marked ADDED: a straight-down view of the roof cropped to the slit, at a scale
where one millimetre is several pixels, and the whole board populated and empty.

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
    ('roof/yoke_az-60_el18.png',          'roof.step',           -60.0,  18.0, None, False),
    ('roof/yoke-close_az-60_el18.png',    'roof.step',           -60.0,  18.0, '0.37,0.46,0.34', False),
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
]


def source_path(name):
    return CAD/name if name == 'periastra.step' else STATES/name


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--renderer', type=Path, required=True)
    parser.add_argument('--only', default=None, help='substring filter on the output path')
    parser.add_argument('--size', type=int, default=1200)
    args = parser.parse_args()
    for out, source, az, el, crop, added, *size in FRAMES:
        if args.only and args.only not in out:
            continue
        target = SNAP/out
        target.parent.mkdir(parents=True, exist_ok=True)
        argv = [sys.executable, str(CAD/'render_frames.py'),
                '--renderer', str(args.renderer), '--source', str(source_path(source)),
                '--out', str(target), '--azimuth', str(az), '--elevation', str(el),
                '--size', str(size[0] if size else args.size), '--provenance', str(target.with_suffix('.json'))]
        if crop:
            argv += ['--crop', crop]
        subprocess.run(argv, check=True, stdout=subprocess.DEVNULL)
        print(('ADDED ' if added else '      ') + out)


if __name__ == '__main__':
    main()
