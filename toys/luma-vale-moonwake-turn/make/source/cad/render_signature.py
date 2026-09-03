"""Deterministic, exact orthographic silhouette sheet from the exported STL."""
from pathlib import Path
import struct

from PIL import Image, ImageDraw


STL = Path(__file__).with_name("moonwake.stl")
OUTPUT = Path(__file__).with_name("snap") / "signature.png"
SIZE = 900
BACKGROUND = (247, 240, 224)
OBJECT = (38, 113, 111)


def triangles(path):
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count:
        raise ValueError("signature renderer requires a binary STL")
    result = []
    for index in range(count):
        offset = 84 + index * 50 + 12
        result.append(struct.unpack_from("<9f", data, offset))
    return result


def panel(mesh, axes):
    coordinates = [
        (vertex[axes[0]], vertex[axes[1]])
        for triangle in mesh
        for vertex in zip(triangle[0::3], triangle[1::3], triangle[2::3])
    ]
    low_x = min(point[0] for point in coordinates)
    high_x = max(point[0] for point in coordinates)
    low_y = min(point[1] for point in coordinates)
    high_y = max(point[1] for point in coordinates)
    scale = SIZE * 0.72 / max(high_x - low_x, high_y - low_y)
    mid_x = (low_x + high_x) / 2
    mid_y = (low_y + high_y) / 2

    image = Image.new("RGB", (SIZE, SIZE), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for triangle in mesh:
        vertices = list(zip(triangle[0::3], triangle[1::3], triangle[2::3]))
        points = [
            (
                round((vertex[axes[0]] - mid_x) * scale + SIZE / 2),
                round(SIZE / 2 - (vertex[axes[1]] - mid_y) * scale),
            )
            for vertex in vertices
        ]
        draw.polygon(points, fill=OBJECT)
    return image


def main():
    mesh = triangles(STL)
    # First stable pose: sight along Y at the ship's XZ silhouette.
    ship = panel(mesh, (0, 2))
    # After a 90-degree roll onto the Y datum: sight along former Z.
    reveal = panel(mesh, (0, 1))
    sheet = Image.new("RGB", (SIZE * 2, SIZE), BACKGROUND)
    sheet.paste(ship, (0, 0))
    sheet.paste(reveal, (SIZE, 0))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, optimize=True)
    print(f"wrote {OUTPUT} ({sheet.width}x{sheet.height} RGB, {len(mesh)} triangles)")


if __name__ == "__main__":
    main()
