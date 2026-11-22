"""Convert one readable OMSI bus model to local SCS model source files."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import struct
from pathlib import Path

from settings import ROOT
from inspect_bus import model_cfg_for_bus, read_text
import inspect_e6m


def mesh_blocks(cfg: Path) -> list[dict]:
    lines = read_text(cfg).splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip().lower() == "[mesh]"]
    blocks = []
    for start, stop in zip(starts, starts[1:] + [len(lines)]):
        block_lines = lines[start + 1:stop]
        if not block_lines:
            continue
        name = block_lines[0].strip().strip('"')
        if not name.lower().endswith(".o3d"):
            continue
        conditions = []
        for index, line in enumerate(block_lines):
            if line.strip().lower() == "[visible]" and index + 2 < len(block_lines):
                conditions.append((block_lines[index + 1].strip(), block_lines[index + 2].strip()))
        numeric = [(key, float(value)) for key, value in conditions
                   if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value)]
        uncertain = len(numeric) != len(conditions)
        visible = not uncertain and all(value == (1.0 if key == "cp_lenkrad_visible" else 0.0)
                                        for key, value in numeric)
        blocks.append({"name": name, "text": "\n".join(block_lines),
                       "conditions": conditions, "visible": visible,
                       "visibility_uncertain": uncertain})
    return blocks


def bounds(meshes: list[dict]) -> list[list[float]]:
    points = [point for mesh in meshes for point in mesh["positions"]]
    return [[float(min(point[axis] for point in points)), float(max(point[axis] for point in points))]
            for axis in range(3)]


def center(mesh: dict) -> tuple[float, float, float]:
    return tuple(float((min(vertex[axis] for vertex in mesh["positions"])
                        + max(vertex[axis] for vertex in mesh["positions"])) / 2) for axis in range(3))


def axle_points(wheels: list[dict]) -> list[dict]:
    clusters: list[dict] = []
    for mesh in wheels:
        point = center(mesh)
        cluster = next((item for item in clusters if abs(item["z"] - point[2]) < 0.16), None)
        if cluster is None:
            cluster = {"z": point[2], "points": []}
            clusters.append(cluster)
        cluster["points"].append(point)
        cluster["z"] = sum(value[2] for value in cluster["points"]) / len(cluster["points"])
    clusters.sort(key=lambda item: item["z"])
    axles = []
    for cluster in clusters:
        sides = {}
        for point in cluster["points"]:
            side = "left" if point[0] < 0 else "right"
            sides.setdefault(side, []).append(point)
        if not sides.get("left") or not sides.get("right"):
            raise ValueError(f"Could not find both wheel sides near axle Z={cluster['z']:.3f}")
        axles.append({
            "z": cluster["z"],
            "left": tuple(sum(p[i] for p in sides["left"]) / len(sides["left"]) for i in range(3)),
            "right": tuple(sum(p[i] for p in sides["right"]) / len(sides["right"]) for i in range(3)),
        })
    if len(axles) not in (2, 3):
        raise ValueError(f"Only 2- and 3-axle buses are supported by this prototype; found {len(axles)}")
    return axles


def load_builder():
    path = Path(__file__).with_name("build_e6m.py")
    spec = importlib.util.spec_from_file_location("e6m_exporter", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load shared SCS geometry exporter: {path}")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.o3d = inspect_e6m.o3d
    return builder


def make_builder(bus_file: Path, cfg: Path, key: str):
    builder = load_builder()
    builder.BUS = bus_file.parent
    builder.MODEL_KEY = key
    builder.DEST = ROOT / "work/scs_source/vehicle/truck" / key
    builder.TEXT = builder.DEST / "textures"
    builder.REPORT = {"missing_textures": [], "materials": [], "meshes": [], "excluded": []}
    builder.MAT = []
    builder.MAT_MAP = {}
    builder.TEX_MAP = {}
    builder.MESHES = []
    cfg_blocks = mesh_blocks(cfg)

    def load(name: str):
        mesh_path = (cfg.parent / name.replace("\\", "/")).resolve()
        blob = mesh_path.read_bytes()
        if len(blob) < 8 or blob[:2] != b"\x84\x19":
            raise ValueError(f"Unsupported O3D header: {mesh_path}")
        if blob[2] > 3 and struct.unpack_from("<I", blob, 4)[0] != 0xffffffff:
            raise ValueError(f"Encrypted mesh; author source required: {mesh_path}")
        result = builder.o3d.import_o3d(blob)
        if not result[1] or not result[2] or result[-1]:
            raise ValueError(f"Invalid or encrypted mesh: {mesh_path}")
        return result

    builder.mesh_blocks = lambda: cfg_blocks
    builder.load = load
    return builder


def export(bus_file: Path, key: str) -> dict:
    cfg = model_cfg_for_bus(bus_file)
    builder = make_builder(bus_file, cfg, key)
    builder.TEXT.mkdir(parents=True, exist_ok=True)
    builder.read_meshes()
    wheels = [mesh for mesh in builder.MESHES if mesh["wheel"]]
    body = [mesh for mesh in builder.MESHES if not mesh["wheel"]]
    if not body or not wheels:
        raise ValueError("Model must contain visible body meshes and separately named whl*.o3d meshes")
    axles = axle_points(wheels)
    body_bounds = bounds(body)
    collision_body = [mesh for mesh in body
                      if not re.search(r"mirror|spiegel|shadow", mesh["name"], re.IGNORECASE)] or body
    collision_bounds = bounds(collision_body)
    steering = next((mesh for mesh in builder.MESHES if "strw" in mesh["name"].lower()), None)
    if steering is None:
        raise ValueError("No steering-wheel mesh found; cabin locator needs manual setup")
    wheel_center = center(steering)
    eye = (wheel_center[0], wheel_center[1] + 0.45, wheel_center[2])
    x_extent = max(abs(body_bounds[0][0]), abs(body_bounds[0][1]))
    front_z, rear_z = body_bounds[2][0], body_bounds[2][1]
    bottom, top = body_bounds[1]
    locators = [
        {"name": "cabin", "pos": (0, 0, 0), "part": "chs", "rot": (1, 0, 0, 0)},
        {"name": "interior", "pos": eye, "part": "cab", "rot": (1, 0, 0, 0)},
        {"name": "interior_uk", "pos": eye, "part": "cab", "rot": (1, 0, 0, 0)},
        {"name": "cam_cabin", "pos": (0, top + 0.3, front_z + 0.4), "part": "cab", "rot": (1, 0, 0, 0)},
        {"name": "cam_cabin2", "pos": (0, top + 0.3, rear_z - 0.4), "part": "cab", "rot": (1, 0, 0, 0)},
        {"name": "hook_t", "pos": (0, bottom + 0.8, rear_z - 0.3), "part": "chs", "rot": (1, 0, 0, 0)},
    ]
    if len(axles) == 2:
        group_indices = {"a": (0,), "b": (1,)}
    else:
        group_indices = {"a": (0, 2), "b": (1,)}
    for group, indices in group_indices.items():
        for group_axle, axle_index in enumerate(indices):
            axle = axles[axle_index]
            for side_index, side in enumerate(("left", "right")):
                position = axle[side]
                wheel_index = group_axle * 2 + side_index
                locators.append({"name": f"wheel_{group}_{wheel_index}", "pos": position,
                                 "part": "chs", "rot": (1, 0, 0, 0)})
    for side, x in enumerate((-x_extent * 0.7, x_extent * 0.7)):
        for stem, hook in (("lh", "headl"), ("lhi", "high_beam"), ("lp", "parkl")):
            locators.append({"name": f"{stem}_{side}", "pos": (x, bottom + 0.85, front_z),
                             "part": "cab", "rot": (1, 0, 0, 0), "hookup": f"flare.vehicle.{hook}"})
        for stem, hook in (("lr", "rearl"), ("lb", "brakel"), ("lv", "reversel")):
            locators.append({"name": f"{stem}_{side}", "pos": (x, bottom + 0.8, rear_z),
                             "part": "cab", "rot": (0, 0, 1, 0), "hookup": f"flare.vehicle.{hook}"})
    builder.write_model("coach", body, locators=locators,
                        variants={"chs_6x2": {"cab": 0, "chs": 1}, "bus_cab": {"cab": 1, "chs": 0}})
    builder.write_model("interior", body, part="base", offset=eye)
    collision_width = collision_bounds[0][1] - collision_bounds[0][0]
    collision_bottom, collision_top = collision_bounds[1]
    collision_height = collision_top - collision_bottom
    collision_length = collision_bounds[2][1] - collision_bounds[2][0]
    collision_center_z = -(collision_bounds[2][0] + collision_bounds[2][1]) / 2
    collision = (builder.header("Collision", "coach", 2)
                 + "Global {\n VertexCount: 0\n TriangleCount: 0\n MaterialCount: 0\n PieceCount: 0\n PartCount: 2\n LocatorCount: 1\n}\n"
                 + "Part {\n Name: \"cab\"\n PieceCount: 0\n LocatorCount: 0\n Pieces:\n Locators:\n}\n"
                 + "Part {\n Name: \"chs\"\n PieceCount: 0\n LocatorCount: 1\n Pieces:\n Locators: 0\n}\n"
                 + f"Locator {{\n Name: \"collision\"\n Index: 0\n Position: {builder.vec((0, collision_bottom + collision_height / 2, collision_center_z))}\n"
                 + f"Rotation: {builder.vec((1, 0, 0, 0))}\n Alias: \"\"\n Weight: 1\n Type: \"Box\"\n Parameters: {builder.vec((collision_width, collision_height, collision_length, 0))}\n}}\n")
    (builder.DEST / "coach.pic").write_text(collision, encoding="utf-8")
    builder.REPORT["materials"] = [{key: value for key, value in material.items() if key != "texture"}
                                    for material in builder.MAT]
    report = {
        "source_bus": str(bus_file),
        "model_config": str(cfg),
        "target_model_key": key,
        "output_dir": str(builder.DEST),
        "mesh_count": len(builder.MESHES),
        "body_mesh_count": len(body),
        "wheel_mesh_count": len(wheels),
        "axle_count": len(axles),
        "axle_centres_scs": axles,
        "body_bounds_scs": body_bounds,
        "collision_bounds_scs": collision_bounds,
        "dimensions_metres_xyz": [collision_width, collision_height, collision_length],
        "estimated_cabin_eye_scs": eye,
        "model_files": [str(builder.DEST / f"{name}.pim") for name in ("coach", "interior")]
                       + [str(builder.DEST / "coach.pic")],
        "missing_textures": sorted(set(builder.REPORT["missing_textures"])),
        "excluded_meshes": builder.REPORT["excluded"],
        "limitations": [
            "This generates SCS intermediate geometry only; it does not create an ETS2 vehicle definition or package.",
            "Wheel positions are measured from OMSI wheel meshes; lighting and camera locators are estimates.",
            "OMSI scripts, animation, doors, passenger paths, signs, and drivetrain behavior are not ported.",
            "The source assets remain local and are not added to Git.",
        ],
    }
    report_path = ROOT / "work/bus_models" / f"{key}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("axle_centres_scs", "excluded_meshes")}, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bus_config", type=Path, help="Installed OMSI .bus file")
    parser.add_argument("--key", help="SCS model directory key; defaults to a stable package slug")
    args = parser.parse_args()
    bus_file = args.bus_config.resolve()
    if not bus_file.is_file():
        raise SystemExit(f"Bus config not found: {bus_file}")
    slug = re.sub(r"[^a-z0-9_]+", "_", bus_file.parent.name.lower()).strip("_")[:32]
    digest = hashlib.sha1(str(bus_file.parent).lower().encode("utf-8")).hexdigest()[:6]
    key = args.key or f"{slug}_{digest}"
    export(bus_file, key)


if __name__ == "__main__":
    main()
