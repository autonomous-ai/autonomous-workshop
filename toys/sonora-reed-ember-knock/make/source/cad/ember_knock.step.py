from build123d import Align, Axis, Box, Cylinder, Pos, Sphere


def centered_box(x, y, z, sx, sy, sz):
    return Pos(x, y, z) * Box(sx, sy, sz, align=(Align.CENTER, Align.CENTER, Align.CENTER))


def gen_step():
    # Coordinates: X crosses the edge (negative=inboard), Y follows it, Z is vertical in use.
    body = centered_box(-6, 0, 24, 70, 32, 6)                 # upper spine
    body += centered_box(29, 0, 29, 22, 24, 8)               # broad press cap
    throat = Cylinder(6, 32, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    body += throat.rotate(Axis.X, 90).translate((0, 0, 21))       # rounded rolling throat

    # Open lower jaw and two side cheeks form the edge saddle without a roof in print stance.
    body += centered_box(-22, 0, -2, 34, 32, 6)
    body += centered_box(-37, -12, 10, 7, 8, 30)
    body += centered_box(-37, 12, 10, 7, 8, 30)

    # Sole underside stop: Ø6 sphere embedded halfway into the lower jaw.
    body += Pos(-23, 0, 2) * Sphere(3)

    # Twin 12 x 8 mm top contacts, coplanar by construction.
    body += centered_box(-17, -10, 20, 12, 8, 3)
    body += centered_box(-17, 10, 20, 12, 8, 3)

    # Inboard globe and collar deliberately dominate volume to bias gravity return.
    body += centered_box(-22, 0, 29, 38, 26, 8)
    body += Pos(-22, 0, 36) * Sphere(16)

    # Open arched handle makes the camping-lantern identity legible.
    outer = Cylinder(20, 7, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    inner = Cylinder(14, 9, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    ring = outer.rotate(Axis.X, 90).translate((-22, 0, 35))
    ring -= inner.rotate(Axis.X, 90).translate((-22, 0, 35))
    ring &= centered_box(-22, 0, 45, 42, 10, 20)
    # Broad handle feet eliminate knife-edge tangencies and merge the arch into the globe collar.
    ring += centered_box(-39, 0, 42, 8, 10, 16)
    ring += centered_box(-5, 0, 42, 8, 10, 16)
    body += ring
    return body.translate((0, 0, 5))
