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
    Torus,
    extrude,
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


def _base_groove(z: float):
    return _zloc(z) * Torus(
        major_radius=p.BASE_GROOVE_MAJOR_RADIUS,
        minor_radius=p.BASE_GROOVE_MINOR_RADIUS,
    )


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
        pedestal = _cut_checked(pedestal, *(_base_groove(z) for z in p.STONE_GROOVE_Z))
    elif side == "steel":
        pedestal = _fuse_checked(pedestal, *_steel_vertical_fins())
        pedestal = _cut_checked(pedestal, *(_base_groove(z) for z in p.STEEL_GROOVE_Z))
    else:
        raise ValueError(f"unknown army side: {side!r}")
    pedestal.label = f"{side}_tactile_pedestal"
    return pedestal


def build_pawn(side: str):
    """Rooftop water tower: the smallest repeated Manhattan silhouette."""

    shape = build_pedestal(side)
    shape = _fuse_checked(
        shape,
        _zloc(p.PAWN_COLUMN_Z)
        * _cone(p.PAWN_COLUMN_RADIUS_BOTTOM, p.PAWN_COLUMN_RADIUS_TOP, p.PAWN_COLUMN_HEIGHT),
        _zloc(p.PAWN_TANK_Z) * _cylinder(p.PAWN_TANK_RADIUS, p.PAWN_TANK_HEIGHT),
        _zloc(p.PAWN_ROOF_Z)
        * _cone(p.PAWN_ROOF_RADIUS_BOTTOM, p.PAWN_ROOF_RADIUS_TOP, p.PAWN_ROOF_HEIGHT),
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
    with BuildSketch(Plane.XZ) as profile:
        Polygon(*p.KNIGHT_PROFILE)
    bridge_tower = extrude(profile.sketch, amount=p.KNIGHT_DEPTH / 2.0, both=True)
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
        _zloc(p.BISHOP_SPIRE_Z)
        * _cone(
            p.BISHOP_SPIRE_RADIUS_BOTTOM,
            p.BISHOP_SPIRE_RADIUS_TOP,
            p.BISHOP_SPIRE_HEIGHT,
        ),
    )
    shape = _fuse_checked(
        shape,
        *_tower_side_code(side, p.BISHOP_STONE_TERRACES, p.BISHOP_STEEL_RIB_TIERS),
    )
    slot = Location(
        (0.0, 0.0, p.BISHOP_SLOT_CENTER_Z),
        (0.0, p.BISHOP_SLOT_ANGLE_DEG, 0.0),
    ) * _box(p.BISHOP_SLOT_WIDTH, p.BISHOP_SLOT_DEPTH, p.BISHOP_SLOT_HEIGHT)
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
    """Build the seamless 8x8 board with dark squares recessed 0.35 mm."""

    board = _box(p.BOARD_SIZE, p.BOARD_SIZE, p.BOARD_TOTAL_HEIGHT)
    recesses = []
    for file_index in range(p.FILES):
        for rank_index in range(p.RANKS):
            if (file_index + rank_index) % 2 == 0:  # a1 is dark
                x, y = p.square_center(file_index, rank_index)
                recesses.append(
                    Location((x, y, p.BOARD_THICKNESS))
                    * _box(
                        p.SQUARE_PITCH - p.SQUARE_GRID_LAND,
                        p.SQUARE_PITCH - p.SQUARE_GRID_LAND,
                        p.SQUARE_RELIEF + p.BOOLEAN_OVERSHOOT,
                    )
                )

    avenue = Location(
        (0.0, p.AVENUE_GROOVE_CENTER_Y, p.BOARD_TOTAL_HEIGHT - p.AVENUE_GROOVE_DEPTH),
        (0.0, 0.0, p.AVENUE_GROOVE_ANGLE_DEG),
    ) * _box(
        p.AVENUE_GROOVE_LENGTH,
        p.AVENUE_GROOVE_WIDTH,
        p.AVENUE_GROOVE_DEPTH + p.BOOLEAN_OVERSHOOT,
    )
    cut_tool = Compound(children=[*recesses, avenue])
    board = _cut_checked(board, cut_tool)
    board.label = "board_manhattan_grid"
    assert abs(board.bounding_box().min.Z) < 1e-7
    return board


def part_color(side: str) -> Color:
    rgb = p.STONE_RGB if side == "stone" else p.STEEL_RGB
    return Color(*rgb)


def board_color() -> Color:
    return Color(*p.BOARD_RGB)
