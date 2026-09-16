"""Parameters and part builders for the Planet Shear matter rank-4 piece.

One printed body: a stylised Earth standing on a flat cylindrical disc that
carries the rank numeral.  The body is split into colour groups -- disc, ice
shelf, ocean, land, drylands, polar ice -- so the shop can finish each in its
own colour.  Every group is a logical part; none of them is printed separately.
"""
import math

from build123d import (
    Align, Box, Cone, Cylinder, Plane, Pos, Rectangle, Sphere, Vector, fillet, loft,
)
from shapely.geometry import MultiPolygon, Polygon as PlanarPolygon, box as planar_box
from shapely.geometry.polygon import orient

import planet_shear_atlas as atlas
from planet_shear_geo import polar_cap_cone, relief_blank as relief_wall_solid, unit_dir

# --- immutable requirements ------------------------------------------------
BASE_DIAMETER = 34.0        # [Wish] hard dimension
BASE_HEIGHT = 5.0           # [Wish] hard dimension
GLOBE_DIAMETER = 21.08      # [Wish] hard dimension
RELIEF = 1.0                # [Wish] continents stand 1.0 mm proud of the ocean
RANK_DIGIT = 4              # [Wish] rank numeral, seven-segment, raised, on the wall

# --- reference-led styling -------------------------------------------------
BASE_TOP_ROUND = 0.6        # [observed] the disc reads with a softened top edge
LON_OFFSET = -65.0          # [observed] Atlantic face toward the viewer
GLYPH_HEIGHT = 3.6          # [observed] numeral occupies most of the wall band
GLYPH_WIDTH = 2.8           # [observed]
GLYPH_STROKE = 1.0          # [inferred] over two extruded lines at a 0.4 mm nozzle
GLYPH_RELIEF = 0.45         # [observed] numeral stands slightly proud
GLYPH_RAMP = 1.20           # [inferred] rise per mm of relief under each stroke bottom
GLYPH_DRAFT = 0.50          # [inferred] side and top draft, so each stroke catches light
GLYPH_BOTTOM = 0.4          # [inferred] centres the numeral on the flat band

# --- printability choices --------------------------------------------------
NOZZLE = 0.4                # [assumed] baseline slicer nozzle
GLOBE_SINK = 2.0            # [inferred] globe seats into the disc so a shelf can form
SEAT_LAT = -42.0            # [inferred] ice shelf meets the globe at this latitude
SEAT_ANGLE = -12.0          # [inferred] deg from vertical; negative spreads the foot outward
RELIEF_FLOOR_LAT = -38.0    # [inferred] no relief where the globe faces downward
MIN_PIECE_AREA = 2.0        # deg^2; below this a clipped sliver is dropped
RING_STEP = 6.0             # deg; outline edges are densified to this before projection

# --- derived ---------------------------------------------------------------
BASE_RADIUS = BASE_DIAMETER / 2.0
GLOBE_RADIUS = GLOBE_DIAMETER / 2.0
GLOBE_CENTRE_Z = BASE_HEIGHT - GLOBE_SINK + GLOBE_RADIUS
RELIEF_RADIUS = GLOBE_RADIUS + RELIEF
CAP_CONE_FAR = 2.0 * RELIEF_RADIUS
SEAT_TOP_RADIUS = GLOBE_RADIUS * math.cos(math.radians(SEAT_LAT))
SEAT_TOP_Z = GLOBE_CENTRE_Z + GLOBE_RADIUS * math.sin(math.radians(SEAT_LAT))
SEAT_BASE_RADIUS = SEAT_TOP_RADIUS - math.tan(math.radians(SEAT_ANGLE)) * (SEAT_TOP_Z - BASE_HEIGHT)
GLOBE_AT_DISC_RADIUS = math.sqrt(GLOBE_RADIUS ** 2 - (GLOBE_CENTRE_Z - BASE_HEIGHT) ** 2)

