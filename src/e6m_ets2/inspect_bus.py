"""Audit one installed OMSI bus model before converting it to ETS2."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

from settings import ROOT

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def model_cfg_for_bus(bus_file: Path) -> Path:
    lines = read_text(bus_file).splitlines()
    for index, line in enumerate(lines):
        if line.strip().lower() == "[model]" and index + 1 < len(lines):
            return (bus_file.parent / lines[index + 1].strip().replace("\\", "/")).resolve()
    raise ValueError(f"No [model] section in {bus_file}")


def mesh_blocks(cfg: Path) -> list[dict]:
    text = read_text(cfg)
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().lower() == "[mesh]"]
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
        # OMSI config variables are runtime-dependent. This mirrors the E6M
        # converter's default model rule and reports the rule for review.
        numeric_conditions = [(key, float(value)) for key, value in conditions
                              if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value)]
        uncertain = len(numeric_conditions) != len(conditions)
        visible = not uncertain and all(value == (1.0 if key == "cp_lenkrad_visible" else 0.0)
                                        for key, value in numeric_conditions)
        blocks.append({"name": name, "conditions": conditions, "visible": visible,
                       "visibility_uncertain": uncertain})
    return blocks


def load_importer(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"OMSI O3D importer not found: {path}")
    spec = importlib.util.spec_from_file_location("o3dconvert", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load OMSI O3D importer: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inspect(bus_file: Path, importer, output: Path) -> dict:
    cfg = model_cfg_for_bus(bus_file)
    blocks = mesh_blocks(cfg)
    meshes = []
    missing_meshes = []
    missing_textures = set()
    for block in blocks:
        mesh_path = (cfg.parent / block["name"].replace("\\", "/")).resolve()
        if not mesh_path.is_file():
            missing_meshes.append(str(mesh_path))
            continue
        blob = mesh_path.read_bytes()
        try:
            data = importer.import_o3d(blob)
            positions = [vertex[0] for vertex in data[1]]
            encrypted = bool(data[-1])
            supported_header = data[0][0:2] == (0x84, 0x19)
            invalid_triangles = sum(
                len(triangle[0]) != 3
                or any(index < 0 or index >= len(positions) for index in triangle[0])
                or triangle[1] < 0 or triangle[1] >= len(data[3])
                for triangle in data[2]
            )
            valid = bool(positions) and bool(data[2]) and not encrypted and supported_header and not invalid_triangles
            bounds = None
            if positions:
                bounds = [[min(point[axis] for point in positions), max(point[axis] for point in positions)]
                          for axis in range(3)]
            textures = sorted({str(material[-1]) for material in data[3] if material and material[-1]})
            for texture in textures:
                texture_path = bus_file.parent / "texture" / texture
                alternatives = [texture_path, texture_path.with_suffix(".tga"), texture_path.with_suffix(".dds")]
                alternatives.extend([
                    cfg.parent / "texture" / texture,
                    cfg.parent / "texture" / Path(texture).with_suffix(".tga"),
                    cfg.parent / "texture" / Path(texture).with_suffix(".dds"),
                ])
                if not any(candidate.is_file() for candidate in alternatives):
                    missing_textures.add(texture)
            meshes.append({
                "name": block["name"],
                "path": str(mesh_path),
                "visible_by_default_rule": block["visible"],
                "visibility_conditions": block["conditions"],
                "visibility_uncertain": block["visibility_uncertain"],
                "valid_for_export": valid,
                "encrypted": encrypted,
                "supported_header": supported_header,
                "invalid_triangle_count": invalid_triangles,
                "vertices": len(positions),
                "triangles": len(data[2]),
                "bounds_omsi": bounds,
                "textures": textures,
                "error": None,
            })
        except Exception as error:
            meshes.append({
                "name": block["name"],
                "path": str(mesh_path),
                "visible_by_default_rule": block["visible"],
                "visibility_conditions": block["conditions"],
                "visibility_uncertain": block["visibility_uncertain"],
                "valid_for_export": False,
                "encrypted": None,
                "supported_header": False,
                "invalid_triangle_count": None,
                "vertices": 0,
                "triangles": 0,
                "bounds_omsi": None,
                "textures": [],
                "error": f"{type(error).__name__}: {error}",
            })
    visible_bounds = [mesh["bounds_omsi"] for mesh in meshes
                      if mesh["visible_by_default_rule"] and mesh["valid_for_export"] and mesh["bounds_omsi"]]
    overall_bounds = None
    if visible_bounds:
        overall_bounds = [[min(bounds[axis][0] for bounds in visible_bounds),
                           max(bounds[axis][1] for bounds in visible_bounds)]
                          for axis in range(3)]
    dimensions = None if overall_bounds is None else [high - low for low, high in overall_bounds]
    report = {
        "bus_config": str(bus_file),
        "model_config": str(cfg),
        "target": "ETS2 Coach Mode (static audit only)",
        "mesh_count": len(meshes),
        "default_visible_mesh_count": sum(mesh["visible_by_default_rule"] for mesh in meshes),
        "exportable_mesh_count": sum(mesh["valid_for_export"] for mesh in meshes),
        "encrypted_mesh_count": sum(mesh["encrypted"] is True for mesh in meshes),
        "failed_mesh_count": sum(mesh["error"] is not None for mesh in meshes),
        "visibility_uncertain_mesh_count": sum(mesh["visibility_uncertain"] for mesh in meshes),
        "overall_visible_bounds_omsi": overall_bounds,
        "overall_dimensions_metres_xyz": dimensions,
        "missing_meshes": sorted(missing_meshes),
        "missing_textures": sorted(missing_textures),
        "default_visibility_rule": "mesh is visible when every numeric [visible] value is 0, except cp_lenkrad_visible which is 1; dynamic conditions need manual review",
        "meshes": meshes,
        "limitations": [
            "This is an offline geometry audit, not an ETS2 conversion or runtime test.",
            "OMSI scripts, doors, destination signs, sounds, passenger paths, and drivetrain behavior are not converted.",
            "Mesh visibility is approximated from the E6M converter rule; dynamic conditions are flagged for review.",
            "The original asset author must permit any redistribution; source assets are never copied by this tool.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    summary = {key: value for key, value in report.items() if key != "meshes"}
    print(json.dumps(summary, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bus_config", type=Path, help="Installed OMSI .bus file to inspect")
    parser.add_argument("--importer", type=Path,
                        default=ROOT / "work/vendor/Blender-O3D-IO-Public/o3d_io/o3dconvert.py",
                        help="Local O3D importer script")
    parser.add_argument("--output", type=Path, help="JSON report path (defaults to local work/e6m_ets2)")
    args = parser.parse_args()
    bus_file = args.bus_config.resolve()
    if not bus_file.is_file():
        raise SystemExit(f"Bus config not found: {bus_file}")
    output = args.output or (ROOT / "work/bus_audits" / f"{bus_file.parent.name}_{bus_file.stem}.json")
    try:
        importer = load_importer(args.importer)
        inspect(bus_file, importer, output)
    except (OSError, ValueError, ImportError) as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
