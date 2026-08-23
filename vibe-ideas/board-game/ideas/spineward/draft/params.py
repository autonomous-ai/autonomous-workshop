"""All dimensions for spineward, mm. Every number here traces to brief.json."""
import math

# --- reef_board ---------------------------------------------------------
BOARD_VERTEX_R = 119.0        # 238mm corner-to-corner / 2
BOARD_T = 14.0                 # brief.json bbox_mm z
BOARD_SKIRT_CHAMFER = 2.5

PAN_PITCH = 34.0                # reef_board OWNS this
PAN_ACROSS_FLATS = 30.0         # reef_board OWNS this (recesses.width_mm)
PAN_VERTEX_R = (PAN_ACROSS_FLATS / 2.0) / math.cos(math.radians(30))  # 17.32
PAN_DEPTH = 3.0                 # recesses.depth_mm
PAN_RINGS = 3                   # centre + 3 rings = 37 pans

PAN_SOCKET_D = 6.6               # pearl shaft socket in the pan floor
PAN_SOCKET_DEPTH = 10.0

SEED_COLLAR_H = 1.2              # 19 inner pans (relief)
LANDING_BARNACLE_H = 1.5         # 6 outer-corner pans (relief)

# --- urchin_shell --------------------------------------------------------
SHELL_ACROSS_FLATS = 29.0
SHELL_VERTEX_R = (SHELL_ACROSS_FLATS / 2.0) / math.cos(math.radians(30))  # 16.75
SHELL_DOME_H = 18.0
SHELL_TOP_CHAMFER = 3.0          # softens the dome crown edge
SHELL_KNOB_ACROSS_FLATS = 12.0
SHELL_KNOB_H = 16.0
SHELL_TOTAL_H = SHELL_DOME_H + SHELL_KNOB_H  # 34mm, matches bbox_mm z

SHELL_SOCKET_D = 6.6
SHELL_SOCKET_DEPTH = 12.0
SHELL_SOCKET_RADIUS = 11.0       # 6 sockets on this radius, one per face

N_URCHIN_SHELL = 4
SHELL_FLATS = [3, 4, 5, 6]        # one per player -- a player's identity

# A modest ROUND on the knob/finial's own vertical corner edges (where two
# flats meet), not just the top rim: idea.json's own art_direction bars any
# "spike thin enough to snap off or to hurt a hand", and a plain sharp-cornered
# n_flats=3 prism has a full-height 60deg knife edge that both violates that
# and, seen from the iso 3/4 view every render leans on, reads as the point of
# a cone rather than a corner of a flat top (a flat polygon top is, correctly,
# NOT screen-horizontal in any elevated/perspective view -- see
# face_forward_rot_deg's docstring -- so an unrounded corner there looks like
# a peak no matter which way the polygon is rotated). Rounding the corner
# blends that point into a small facet at every camera angle without erasing
# the flats themselves: both radii stay well under the 6mm apothem every
# SHELL_FLATS variant shares (across_flats_to_vertex_r) and the ~2mm apothem
# RACK_FINIAL_VERTEX_R gives its smallest (n=3) variant.
SHELL_KNOB_EDGE_FILLET = 1.8
RACK_FINIAL_EDGE_FILLET = 0.6

# --- spine -----------------------------------------------------------------
SPINE_ACROSS = 11.0               # widest footprint (blade thickness)
SPINE_PEG_D = 6.0
SPINE_PEG_H = 12.0                # fully buried in a shell socket
SPINE_EXPOSED_H = 20.0            # stands proud of the shell
SPINE_TOTAL_H = SPINE_PEG_H + SPINE_EXPOSED_H  # 32mm, matches bbox_mm z
SPINE_BLADE_BASE = (SPINE_ACROSS, 4.0)   # base footprint of the wedge
SPINE_BLADE_TIP = (1.0, 1.0)

N_SPINE = 24

# --- pearl (one/two/three ring, identical geometry) -------------------
PEARL_KNOB_D = 16.0
PEARL_KNOB_H = 11.0
PEARL_SHAFT_D = 6.0
PEARL_SHAFT_H = 16.0
PEARL_TOTAL_H = PEARL_KNOB_H + PEARL_SHAFT_H   # 27mm, matches bbox_mm z
PEARL_RING_H = 1.2

N_PEARL_ONE = 8
N_PEARL_TWO = 5
N_PEARL_THREE = 3