# --- colours: sRGB hex read off the sealed reference image -----------------
DISC_BLUE = (0.086, 0.318, 0.769)     # #1551c4
OCEAN_BLUE = (0.106, 0.353, 0.831)    # #1b5ad4
LAND_GREEN = (0.549, 0.643, 0.239)    # #8ca43d
DRYLAND_TAN = (0.816, 0.616, 0.353)   # #d09d5a
ICE_WHITE = (0.949, 0.961, 0.973)     # #f2f5f8


def check_parameters():
    """Algebraic invariants, asserted before any geometry is built."""
    assert GLOBE_RADIUS * 2 == GLOBE_DIAMETER
    assert GLOBE_DIAMETER < BASE_DIAMETER, "globe must sit inside the disc footprint"
    assert SEAT_LAT >= -45.0, "ice seat must cover the globe down past 45 deg"
    assert SEAT_ANGLE < 45.0, "ice seat wall would need support"
    assert SEAT_TOP_Z > BASE_HEIGHT, "ice seat would start below the disc face"
    assert SEAT_BASE_RADIUS > GLOBE_AT_DISC_RADIUS, "ice seat is narrower than the globe it holds"
    assert RELIEF_FLOOR_LAT >= SEAT_LAT + 3.0, "relief would overhang the ice seat rim"
    assert GLYPH_STROKE >= 2 * NOZZLE, "numeral stroke thinner than two extruded lines"
    assert GLYPH_BOTTOM + GLYPH_HEIGHT <= BASE_HEIGHT - BASE_TOP_ROUND, "numeral overruns the wall"
    assert GLYPH_RELIEF * (GLYPH_RAMP + GLYPH_DRAFT) < GLYPH_STROKE, "draft would consume the middle bar"
    assert 2 * GLYPH_DRAFT * GLYPH_RELIEF < GLYPH_STROKE, "side draft would consume the stroke"
    assert 0 <= RANK_DIGIT <= 9


def _half_space_above(z):
    span = 4 * BASE_DIAMETER
    return Pos(0, 0, z) * Box(span, span, span, align=(Align.CENTER, Align.CENTER, Align.MIN))


def globe_sphere():
    return Pos(0, 0, GLOBE_CENTRE_Z) * Sphere(GLOBE_RADIUS)


def ocean_seat():
    """Conical seat from the disc face up to the globe, finished as ocean.

    A tangent round would meet both the disc and the globe at zero angle, and the
    slivers that tessellates into read as a torn fringe around the foot of the
    globe.  A cone lands on both with a definite edge.

    It is finished in the ocean's own blue rather than in ice white: as white it
    read to an independent reviewer as bare unpainted material at the foot of
    the piece, which cost more than the band of ice it was standing in for.
    """
    return Pos(0, 0, BASE_HEIGHT) * Cone(
        SEAT_BASE_RADIUS, SEAT_TOP_RADIUS, SEAT_TOP_Z - BASE_HEIGHT,
        align=(Align.CENTER, Align.CENTER, Align.MIN))


