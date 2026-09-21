"""orbit_tray -- eight identical sockets, because every disc is identical.

An earlier draft graded the sockets to an orbital-radius ladder so the boxed
set would display the solar system in orbital order.  Uniform discs make that
impossible, and it is dropped rather than faked.  The tray is a tray.
"""

from __future__ import annotations

from build123d import Align, Box, Cylinder, Pos

import params as P


def build_orbit_tray():
    """One tray, printed flat, bed datum at Z = 0."""
    body = Box(
        P.TRAY_W, P.TRAY_D, P.TRAY_H,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    sockets = []
    for col in range(P.TRAY_COLS):
        for row in range(P.TRAY_ROWS):
            x = (col - (P.TRAY_COLS - 1) / 2.0) * P.TRAY_PITCH
            y = (row - (P.TRAY_ROWS - 1) / 2.0) * P.TRAY_PITCH
            sockets.append(
                Pos(x, y, P.TRAY_H - P.TRAY_SOCKET_DEPTH)
                * Cylinder(
                    radius=P.TRAY_SOCKET_D / 2.0,
                    height=P.TRAY_SOCKET_DEPTH + 1.0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN),
                )
            )
    body = body - sockets
    body.label = "orbit_tray"
    return body
