"""One local deck cell; callers provide local holes, sockets and rib exclusions."""
import params as p
from features.primitives import bounded_box, z_cylinder, top_countersink


def _segments(lo, hi, fixed, width, along_x, exclusions):
    """Drop a whole rib width around access envelopes; never leave thin slivers."""
    blocked = []
    for x0, x1, y0, y1 in exclusions:
        cross0, cross1 = (y0, y1) if along_x else (x0, x1)
        if cross1 < fixed-width/2 or cross0 > fixed+width/2:
            continue
        a, b = (x0, x1) if along_x else (y0, y1)
        blocked.append((max(lo, a-p.DECK_RIB_CLEAR), min(hi, b+p.DECK_RIB_CLEAR)))
    cursor = lo
    for a, b in sorted(blocked):
        if b <= cursor or a >= hi:
            continue
        if a-cursor >= p.DECK_RIB_MIN_SEGMENT:
            yield cursor, a
        cursor = max(cursor, b)
    if hi-cursor >= p.DECK_RIB_MIN_SEGMENT:
        yield cursor, hi


def build_tile(bounds, holes=(), countersinks=(), sockets=(), cutters=(),
               rib_exclusions=()):
    """Top Z0, underside Z−6. Coordinates and all supplied solids are local."""
    x0, x1, y0, y1 = bounds
    tile = bounded_box(x0, x1, y0, y1, -p.DECK_T, 0)
    exclusions = list(rib_exclusions)
    for x, y in holes:
        a = p.DECK_NUT_ACCESS_HALF
        exclusions.append((x-a, x+a, y-a, y+a))
    for cutter in cutters:
        b = cutter.bounding_box()
        exclusions.append((b.min.X, b.max.X, b.min.Y, b.max.Y))
    for along_x in (True, False):
        lo, hi = (x0, x1) if along_x else (y0, y1)
        for fixed in p.DECK_RIB_STATIONS:
            for a, b in _segments(lo, hi, fixed, p.DECK_RIB_T, along_x, exclusions):
                coords = (a,b,fixed-p.DECK_RIB_T/2,fixed+p.DECK_RIB_T/2)
                if not along_x:
                    coords = (coords[2],coords[3],coords[0],coords[1])
                tile += bounded_box(*coords,-p.DECK_T-p.DECK_RIB_DEPTH,-p.DECK_T)
    for x, y in holes:
        tile -= z_cylinder(x,y,-p.DECK_T-p.DECK_RIB_DEPTH,
                           p.DECK_T+p.DECK_RIB_DEPTH,p.M4_BORE/2)
    for x, y in countersinks:
        tile -= top_countersink(x,y,0,p.CSK_HEAD_MAX_H,p.M4_BORE,p.CSK_RECESS_D)
    for x, y in sockets:
        tile -= z_cylinder(x,y,-p.DECK_T,p.DECK_STRAP_SOCKET_DEPTH,
                           p.DECK_STRAP_SOCKET_D/2)
    for cutter in cutters:
        tile -= cutter
    assert len(tile.solids()) == 1, 'Deck cell must remain one printable solid'
    return tile
