"""urchin_shell: a domed hexagonal carapace, 6 vertical sockets on an 11mm
radius (one per face, spine or pearl), topped by a grip knob whose 3/4/5/6
-flat prism is a player's whole identity for the game.
"""
import math

import cadquery as cq

import params as p


def _hex_pts(vertex_r: float):
    return p.polygon_pts(6, vertex_r)


def shell_socket_positions():
    """6 socket centres at SHELL_SOCKET_RADIUS, aligned to the hex's FACE
    normals (30deg offset from the vertex directions) -- this is what makes
    a seated socket 'point at' one neighbouring pan."""
    return [
        (p.SHELL_SOCKET_RADIUS * math.cos(math.radians(30 + i * 60)),
         p.SHELL_SOCKET_RADIUS * math.sin(math.radians(30 + i * 60)))
        for i in range(6)
    ]


def build_urchin_shell(n_flats: int) -> cq.Workplane:
    body = (
        cq.Workplane("XY").polyline(_hex_pts(p.SHELL_VERTEX_R)).close()
        .extrude(p.SHELL_DOME_H)
    )
    body = body.faces(">Z").chamfer(p.SHELL_TOP_CHAMFER)

    knob = (
        cq.Workplane("XY")
        .polyline(p.polygon_pts(
            n_flats,
            p.across_flats_to_vertex_r(p.SHELL_KNOB_ACROSS_FLATS, n_flats),
            rot_deg=p.face_forward_rot_deg(n_flats)))
        .close()
        .extrude(p.SHELL_KNOB_H)
    )
    # Round the knob's own vertical corner edges -- see SHELL_KNOB_EDGE_FILLET
    # for why (hand-safety per idea.json's art_direction, and it is what
    # actually breaks the "looks like a cone tip" illusion in the iso view).
    knob = knob.edges("|Z").fillet(p.SHELL_KNOB_EDGE_FILLET)
    knob = knob.translate((0, 0, p.SHELL_DOME_H))
    body = body.union(knob)

    # Sockets open at the dome crown (z=SHELL_DOME_H) and stop there -- they
    # never reach into the knob material above.
    socket = (
        cq.Workplane("XY").circle(p.SHELL_SOCKET_D / 2.0)
        .extrude(p.SHELL_SOCKET_DEPTH)
    )
    for (sx, sy) in shell_socket_positions():
        cutter = socket.translate(
            (sx, sy, p.SHELL_DOME_H - p.SHELL_SOCKET_DEPTH))
        body = body.cut(cutter)

    return body
