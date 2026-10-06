"""GLB (binary glTF 2.0) export. Small dependency-free writer: boxes grouped by material, one node per floor."""
from __future__ import annotations

import json
import struct
from typing import Dict, List, Tuple

import numpy as np

from ..geometry import analyze
from ..geometry.slabs import slab_cells

SLAB_T = 0.2
MATERIALS = {
    "wall": ([0.93, 0.92, 0.89, 1.0], "OPAQUE"),
    "slab": ([0.70, 0.70, 0.68, 1.0], "OPAQUE"),
    "stair": ([0.55, 0.45, 0.35, 1.0], "OPAQUE"),
    "door": ([0.45, 0.30, 0.18, 1.0], "OPAQUE"),
    "glass": ([0.55, 0.78, 0.92, 0.35], "BLEND"),
}
_FACES = [  # normal, 4 corner offsets (indices into min/max selectors)
    ((1, 0, 0), [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]),
    ((-1, 0, 0), [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)]),
    ((0, 1, 0), [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)]),
    ((0, -1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
    ((0, 0, 1), [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]),
    ((0, 0, -1), [(0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)]),
]


class _Mesh:
    def __init__(self):
        self.pos: List[Tuple[float, float, float]] = []
        self.nor: List[Tuple[float, float, float]] = []
        self.idx: List[int] = []

    def box(self, x0, y0, z0, x1, y1, z1):
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
            return
        lo, hi = (x0, y0, z0), (x1, y1, z1)
        for n, corners in _FACES:
            base = len(self.pos)
            for c in corners:
                p = tuple(hi[i] if c[i] else lo[i] for i in range(3))
                # plan (x east, y north, z up) -> glTF (x, z, -y)
                self.pos.append((p[0], p[2], -p[1]))
                self.nor.append((n[0], n[2], -n[1]))
            self.idx += [base, base + 1, base + 2, base, base + 2, base + 3]


def _wall_boxes(mesh: _Mesh, w, openings, z_base, height):
    """Box decomposition of a wall piece around its openings."""
    ax = w.axis
    a_lo, a_hi = (w.x0, w.x1) if ax == "x" else (w.y0, w.y1)
    cross = (w.y0, w.y1) if ax == "x" else (w.x0, w.x1)

    def emit(a0, a1, z0, z1):
        if a1 - a0 < 1e-6 or z1 - z0 < 1e-6:
            return
        if ax == "x":
            mesh.box(a0, cross[0], z_base + z0, a1, cross[1], z_base + z1)
        else:
            mesh.box(cross[0], a0, z_base + z0, cross[1], a1, z_base + z1)

    ops = sorted([o for o in openings if o.wall_id == w.id and not o.problems and o.rect], key=lambda o: o.a0)
    cur = a_lo
    for o in ops:
        o0, o1 = max(o.a0, cur), min(o.a1, a_hi)
        if o1 <= o0:
            continue
        emit(cur, o0, 0, height)
        emit(o0, o1, 0, o.z0)           # below (windows)
        emit(o0, o1, o.z1, height)      # lintel
        cur = o1
    emit(cur, a_hi, 0, height)


def build_meshes(model) -> Dict[str, Dict[str, _Mesh]]:
    """{floor_id: {material: mesh}} in plan coordinates."""
    an = analyze(model)
    out: Dict[str, Dict[str, _Mesh]] = {}
    for fg in an.floors:
        fl = fg.floor
        meshes = {k: _Mesh() for k in MATERIALS}
        z = fl.elevation
        for (x0, y0, x1, y1) in slab_cells(fg.slab):
            meshes["slab"].box(x0, y0, z - SLAB_T, x1, y1, z)
        for w in fg.walls:
            _wall_boxes(meshes["wall"], w, fg.openings, z, fl.height)
        for op in fg.openings:
            if op.problems or op.rect is None:
                continue
            x0, y0, x1, y1 = op.rect
            if op.kind == "window":
                if op.axis == "x":
                    c = (y0 + y1) / 2
                    meshes["glass"].box(x0, c - 0.01, z + op.z0, x1, c + 0.01, z + op.z1)
                else:
                    c = (x0 + x1) / 2
                    meshes["glass"].box(c - 0.01, y0, z + op.z0, c + 0.01, y1, z + op.z1)
            elif not op.leafless:
                # closed-position door leaf, thin, inside the opening
                if op.axis == "x":
                    c = (y0 + y1) / 2
                    meshes["door"].box(x0 + 0.02, c - 0.02, z, x1 - 0.02, c + 0.02, z + op.z1 - 0.02)
                else:
                    c = (x0 + x1) / 2
                    meshes["door"].box(c - 0.02, y0 + 0.02, z, c + 0.02, y1 - 0.02, z + op.z1 - 0.02)
        for geo in fg.stairs.values():
            for (x0, y0, z0, x1, y1, z1) in (geo.boxes or []):
                meshes["stair"].box(x0, y0, z + z0, x1, y1, z + z1)
        out[fl.id] = meshes
    return out


def export_glb(model, path: str) -> str:
    an = analyze(model)
    per_floor = build_meshes(model)
    blob = bytearray()
    views, accessors, meshes_json, materials, nodes = [], [], [], [], []
    mat_index = {}
    for name, (rgba, mode) in MATERIALS.items():
        mat_index[name] = len(materials)
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": rgba, "metallicFactor": 0.0, "roughnessFactor": 0.9},
             "alphaMode": mode, "doubleSided": True}
        materials.append(m)

    def add_array(arr: np.ndarray, target: int, ctype: int, typ: str, with_minmax=False):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(arr.tobytes())
        views.append({"buffer": 0, "byteOffset": off, "byteLength": arr.nbytes, "target": target})
        acc = {"bufferView": len(views) - 1, "componentType": ctype, "count": int(arr.shape[0]), "type": typ}
        if with_minmax:
            acc["min"] = arr.min(axis=0).tolist()
            acc["max"] = arr.max(axis=0).tolist()
        accessors.append(acc)
        return len(accessors) - 1

    floor_nodes = []
    for fg in an.floors:
        fl = fg.floor
        children = []
        for mname, mesh in per_floor[fl.id].items():
            if not mesh.idx:
                continue
            p = add_array(np.array(mesh.pos, dtype=np.float32), 34962, 5126, "VEC3", True)
            n = add_array(np.array(mesh.nor, dtype=np.float32), 34962, 5126, "VEC3")
            i = add_array(np.array(mesh.idx, dtype=np.uint32), 34963, 5125, "SCALAR")
            meshes_json.append({"name": f"{fl.id}-{mname}", "primitives": [
                {"attributes": {"POSITION": p, "NORMAL": n}, "indices": i, "material": mat_index[mname]}]})
            nodes.append({"name": f"{fl.id}-{mname}", "mesh": len(meshes_json) - 1})
            children.append(len(nodes) - 1)
        nodes.append({"name": f"floor-{fl.id}", "children": children,
                      "extras": {"floor_id": fl.id, "floor_name": fl.name, "elevation": fl.elevation, "height": fl.height}})
        floor_nodes.append(len(nodes) - 1)
    if not floor_nodes:
        raise ValueError("nothing to export: building has no floors")
    nodes.append({"name": "building", "children": floor_nodes,
                  "extras": {"site_width": an.building.width, "site_depth": an.building.depth}})
    root = len(nodes) - 1
    gltf = {"asset": {"version": "2.0", "generator": "archagent"}, "scene": 0, "scenes": [{"nodes": [root]}],
            "nodes": nodes, "meshes": meshes_json, "materials": materials, "accessors": accessors,
            "bufferViews": views, "buffers": [{"byteLength": len(blob)}]}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    blob.extend(b"\0" * (-len(blob) % 4))
    total = 12 + 8 + len(js) + 8 + len(blob)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(blob), 0x004E4942) + bytes(blob))
    return path