# --- pearl_rack -----------------------------------------------------------
RACK_L = 135.0
RACK_W = 34.0
RACK_H = 22.0
RACK_WELL_D = 17.0
RACK_WELL_DEPTH = 9.0
RACK_N_WELLS = 6
RACK_WELL_PITCH = 16.0
RACK_FINIAL_VERTEX_R = 4.0
RACK_FINIAL_H = 8.0

N_PEARL_RACK = 4
RACK_FLATS = [3, 4, 5, 6]          # matches the seated player's shell knob

# --- tide_pot --------------------------------------------------------------
POT_TRAY_D = 150.0
POT_DRUM_D = 85.0
POT_DRUM_H = 95.0
POT_WALL = 4.0
POT_TRAY_H = 18.0
POT_N_SCALLOPS = 10


def hex_lattice_positions(pitch: float, max_ring: int = 3):
    """37-point triangular lattice: centre + rings of 6/12/18, EXACTLY once.

    Returns (x, y, ring, is_corner) -- is_corner is True only for the 6
    corner points of the OUTERMOST ring (ring == max_ring), the 6 "landing
    shelf" pans. Generated once here and reused for the dish cuts, the
    centre-socket cuts, and the seed/landing relief overlays -- never
    regenerated (see brief.json print_plan).
    """
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

    def axial_to_xy(q, r):
        x = pitch * (q + r / 2.0)
        y = pitch * (r * math.sqrt(3) / 2.0)
        return (x, y)

    pts = [(0.0, 0.0, 0, False)]
    for k in range(1, max_ring + 1):
        q, r = directions[4][0] * k, directions[4][1] * k
        ring = []
        corner_flags = []
        for i in range(6):
            for j in range(k):
                ring.append((q, r))
                corner_flags.append(j == 0)
                q += directions[i][0]
                r += directions[i][1]
        for (qq, rr), corner in zip(ring, corner_flags):
            x, y = axial_to_xy(qq, rr)
            pts.append((x, y, k, corner and k == max_ring))
    return pts


def polygon_pts(n: int, vertex_r: float, rot_deg: float = 0.0):
    """n-sided regular polygon vertices at the given circumradius."""
    return [
        (vertex_r * math.cos(math.radians(rot_deg + i * 360.0 / n)),
         vertex_r * math.sin(math.radians(rot_deg + i * 360.0 / n)))
        for i in range(n)
    ]


def across_flats_to_vertex_r(across_flats: float, n: int = 6) -> float:
    return (across_flats / 2.0) / math.cos(math.pi / n)


# The review tool's "iso" panel (cadcode/scripts/packages/cadpy/render_part.py
# DEFAULT_VIEWS) is elev=24, azim=-58 -- the view a human sees first and the
# one every hero/QA render leans on. Its horizontal viewing azimuth is -58deg.
ISO_VIEW_AZIMUTH_DEG = -58.0


def face_forward_rot_deg(n: int, target_azim_deg: float = ISO_VIEW_AZIMUTH_DEG) -> float:
    """polygon_pts() rot_deg that points a FLAT FACE (not a vertex) at the
    given camera azimuth -- EXCEPT for n=3, where it points a VERTEX at the
    camera instead (see below).

    Evidence: turn spineward-repair -- a vertex-first knob (rot_deg=0) put a
    single point of the polygon toward the iso camera, and the flat top
    behind it read as a pyramid/cone peak in that 3/4 view even though every
    straight elevation view of the same solid was already a plain rectangle
    (mesh top face is genuinely flat -- see build/draft_parts STL vertex
    check). A face-normal aimed at the camera instead shows one clean flat
    facet plus its neighbours curving away, which is what actually lets a
    flat count be counted.

    n=3 special case (turn spineward-repair-2): that fix made shells 02-04
    (4/5/6 flats) read correctly but shell_01 (3 flats) still projected as a
    sharp peak in the iso/front views. For a triangle, "face forward"
    necessarily puts the single OPPOSITE VERTEX at maximum depth directly
    behind the near face -- under this pipeline's elevated iso/front camera
    poses that far vertex sits well above the near face's silhouette and
    reads as a sharp peak. More sides (n>=4) don't have this problem: no
    single vertex sits opposite a single face, so face-forward's depth
    disparity stays small. Pointing a VERTEX at the camera instead (rot_deg
    = target_azim_deg, i.e. face-forward's result + 180/n = +60deg for n=3)
    puts the far, flat EDGE at maximum depth instead of a far vertex, which
    minimizes height disparity and keeps the top reading as flat.
    """
    if n == 3:
        return target_azim_deg
    return target_azim_deg - 180.0 / n
