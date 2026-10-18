#!/usr/bin/env python3
"""
Prepares the Blåhaj STL geometry for the OpenFOAM wind tunnel simulation:
1. Verifies STL bounding box dimensions and location.
2. If raw/unscaled (e.g. from 3D printing STL ~160mm along Y, outside wind tunnel),
   backs up raw STL to blahaj.stl.orig, scales to 1.0m length, rotates -90 deg
   around Z so snout faces oncoming wind (-X), and centers within the wind tunnel
   refinement box at (1.5, 0.0, 0.3).
"""

import os
import struct
import math
import sys

STL_PATH = "constant/triSurface/blahaj.stl"
BACKUP_PATH = "constant/triSurface/blahaj.stl.orig"

def inspect_stl(path):
    with open(path, "rb") as f:
        header = f.read(80)
        count_bytes = f.read(4)
        if len(count_bytes) < 4:
            return None, None, None
        count = struct.unpack("<I", count_bytes)[0]
        min_b = [float("inf")] * 3
        max_b = [-float("inf")] * 3
        for _ in range(count):
            data = f.read(50)
            if len(data) < 50:
                break
            for i in range(12, 48, 12):
                v = struct.unpack("<3f", data[i : i + 12])
                for j in range(3):
                    min_b[j] = min(min_b[j], v[j])
                    max_b[j] = max(max_b[j], v[j])
        return count, min_b, max_b

def is_already_scaled_and_placed(min_b, max_b):
    return (
        0.5 <= min_b[0] <= 1.5 and
        1.5 <= max_b[0] <= 2.5 and
        -0.5 <= min_b[1] <= 0.0 and
        0.0 <= max_b[1] <= 0.5 and
        0.1 <= min_b[2] <= 0.5 and
        0.5 <= max_b[2] <= 1.2
    )

def transform_stl(in_path, out_path):
    with open(in_path, "rb") as f_in:
        header = f_in.read(80)
        count = struct.unpack("<I", f_in.read(4))[0]
        
        # Read all vertices to determine original bounds
        triangles = []
        min_orig = [float("inf")] * 3
        max_orig = [-float("inf")] * 3
        for _ in range(count):
            data = f_in.read(50)
            v1 = struct.unpack("<3f", data[12:24])
            v2 = struct.unpack("<3f", data[24:36])
            v3 = struct.unpack("<3f", data[36:48])
            attr = data[48:50]
            for v in (v1, v2, v3):
                for j in range(3):
                    min_orig[j] = min(min_orig[j], v[j])
                    max_orig[j] = max(max_orig[j], v[j])
            triangles.append((v1, v2, v3, attr))

    # Length along Y
    orig_length = max_orig[1] - min_orig[1]
    scale = 1.0 / orig_length if orig_length > 0 else 0.00625
    center_x = (min_orig[0] + max_orig[0]) / 2.0
    center_y = (min_orig[1] + max_orig[1]) / 2.0
    min_z = min_orig[2]

    with open(out_path, "wb") as f_out:
        title = b"Transformed Blahaj for OpenFOAM wind tunnel simulation"
        f_out.write(title + b" " * (80 - len(title)))
        f_out.write(struct.pack("<I", count))

        for v1, v2, v3, attr in triangles:
            def tf(v):
                x_rel = v[0] - center_x
                y_rel = v[1] - center_y
                z_rel = v[2] - min_z
                # -90 deg rotation around Z: (x, y) -> (y, -x)
                x_new = 1.5 + y_rel * scale
                y_new = 0.0 - x_rel * scale
                z_new = 0.3 + z_rel * scale
                return (x_new, y_new, z_new)

            tv1, tv2, tv3 = tf(v1), tf(v2), tf(v3)
            # Normal calculation
            ax, ay, az = tv2[0] - tv1[0], tv2[1] - tv1[1], tv2[2] - tv1[2]
            bx, by, bz = tv3[0] - tv1[0], tv3[1] - tv1[1], tv3[2] - tv1[2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            mag = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            norm = (nx / mag, ny / mag, nz / mag)

            f_out.write(struct.pack("<3f", *norm))
            f_out.write(struct.pack("<3f", *tv1))
            f_out.write(struct.pack("<3f", *tv2))
            f_out.write(struct.pack("<3f", *tv3))
            f_out.write(attr)

def main():
    if not os.path.isfile(STL_PATH):
        if os.path.isfile(BACKUP_PATH):
            print(f"Restoring {STL_PATH} from {BACKUP_PATH}...")
            transform_stl(BACKUP_PATH, STL_PATH)
        else:
            print(f"Error: {STL_PATH} not found!", file=sys.stderr)
            sys.exit(1)

    count, min_b, max_b = inspect_stl(STL_PATH)
    if count is None:
        print(f"Error: unable to parse {STL_PATH}", file=sys.stderr)
        sys.exit(1)

    if is_already_scaled_and_placed(min_b, max_b):
        print(f"--> Geometry already properly placed: bounds [{min_b[0]:.2f}, {min_b[1]:.2f}, {min_b[2]:.2f}] to [{max_b[0]:.2f}, {max_b[1]:.2f}, {max_b[2]:.2f}]")
    else:
        print(f"--> Geometry outside domain (bounds [{min_b[0]:.2f}, {min_b[1]:.2f}, {min_b[2]:.2f}] to [{max_b[0]:.2f}, {max_b[1]:.2f}, {max_b[2]:.2f}]).")
        if not os.path.isfile(BACKUP_PATH):
            import shutil
            shutil.copy2(STL_PATH, BACKUP_PATH)
            print(f"--> Backed up original to {BACKUP_PATH}")
        transform_stl(BACKUP_PATH, STL_PATH)
        _, new_min, new_max = inspect_stl(STL_PATH)
        print(f"--> Transformed geometry: new bounds [{new_min[0]:.2f}, {new_min[1]:.2f}, {new_min[2]:.2f}] to [{new_max[0]:.2f}, {new_max[1]:.2f}, {new_max[2]:.2f}]")

if __name__ == "__main__":
    main()
