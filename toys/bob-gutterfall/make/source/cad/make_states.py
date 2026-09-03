"""Create non-printable evidence STLs: exact product pose plus a table witness."""
from pathlib import Path
import math
import struct

ROOT = Path(__file__).parent
SOURCE = ROOT / "gutterfall_final.stl"
OUT = ROOT / "review" / "states"
PIVOT = (-5.0, 0.0, 32.0)


def read_binary_stl(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    return [struct.unpack_from("<12fH", data, 84 + 50 * i) for i in range(count)]


def rotate_y(point, degrees):
    x, y, z = point
    x -= PIVOT[0]
    z -= PIVOT[2]
    a = math.radians(degrees)
    return (x * math.cos(a) + z * math.sin(a) + PIVOT[0], y,
            -x * math.sin(a) + z * math.cos(a) + PIVOT[2])


def transform_facets(facets, degrees):
    result = []
    for row in facets:
        n = rotate_y(row[0:3], degrees)
        n0 = rotate_y((0, 0, 0), degrees)
        normal = (n[0] - n0[0], n[1] - n0[1], n[2] - n0[2])
        vertices = [rotate_y(row[i:i + 3], degrees) for i in (3, 6, 9)]
        result.append((*normal, *vertices[0], *vertices[1], *vertices[2], 0))
    return result


def table_facets():
    # A neutral 4 mm tabletop coupon extending into the rear-opening throat.
    corners = [(-60, -48, 28), (0, -48, 28), (0, 48, 28), (-60, 48, 28),
               (-60, -48, 32), (0, -48, 32), (0, 48, 32), (-60, 48, 32)]
    faces = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7),
             (0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5),
             (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    rows = []
    for a, b, c in faces:
        va, vb, vc = corners[a], corners[b], corners[c]
        ux, uy, uz = (vb[i] - va[i] for i in range(3))
        vx, vy, vz = (vc[i] - va[i] for i in range(3))
        n = (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)
        rows.append((*n, *va, *vb, *vc, 0))
    return rows


def write_binary_stl(path, facets, name):
    header = name.encode("ascii")[:80].ljust(80, b" ")
    with path.open("wb") as f:
        f.write(header)
        f.write(struct.pack("<I", len(facets)))
        for row in facets:
            f.write(struct.pack("<12fH", *row))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = read_binary_stl(SOURCE)
    for label, angle in (("ready", 0.0), ("caught", 70.0)):
        facets = transform_facets(source, angle) + table_facets()
        write_binary_stl(OUT / f"{label}.stl", facets, f"Gutterfall {label} evidence")


if __name__ == "__main__":
    main()
