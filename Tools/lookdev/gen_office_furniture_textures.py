"""Generate the small procedural texture family used by the Office prop kit.

This keeps the furniture maps editable without pulling a film still or an
unlicensed texture into the project.  It uses only Python's standard library;
run from the Unity project root with ``python3
Tools/lookdev/gen_office_furniture_textures.py``.
"""

import math
import os
import random
import struct
import zlib


SIZE = 512
OUT = "Assets/Resources/Surfaces/Textures"


def write_png(path, pixels):
    raw = bytearray()
    for row in pixels:
        raw.append(0)
        for pixel in row:
            raw.extend(bytes(pixel))

    def chunk(kind, payload):
        return (struct.pack(">I", len(payload)) + kind + payload +
                struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as handle:
        handle.write(png)


def noise(x, y, seed):
    value = math.sin(x * 12.9898 + y * 78.233 + seed * 37.719) * 43758.5453
    return value - math.floor(value)


def normal(height, x, y):
    dx = (height(x + 1, y) - height(x - 1, y)) * 7.0
    dy = (height(x, y + 1) - height(x, y - 1)) * 7.0
    nx, ny, nz = -dx, -dy, 1.0
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    return (int(128 + 127 * nx / length), int(128 + 127 * ny / length),
            int(255 * nz / length), 255)


def build(name, seed):
    albedo, normals, masks = [], [], []
    for y in range(SIZE):
        albedo_row, normal_row, mask_row = [], [], []
        for x in range(SIZE):
            u, v = x / SIZE, y / SIZE
            random_value = noise(x // 3, y // 3, seed)
            if name == "OfficeFurniture_Wood":
                grain = .5 + .5 * math.sin((u * 42 + v * 4 + math.sin(v * 30) * .15) * math.pi)
                value = .80 + .14 * grain + .05 * (random_value - .5)
                color = (int(255 * value), int(215 * value), int(165 * value), 255)
                height = lambda xx, yy: .5 + .5 * math.sin(((xx / SIZE) * 42 + (yy / SIZE) * 4) * math.pi)
                smoothness, cavity = 128 + int(32 * grain), 220 - int(45 * random_value)
            elif name == "OfficeFurniture_Metal":
                scratch = .5 + .5 * math.sin((u * 170 + v * 13 + math.sin(v * 55) * .5) * math.pi)
                value = .66 + .08 * scratch + .04 * (random_value - .5)
                color = (int(255 * value), int(255 * value * .98), int(255 * value * .94), 255)
                height = lambda xx, yy: .5 + .5 * math.sin(((xx / SIZE) * 170 + (yy / SIZE) * 13) * math.pi)
                smoothness, cavity = 178 + int(36 * scratch), 235 - int(30 * random_value)
            else:
                weave = (math.sin(u * SIZE * .34) + math.sin(v * SIZE * .42)) * .025
                value = .76 + weave + .04 * (random_value - .5)
                color = (int(255 * value * .84), int(255 * value * .90), int(255 * value * .86), 255)
                height = lambda xx, yy: .5 + .5 * (math.sin((xx / SIZE) * SIZE * .34) + math.sin((yy / SIZE) * SIZE * .42)) * .05
                smoothness, cavity = 155 + int(22 * random_value), 210 - int(35 * random_value)
            albedo_row.append(color)
            normal_row.append(normal(height, x, y))
            mask_row.append((smoothness, cavity, 0, 255))
        albedo.append(albedo_row)
        normals.append(normal_row)
        masks.append(mask_row)

    for suffix, pixels in (("_A", albedo), ("_N", normals), ("_S", masks)):
        write_png(os.path.join(OUT, name + suffix + ".png"), pixels)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    random.seed(401)
    build("OfficeFurniture_Wood", 1)
    build("OfficeFurniture_Metal", 2)
    build("OfficeFurniture_Vinyl", 3)
