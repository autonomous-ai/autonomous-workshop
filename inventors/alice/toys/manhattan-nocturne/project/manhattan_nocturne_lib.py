"""Geometry builders for Manhattan Nocturne.

Parts are built in print orientation: footprint centered on XY, bed datum Z=0.
The assembly entry is the only file that applies chess-square placements.
"""

from __future__ import annotations

from build123d import (
    Align,
    Axis,
    Box,
    BuildSketch,
    Color,
    Compound,
    Cone,
    Cylinder,
    Location,
    Plane,
    Polygon,
    Rectangle,
    Torus,
    extrude,
    fillet,
    loft,
    revolve,
)

import params as p


def _zloc(z: float) -> Location:
    return Location((0.0, 0.0, z))


def _box(x: float, y: float, z: float):
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _cylinder(radius: float, height: float):
    return Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _cone(radius_bottom: float, radius_top: float, height: float):
    return Cone(radius_bottom, radius_top, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _fuse_checked(shape, *details):
    result = shape.fuse(*details)
    assert len(result.solids()) == 1, "feature union must remain one physical body"
    assert result.is_valid, "feature union must remain a valid B-rep"
    return result


def _cut_checked(shape, *cutters):
    result = shape.cut(*cutters)
    assert len(result.solids()) == 1, "subtractive feature must not split the physical body"
    assert result.is_valid, "subtractive feature must remain a valid B-rep"
    return result


def _revolved_profile(profile: tuple[tuple[float, float], ...]):
    """Revolve a closed radius/Z silhouette as one clean axisymmetric solid."""

    with BuildSketch(Plane.XZ) as sketch:
        Polygon(*profile)
    result = revolve(sketch.sketch, axis=Axis.Z)
    assert len(result.solids()) == 1
    assert result.is_valid
    return result


def _ruled_rect_loft(
    lower_x: float,
    lower_y: float,
    lower_z: float,
    upper_x: float,
    upper_y: float,
    upper_z: float,
    through_z: float | None = None,
    hold_lower_until_z: float | None = None,
):
    """Make a printable rectangular frustum, optionally extended through Z."""

    with BuildSketch(Plane.XY.offset(lower_z)) as lower:
        Rectangle(lower_x, lower_y)
    sections = [lower.sketch]
    if hold_lower_until_z is not None:
        assert lower_z < hold_lower_until_z < upper_z
        with BuildSketch(Plane.XY.offset(hold_lower_until_z)) as shoulder:
            Rectangle(lower_x, lower_y)
        sections.append(shoulder.sketch)
    with BuildSketch(Plane.XY.offset(upper_z)) as upper:
        Rectangle(upper_x, upper_y)
    sections.append(upper.sketch)
    if through_z is not None:
        with BuildSketch(Plane.XY.offset(through_z)) as through:
            Rectangle(upper_x, upper_y)
        sections.append(through.sketch)
    result = loft(sections, ruled=True)
    assert len(result.solids()) == 1
    assert result.is_valid
    return result


def _stone_base_groove(z: float):
    return _zloc(z) * Torus(
        major_radius=p.BASE_GROOVE_MAJOR_RADIUS,
        minor_radius=p.BASE_GROOVE_MINOR_RADIUS,
    )


def _steel_base_rails():
    """Three printable rails leave two tactile grooves between them."""

    return [
        _zloc(z) * _cylinder(p.STEEL_BASE_RAIL_RADIUS, p.STEEL_BASE_RAIL_HEIGHT)
        for z in p.STEEL_BASE_RAIL_Z
    ]


def _stone_horizontal_bands():
    return [
        _zloc(z) * _cylinder(p.STONE_BAND_RADIUS, p.STONE_BAND_HEIGHT)
        for z in p.STONE_BAND_Z
    ]


def _steel_vertical_fins():
    fins = []
    for x in (-p.STEEL_FIN_CENTER_RADIUS, p.STEEL_FIN_CENTER_RADIUS):
        fins.append(
            Location((x, 0.0, p.STEEL_FIN_START_Z))
            * _box(p.STEEL_FIN_RADIAL, p.STEEL_FIN_TANGENTIAL, p.STEEL_FIN_HEIGHT)
        )
    for y in (-p.STEEL_FIN_CENTER_RADIUS, p.STEEL_FIN_CENTER_RADIUS):
        fins.append(
            Location((0.0, y, p.STEEL_FIN_START_Z))
            * _box(p.STEEL_FIN_TANGENTIAL, p.STEEL_FIN_RADIAL, p.STEEL_FIN_HEIGHT)
        )
    return fins


def _stone_square_terraces(tiers):
    """Horizontal masonry ledges that continue Stone's code up a tower."""

    terraces = []
    for z, tower_size in tiers:
        terrace_size = tower_size + 2.0 * p.UPPER_STONE_TERRACE_PROJECTION
        terraces.append(
            _zloc(z)
            * _box(terrace_size, terrace_size, p.UPPER_STONE_TERRACE_HEIGHT)
        )
    return terraces


def _steel_square_ribs(tiers):
    """Four façade ribs per tier that continue Steel's code vertically."""

    ribs = []
    for z, height, tower_size in tiers:
        face_center = tower_size / 2.0
        for x in (-face_center, face_center):
            ribs.append(
                Location((x, 0.0, z))
                * _box(
                    p.UPPER_STEEL_RIB_RADIAL,
                    p.UPPER_STEEL_RIB_TANGENTIAL,
                    height,
                )
            )
        for y in (-face_center, face_center):
            ribs.append(
                Location((0.0, y, z))
                * _box(
                    p.UPPER_STEEL_RIB_TANGENTIAL,
                    p.UPPER_STEEL_RIB_RADIAL,
                    height,
                )
            )
    return ribs


def _pawn_upper_side_code(side: str):
    if side == "stone":
        return [
            _zloc(z)
            * _cylinder(
                p.PAWN_STONE_UPPER_BAND_RADIUS,
                p.UPPER_STONE_TERRACE_HEIGHT,
            )
            for z in p.PAWN_STONE_UPPER_BAND_Z
        ]

    fins = []
    center = p.PAWN_STEEL_UPPER_FIN_CENTER_RADIUS
    for x in (-center, center):
        fins.append(
            Location((x, 0.0, p.PAWN_STEEL_UPPER_FIN_Z))
            * _box(
                p.UPPER_STEEL_RIB_RADIAL,
                p.UPPER_STEEL_RIB_TANGENTIAL,
                p.PAWN_STEEL_UPPER_FIN_HEIGHT,
            )
        )
    for y in (-center, center):
        fins.append(
            Location((0.0, y, p.PAWN_STEEL_UPPER_FIN_Z))
            * _box(
                p.UPPER_STEEL_RIB_TANGENTIAL,
                p.UPPER_STEEL_RIB_RADIAL,
                p.PAWN_STEEL_UPPER_FIN_HEIGHT,
            )
        )
    return fins


def _knight_upper_side_code(side: str):
    details = []
    face_center = p.KNIGHT_DEPTH / 2.0
    if side == "stone":
        for z, width in p.KNIGHT_STONE_FACE_BANDS:
            for y in (-face_center, face_center):
                details.append(
                    Location((0.0, y, z))
                    * _box(
                        width,
                        p.UPPER_STEEL_RIB_RADIAL,
                        p.UPPER_STONE_TERRACE_HEIGHT,
                    )
                )
    else:
        for y in (-face_center, face_center):
            details.append(
                Location((p.KNIGHT_STEEL_RIB_X, y, p.KNIGHT_STEEL_RIB_Z))
                * _box(
                    p.UPPER_STEEL_RIB_TANGENTIAL,
                    p.UPPER_STEEL_RIB_RADIAL,
                    p.KNIGHT_STEEL_RIB_HEIGHT,
                )
            )
    return details


def _tower_side_code(side: str, stone_terraces, steel_rib_tiers):
    if side == "stone":
        return _stone_square_terraces(stone_terraces)
    return _steel_square_ribs(steel_rib_tiers)


def build_pedestal(side: str):
    """Build the shared base with tactile side coding, not color dependence."""

    pedestal = _revolved_profile(p.PEDESTAL_PROFILE)
    if side == "stone":
        pedestal = _fuse_checked(pedestal, *_stone_horizontal_bands())
        pedestal = _cut_checked(
            pedestal,
            *(_stone_base_groove(z) for z in p.STONE_GROOVE_Z),
        )
    elif side == "steel":
        pedestal = _fuse_checked(
            pedestal,
            *_steel_base_rails(),
            *_steel_vertical_fins(),
        )
    else:
        raise ValueError(f"unknown army side: {side!r}")
    pedestal.label = f"{side}_tactile_pedestal"
    return pedestal


def build_pawn(side: str):
    """Rooftop water tower: the smallest repeated Manhattan silhouette."""

    shape = build_pedestal(side)
    # Tank wall and roof are one revolved silhouette. A former 0.55 mm axial
    # overlap left a shallow annular tank lip above the taper on fine meshes.
    tank_roof_profile = (
        (0.0, p.PAWN_TANK_Z),
        (p.PAWN_TANK_RADIUS, p.PAWN_TANK_Z),
        (p.PAWN_ROOF_RADIUS_BOTTOM, p.PAWN_ROOF_Z),
        (p.PAWN_ROOF_RADIUS_TOP, p.PAWN_ROOF_Z + p.PAWN_ROOF_HEIGHT),
        (0.0, p.PAWN_ROOF_Z + p.PAWN_ROOF_HEIGHT),
    )
    shape = _fuse_checked(
        shape,
        _zloc(p.PAWN_COLUMN_Z)
        * _cylinder(p.PAWN_COLUMN_RADIUS_BOTTOM, p.PAWN_COLUMN_STRAIGHT_HEIGHT),
        _zloc(p.PAWN_COLUMN_TAPER_Z)
        * _cone(
            p.PAWN_COLUMN_RADIUS_BOTTOM,
            p.PAWN_COLUMN_RADIUS_TOP,
            p.PAWN_COLUMN_TAPER_HEIGHT,
        ),
        _revolved_profile(tank_roof_profile),
        _zloc(p.PAWN_FINIAL_Z) * _cylinder(p.PAWN_FINIAL_RADIUS, p.PAWN_FINIAL_HEIGHT),
    )
    shape = _fuse_checked(shape, *_pawn_upper_side_code(side))
    shape.label = f"{side}_pawn_water_tower"
    return shape


def build_rook(side: str):
    """Square masonry tower with setbacks and four readable parapet corners."""

    shape = build_pedestal(side)
    shape = _fuse_checked(
        shape,
        _zloc(p.ROOK_PEDESTAL_CROWN_Z)
        * _cylinder(p.ROOK_PEDESTAL_CROWN_RADIUS, p.ROOK_PEDESTAL_CROWN_HEIGHT),
        *(
            _zloc(z) * _box(size, size, height)
            for z, size, height in p.ROOK_FOOTING_TIERS
        ),
        _zloc(p.ROOK_TOWER_Z) * _box(p.ROOK_TOWER_SIZE, p.ROOK_TOWER_SIZE, p.ROOK_TOWER_HEIGHT),
        _zloc(p.ROOK_SETBACK_Z) * _box(p.ROOK_SETBACK_SIZE, p.ROOK_SETBACK_SIZE, p.ROOK_SETBACK_HEIGHT),
        _zloc(p.ROOK_ROOF_Z) * _box(p.ROOK_ROOF_SIZE, p.ROOK_ROOF_SIZE, p.ROOK_ROOF_HEIGHT),
    )
    for x in (-p.ROOK_TURRET_OFFSET, p.ROOK_TURRET_OFFSET):
        for y in (-p.ROOK_TURRET_OFFSET, p.ROOK_TURRET_OFFSET):
            turret = Location((x, y, p.ROOK_TURRET_Z)) * _box(
                p.ROOK_TURRET_SIZE, p.ROOK_TURRET_SIZE, p.ROOK_TURRET_HEIGHT
            )
            shape = _fuse_checked(shape, turret)
    shape = _fuse_checked(
        shape,
        *_tower_side_code(side, p.ROOK_STONE_TERRACES, p.ROOK_STEEL_RIB_TIERS),
    )
    shape.label = f"{side}_rook_masonry_tower"
    return shape


def build_knight(side: str):
    """Angular bridge tower: horse-readable in profile, architectural in detail."""

    shape = build_pedestal(side)
    # One revolved silhouette carries the D13.9 pedestal into the D18.4
    # footing. Keeping the flare and footing in one B-rep avoids a shallow
    # annular underside at their former Boolean seam on fine STL exports.
    footing_profile = (
        (0.0, p.KNIGHT_FOOTING_FLARE_Z),
        (p.KNIGHT_FOOTING_FLARE_RADIUS_BOTTOM, p.KNIGHT_FOOTING_FLARE_Z),
        (p.KNIGHT_FOOTING_RADIUS, p.KNIGHT_FOOTING_SHOULDER_Z),
        (p.KNIGHT_FOOTING_RADIUS, p.KNIGHT_FOOTING_TOP_Z),
        (0.0, p.KNIGHT_FOOTING_TOP_Z),
    )
    shape = _fuse_checked(
        shape,
        _revolved_profile(footing_profile),
    )
    with BuildSketch(Plane.XZ) as profile:
        Polygon(*p.KNIGHT_PROFILE)
    bridge_tower = extrude(profile.sketch, amount=p.KNIGHT_DEPTH / 2.0, both=True)
    extrusion_edges = set(bridge_tower.edges().filter_by(Axis.Y))
    face_perimeter = [edge for edge in bridge_tower.edges() if edge not in extrusion_edges]
    bridge_tower = fillet(face_perimeter, radius=p.KNIGHT_FACE_EDGE_FILLET)
    assert len(bridge_tower.solids()) == 1 and bridge_tower.is_valid
    arch = Location((p.KNIGHT_ARCH_CENTER_X, 0.0, p.KNIGHT_ARCH_Z)) * _box(
        p.KNIGHT_ARCH_WIDTH,
        p.KNIGHT_DEPTH + 2.0 * p.BOOLEAN_OVERSHOOT,
        p.KNIGHT_ARCH_HEIGHT,
    )
    bridge_tower = _cut_checked(bridge_tower, arch)
    shape = _fuse_checked(shape, bridge_tower)
    shape = _fuse_checked(shape, *_knight_upper_side_code(side))
    shape.label = f"{side}_knight_bridge_tower"
    return shape


def build_bishop(side: str):
    """Stepped skyscraper with a bishop-readable diagonal avenue crown."""

    shape = build_pedestal(side)
    shape = _fuse_checked(
        shape,
        _zloc(p.BISHOP_TOWER_Z)
        * _box(p.BISHOP_TOWER_SIZE, p.BISHOP_TOWER_SIZE, p.BISHOP_TOWER_HEIGHT),
        _zloc(p.BISHOP_SETBACK_ONE_Z)
        * _box(
            p.BISHOP_SETBACK_ONE_SIZE,
            p.BISHOP_SETBACK_ONE_SIZE,
            p.BISHOP_SETBACK_ONE_HEIGHT,
        ),
        _zloc(p.BISHOP_SETBACK_TWO_Z)
        * _box(
            p.BISHOP_SETBACK_TWO_SIZE,
            p.BISHOP_SETBACK_TWO_SIZE,
            p.BISHOP_SETBACK_TWO_HEIGHT,
        ),
        _zloc(p.BISHOP_CROWN_Z)
        * _box(p.BISHOP_CROWN_SIZE, p.BISHOP_CROWN_SIZE, p.BISHOP_CROWN_HEIGHT),
        _zloc(p.BISHOP_SPIRE_LOWER_Z)
        * _box(
            p.BISHOP_SPIRE_LOWER_SIZE,
            p.BISHOP_SPIRE_LOWER_SIZE,
            p.BISHOP_SPIRE_LOWER_HEIGHT,
        ),
        _zloc(p.BISHOP_SPIRE_MID_Z)
        * _box(
            p.BISHOP_SPIRE_MID_SIZE,
            p.BISHOP_SPIRE_MID_SIZE,
            p.BISHOP_SPIRE_MID_HEIGHT,
        ),
        _zloc(p.BISHOP_SPIRE_TOP_Z)
        * _box(
            p.BISHOP_SPIRE_TOP_SIZE,
            p.BISHOP_SPIRE_TOP_SIZE,
            p.BISHOP_SPIRE_TOP_HEIGHT,
        ),
    )
    shape = _fuse_checked(
        shape,
        *_tower_side_code(side, p.BISHOP_STONE_TERRACES, p.BISHOP_STEEL_RIB_TIERS),
    )
    with BuildSketch(Plane.XZ) as slot_profile:
        Polygon(
            (-p.BISHOP_SLOT_WIDTH / 2.0, p.BISHOP_SLOT_BOTTOM_LEFT_Z),
            (p.BISHOP_SLOT_WIDTH / 2.0, p.BISHOP_SLOT_BOTTOM_RIGHT_Z),
            (p.BISHOP_SLOT_WIDTH / 2.0, p.BISHOP_SLOT_TOP_Z),
            (-p.BISHOP_SLOT_WIDTH / 2.0, p.BISHOP_SLOT_TOP_Z),
        )
    slot = extrude(slot_profile.sketch, amount=p.BISHOP_SLOT_DEPTH / 2.0, both=True)
    shape = _cut_checked(shape, slot)
    shape.label = f"{side}_bishop_light_canyon"
    return shape


def build_queen(side: str):
    """Four-sided, broad Art Deco fan crown visible from every board edge."""

    shape = build_pedestal(side)
    shape = _fuse_checked(
        shape,
        _zloc(p.QUEEN_TOWER_Z)
        * _box(p.QUEEN_TOWER_SIZE, p.QUEEN_TOWER_SIZE, p.QUEEN_TOWER_HEIGHT),
        _zloc(p.QUEEN_SETBACK_Z)
        * _box(p.QUEEN_SETBACK_SIZE, p.QUEEN_SETBACK_SIZE, p.QUEEN_SETBACK_HEIGHT),
        _zloc(p.QUEEN_CROWN_BASE_Z)
        * _box(
            p.QUEEN_CROWN_BASE_SIZE,
            p.QUEEN_CROWN_BASE_SIZE,
            p.QUEEN_CROWN_BASE_HEIGHT,
        ),
    )

    with BuildSketch(Plane.XZ) as fan_profile:
        Polygon(*p.QUEEN_FAN_PROFILE)
    fan_x = extrude(fan_profile.sketch, amount=p.QUEEN_FAN_THICKNESS / 2.0, both=True)
    fan_y = Location((0.0, 0.0, 0.0), (0.0, 0.0, p.QUEEN_FAN_ROTATION_DEG)) * fan_x
    fan_crown = _fuse_checked(fan_x, fan_y)
    shape = _fuse_checked(shape, fan_crown)
    shape = _fuse_checked(
        shape,
        *_tower_side_code(side, p.QUEEN_STONE_TERRACES, p.QUEEN_STEEL_RIB_TIERS),
    )
    shape.label = f"{side}_queen_art_deco_fan"
    return shape


def build_king(side: str):
    """Neo-Gothic setback stack with a chunky, printable beacon cross."""

    shape = build_pedestal(side)
    shape = _fuse_checked(
        shape,
        _zloc(p.KING_TOWER_Z)
        * _box(p.KING_TOWER_SIZE, p.KING_TOWER_SIZE, p.KING_TOWER_HEIGHT),
        _zloc(p.KING_SETBACK_ONE_Z)
        * _box(
            p.KING_SETBACK_ONE_SIZE,
            p.KING_SETBACK_ONE_SIZE,
            p.KING_SETBACK_ONE_HEIGHT,
        ),
        _zloc(p.KING_SETBACK_TWO_Z)
        * _box(
            p.KING_SETBACK_TWO_SIZE,
            p.KING_SETBACK_TWO_SIZE,
            p.KING_SETBACK_TWO_HEIGHT,
        ),
        _zloc(p.KING_SPIRE_PLINTH_Z)
        * _box(
            p.KING_SPIRE_PLINTH_SIZE,
            p.KING_SPIRE_PLINTH_SIZE,
            p.KING_SPIRE_PLINTH_HEIGHT,
        ),
        _zloc(p.KING_SPIRE_Z)
        * _cone(p.KING_SPIRE_RADIUS_BOTTOM, p.KING_SPIRE_RADIUS_TOP, p.KING_SPIRE_HEIGHT),
        _zloc(p.KING_CROSS_Z)
        * _box(p.KING_CROSS_THICKNESS, p.KING_CROSS_THICKNESS, p.KING_CROSS_VERTICAL_HEIGHT),
        Location((0.0, 0.0, p.KING_CROSS_ARM_CENTER_Z))
        * _box(p.KING_CROSS_ARM_WIDTH, p.KING_CROSS_THICKNESS, p.KING_CROSS_ARM_HEIGHT),
    )
    shape = _fuse_checked(
        shape,
        *_tower_side_code(side, p.KING_STONE_TERRACES, p.KING_STEEL_RIB_TIERS),
    )
    shape.label = f"{side}_king_neo_gothic_beacon"
    return shape


PIECE_BUILDERS = {
    "pawn": build_pawn,
    "rook": build_rook,
    "knight": build_knight,
    "bishop": build_bishop,
    "queen": build_queen,
    "king": build_king,
}


def build_piece(side: str, role: str):
    """Build one of the twelve canonical tactile piece variants."""

    if side not in p.SIDES:
        raise ValueError(f"unknown side: {side!r}")
    try:
        shape = PIECE_BUILDERS[role](side)
    except KeyError as exc:
        raise ValueError(f"unknown chess role: {role!r}") from exc
    assert len(shape.solids()) == 1
    assert abs(shape.bounding_box().min.Z) < 1e-7
    return shape


def build_board():
    """Build one base with 32 isolated light pads and a sloped street plan."""

    board = _box(p.BOARD_SIZE, p.BOARD_SIZE, p.BOARD_THICKNESS)
    pad = _ruled_rect_loft(
        p.LIGHT_PAD_LOWER_SIZE,
        p.LIGHT_PAD_LOWER_SIZE,
        p.LIGHT_PAD_LOWER_Z,
        p.LIGHT_PAD_TOP_SIZE,
        p.LIGHT_PAD_TOP_SIZE,
        p.BOARD_TOTAL_HEIGHT,
        hold_lower_until_z=p.BOARD_THICKNESS,
    )
    light_pads = []
    for file_index in range(p.FILES):
        for rank_index in range(p.RANKS):
            if p.is_light_square(file_index, rank_index):
                x, y = p.square_center(file_index, rank_index)
                light_pads.append(Location((x, y, 0.0)) * pad)
    assert len(light_pads) == 32
    board = _fuse_checked(board, *light_pads)

    groove_bottom_z = p.BOARD_THICKNESS - p.BORDER_STREET_GROOVE_DEPTH
    groove_through_z = p.BOARD_THICKNESS + p.BOOLEAN_OVERSHOOT
    file_street = _ruled_rect_loft(
        p.BORDER_STREET_GROOVE_BOTTOM_WIDTH,
        p.BORDER_STREET_GROOVE_BOTTOM_LENGTH,
        groove_bottom_z,
        p.BORDER_STREET_GROOVE_TOP_WIDTH,
        p.BORDER_STREET_GROOVE_TOP_LENGTH,
        p.BOARD_THICKNESS,
        groove_through_z,
    )
    rank_street = _ruled_rect_loft(
        p.BORDER_STREET_GROOVE_BOTTOM_LENGTH,
        p.BORDER_STREET_GROOVE_BOTTOM_WIDTH,
        groove_bottom_z,
        p.BORDER_STREET_GROOVE_TOP_LENGTH,
        p.BORDER_STREET_GROOVE_TOP_WIDTH,
        p.BOARD_THICKNESS,
        groove_through_z,
    )
    street_grooves = []
    for coordinate in p.INTERNAL_GRID_COORDINATES:
        for y in (-p.BORDER_STREET_GROOVE_CENTER, p.BORDER_STREET_GROOVE_CENTER):
            street_grooves.append(Location((coordinate, y, 0.0)) * file_street)

        for x in (-p.BORDER_STREET_GROOVE_CENTER, p.BORDER_STREET_GROOVE_CENTER):
            street_grooves.append(Location((x, coordinate, 0.0)) * rank_street)

    avenue = _ruled_rect_loft(
        p.AVENUE_GROOVE_BOTTOM_LENGTH,
        p.AVENUE_GROOVE_BOTTOM_WIDTH,
        p.BOARD_THICKNESS - p.AVENUE_GROOVE_DEPTH,
        p.AVENUE_GROOVE_TOP_LENGTH,
        p.AVENUE_GROOVE_TOP_WIDTH,
        p.BOARD_THICKNESS,
        groove_through_z,
    )
    avenue = Location(
        (p.AVENUE_GROOVE_CENTER_X, p.AVENUE_GROOVE_CENTER_Y, 0.0),
        (0.0, 0.0, p.AVENUE_ANGLE_DEG),
    ) * avenue
    board = _cut_checked(board, Compound(children=[*street_grooves, avenue]))
    board.label = "board_checker_pads_street_plan"
    assert len(board.solids()) == 1 and board.is_valid
    assert abs(board.bounding_box().min.Z) < 1e-7
    return board


def part_color(side: str) -> Color:
    rgb = p.STONE_RGB if side == "stone" else p.STEEL_RGB
    return Color(*rgb)


def board_color() -> Color:
    return Color(*p.BOARD_RGB)