def fused_body():
    """Disc, ice seat and globe joined into the outer form of the piece."""
    disc = Cylinder(BASE_RADIUS, BASE_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
    top_rim = [e for e in disc.edges() if abs(e.center().Z - BASE_HEIGHT) < 1e-6]
    assert len(top_rim) == 1, f"expected one disc top rim, found {len(top_rim)}"
    return fillet(top_rim, BASE_TOP_ROUND) + ocean_seat() + globe_sphere()


# --- the rank numeral ------------------------------------------------------
SEVEN_SEGMENT = {
    0: "abcdef", 1: "bc", 2: "abdeg", 3: "abcdg", 4: "bcfg",
    5: "acdfg", 6: "acdefg", 7: "abc", 8: "abcdefg", 9: "abcdfg",
}


def _segment_boxes(digit):
    """Segment rectangles as (centre_x, centre_z, width, height) in glyph space."""
    half_w, half_h = GLYPH_WIDTH / 2.0, GLYPH_HEIGHT / 2.0
    s, bar = GLYPH_STROKE, GLYPH_WIDTH
    arm = GLYPH_HEIGHT / 2.0
    layout = {
        "a": (0.0, half_h - s / 2, bar, s),
        "b": (half_w - s / 2, half_h / 2, s, arm),
        "c": (half_w - s / 2, -half_h / 2, s, arm),
        "d": (0.0, -half_h + s / 2, bar, s),
        "e": (-half_w + s / 2, -half_h / 2, s, arm),
        "f": (-half_w + s / 2, half_h / 2, s, arm),
        "g": (0.0, 0.0, bar, s),
    }
    return [layout[name] for name in SEVEN_SEGMENT[digit]]


def _stroke_blank(cx, bottom, top, half_w):
    """One drafted segment blank, narrowing as it stands out of the wall.

    The underside has to rise faster than it protrudes or it is a ceiling over
    open air; the sides and top are drafted as well, so every face of the
    numeral catches the light at its own angle instead of lying flush with the
    wall it sits on.
    """
    sections = []
    for reach in (-GLYPH_STROKE, GLYPH_RELIEF):
        width = 2.0 * (half_w - GLYPH_DRAFT * reach)
        low, high = bottom + GLYPH_RAMP * reach, top - GLYPH_DRAFT * reach
        plane = Plane(origin=(cx, -(BASE_RADIUS + reach), (low + high) / 2.0),
                      x_dir=(1, 0, 0), z_dir=(0, -1, 0))
        sections.append(plane * Rectangle(width, high - low))
    return loft(sections, ruled=True)


def rank_numeral():
    """Raised seven-segment numeral on the front of the disc wall."""
    centre_z = GLYPH_BOTTOM + GLYPH_HEIGHT / 2.0
    ring = (Cylinder(BASE_RADIUS + GLYPH_RELIEF, BASE_HEIGHT,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
            - Cylinder(BASE_RADIUS, BASE_HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    glyph = None
    for cx, cz, w, h in _segment_boxes(RANK_DIGIT):
        blank = _stroke_blank(cx, centre_z + cz - h / 2.0, centre_z + cz + h / 2.0, w / 2.0)
        stroke = blank & ring
        glyph = stroke if glyph is None else glyph + stroke
    return glyph


# --- relief ----------------------------------------------------------------
def _planar_parts(shape):
    if shape.is_empty:
        return []
    if isinstance(shape, MultiPolygon):
        return [g for g in shape.geoms if not g.is_empty]
    if isinstance(shape, PlanarPolygon):
        return [shape]
    return []


def _densify(ring, step=None):
    """Split long outline edges so a parallel stays a parallel once projected.

    Every straight segment becomes a great circle on the globe.  A clip along a
    line of latitude is a small circle, so as one long segment it bows across
    the outline and the section polygon self-intersects.
    """
    step = RING_STEP if step is None else step
    dense = []
    for i, (lon, lat) in enumerate(ring):
        nlon, nlat = ring[(i + 1) % len(ring)]
        dense.append((lon, lat))
        cuts = int(max(abs(nlon - lon), abs(nlat - lat)) / step)
        for k in range(1, cuts):
            t = k / cuts
            dense.append((lon + (nlon - lon) * t, lat + (nlat - lat) * t))
    return dense


def outline_rings(outline, floor=None):
    """Counter-clockwise, densified rings for one outline, clipped to `floor`.

    Relief is clipped at the latitude below which the globe faces downward.  A
    colour-only outline such as the southern ice has no such limit, and passing
    `floor=-90` keeps it whole.
    """
    poly = PlanarPolygon(outline)
    if not poly.is_valid:
        poly = poly.buffer(0)
    poly = poly.intersection(planar_box(-400, RELIEF_FLOOR_LAT if floor is None else floor,
                                        400, 90))
    rings = []
    for piece in _planar_parts(poly):
        if piece.area < MIN_PIECE_AREA:
            continue
        ring = list(orient(piece, sign=1.0).exterior.coords)[:-1]
        rings.append(_densify(ring))
    return rings


def relief_blank(outlines, lean=True, floor=None):
    """Union of the wall solids for every outline in `outlines`."""
    blank = None
    for outline in outlines:
        for ring in outline_rings(outline, floor):
            solid = relief_wall_solid([(lon + LON_OFFSET, lat) for lon, lat in ring],
                                      GLOBE_RADIUS, RELIEF, lean)
            blank = solid if blank is None else blank + solid
    return blank


def relief_shell():
    return Sphere(RELIEF_RADIUS) - Sphere(GLOBE_RADIUS)


def relief_groups():
    """(land, dryland, ice) relief solids in globe-local coordinates."""
    shell = relief_shell()
    cap = polar_cap_cone(atlas.ARCTIC_CAP_LAT, GLOBE_RADIUS, CAP_CONE_FAR)
    ice = shell & (relief_blank(atlas.ICEFIELDS) + cap)
    ground = (shell & relief_blank(atlas.LANDMASSES)) - ice
    # drylands only recolour ground that is already there, so their walls are
    # interior faces and never need the printable lean
    dry_cones = relief_blank(atlas.DRYLANDS, lean=False)
    return ground - dry_cones, ground & dry_cones, ice


def _outline_direction(outlines):
    """Mean unit direction of every vertex in a group of outlines."""
    total = Vector(0, 0, 0)
    count = 0
    for outline in outlines:
        for lon, lat in outline:
            total = total + unit_dir(lon + LON_OFFSET, lat)
            count += 1
    return (total * (1.0 / count)).normalized()


def _solid_direction(solid):
    centre = solid.bounding_box().center()
    return Vector(centre.X, centre.Y, centre.Z).normalized()


def _name_solids(compound, groups, label):
    """Give each body of a fused relief compound the name of the outline group it is.

    The compounds are built exactly as they were before the parts were named, so
    naming never changes a byte of geometry: it only decides which body carries
    which production-part name.
    """
    solids = compound.solids()
    targets = {name: _outline_direction(outlines) for name, outlines in groups}
    if len(solids) != len(targets):
        raise AssertionError(
            "%s built %d bodies for %d named groups" % (label, len(solids), len(targets))
        )
    matched = {}
    for solid in solids:
        here = _solid_direction(solid)
        name = max((n for n in targets if n not in matched), key=lambda n: here.dot(targets[n]))
        matched[name] = solid
    # emit in the atlas' own order so the sealed occurrence order is stable
    return {name: matched[name] for name, _outlines in groups}


def named_relief():
    """One named body per production part, in globe-local coordinates."""
    land, dryland, ice = relief_groups()
    named = _name_solids(land, atlas.LANDMASS_GROUPS, "continental relief")
    named.update(_name_solids(dryland, atlas.DRYLAND_GROUPS, "dryland relief"))
    if len(ice.solids()) != 1:
        raise AssertionError("polar ice built %d bodies" % len(ice.solids()))
    named["polar_ice"] = ice.solids()[0]
    return named


# --- the printed part ------------------------------------------------------
def build_piece():
    """The whole printed body as one fused solid, disc face on the bed."""
    check_parameters()
    land, dryland, ice = relief_groups()
    at_globe = Pos(0, 0, GLOBE_CENTRE_Z)
    piece = (fused_body() + rank_numeral() + at_globe * land + at_globe * dryland
             + at_globe * ice)
    assert len(piece.solids()) == 1, f"piece split into {len(piece.solids())} solids"
    return piece


# --- colour groups, all in assembly coordinates ----------------------------
def build_base():
    body = fused_body() - globe_sphere()
    return (body & _half_space_above(-BASE_HEIGHT)) - _half_space_above(BASE_HEIGHT) + rank_numeral()


def build_seat():
    return (fused_body() - globe_sphere()) & _half_space_above(BASE_HEIGHT)


def build_ocean():
    return globe_sphere()


def build_base():
    body = fused_body() - globe_sphere()
    return (body & _half_space_above(-BASE_HEIGHT)) - _half_space_above(BASE_HEIGHT) + rank_numeral()


def build_seat():
    return (fused_body() - globe_sphere()) & _half_space_above(BASE_HEIGHT)


def build_ocean():
    return globe_sphere()


def build_relief():
    """Named relief bodies lifted into assembly coordinates."""
    at_globe = Pos(0, 0, GLOBE_CENTRE_Z)
    return {name: at_globe * solid for name, solid in named_relief().items()}
