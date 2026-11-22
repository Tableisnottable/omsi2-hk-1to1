"""Inventory installed OMSI bus packages without copying game assets."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

DEFAULT_ROOT = Path(r"A:\SteamLibrary\steamapps\common\OMSI 2\Vehicles")
DEFAULT_OUTPUT = Path(__file__).resolve().parents[2] / "work/e6m_ets2/bus_inventory.json"
AI_MARKERS = ("ai_", "_ai", "traffic", "fahrzeug_ai")
NON_BUS_MARKERS = ("daf_xf_105",)
MODEL_SECTION = re.compile(r"^\s*\[model\]\s*$", re.IGNORECASE | re.MULTILINE)
MESH_SECTION = re.compile(r"^\s*\[mesh\]\s*$", re.IGNORECASE | re.MULTILINE)


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def section_values(text: str, marker: re.Pattern[str], value_count: int = 1) -> list[list[str]]:
    lines = text.splitlines()
    blocks: list[list[str]] = []
    for index, line in enumerate(lines):
        if marker.fullmatch(line):
            values = [candidate.strip().strip('"') for candidate in lines[index + 1:index + 1 + value_count]]
            blocks.append(values)
    return blocks


def resolve_reference(base: Path, value: str) -> Path:
    return (base / value.replace("\\", "/")).resolve()


def inspect_package(package: Path, vehicles_root: Path) -> dict:
    bus_files = sorted(package.glob("*.bus"))
    variants = []
    package_models: set[str] = set()
    missing_model_cfgs: set[str] = set()
    missing_meshes: set[str] = set()
    referenced_meshes: set[str] = set()
    external_meshes: set[str] = set()

    for bus_file in bus_files:
        bus_text = read_text(bus_file)
        model_sections = section_values(bus_text, MODEL_SECTION)
        model_values = [values[0] for values in model_sections if values and values[0]]
        model_cfgs = []
        for value in model_values:
            cfg = resolve_reference(package, value)
            model_cfgs.append(str(cfg.relative_to(vehicles_root)) if cfg.is_relative_to(vehicles_root) else str(cfg))
            package_models.add(str(cfg))
            if not cfg.is_file():
                missing_model_cfgs.add(str(cfg))
                continue
            cfg_text = read_text(cfg)
            for mesh_values in section_values(cfg_text, MESH_SECTION):
                if not mesh_values or not mesh_values[0] or mesh_values[0].startswith("["):
                    continue
                mesh = resolve_reference(cfg.parent, mesh_values[0])
                referenced_meshes.add(str(mesh))
                if not mesh.is_file():
                    missing_meshes.add(str(mesh))
                if not mesh.is_relative_to(package):
                    external_meshes.add(str(mesh))
        variants.append({
            "config": bus_file.name,
            "model_cfgs": model_cfgs,
            "has_model_reference": bool(model_values),
        })

    marker_text = (package.name + " " + " ".join(v["config"] for v in variants)).lower()
    ai_like = any(marker in marker_text for marker in AI_MARKERS)
    non_bus = any(marker in marker_text for marker in NON_BUS_MARKERS)
    model_dir = package / "model"
    o3d_files = list(model_dir.rglob("*.o3d")) if model_dir.is_dir() else []
    model_cfg_files = list(model_dir.rglob("*.cfg")) if model_dir.is_dir() else []
    return {
        "package": package.name,
        "classification": "ai_or_traffic" if ai_like else (
            "non_bus_vehicle" if non_bus else ("drivable_candidate" if bus_files else "model_only")
        ),
        "bus_config_count": len(bus_files),
        "model_cfg_count": len(package_models),
        "model_cfg_files_in_model_dir": len(model_cfg_files),
        "o3d_files_in_model_dir": len(o3d_files),
        "referenced_mesh_count": len(referenced_meshes),
        "missing_model_cfgs": sorted(missing_model_cfgs),
        "missing_meshes": sorted(missing_meshes),
        "external_mesh_references": sorted(external_meshes),
        "variants": variants,
    }


def inventory(root: Path) -> dict:
    packages = [inspect_package(path, root) for path in sorted(root.iterdir()) if path.is_dir()]
    counts = Counter(item["classification"] for item in packages)
    drivable = [item for item in packages if item["classification"] == "drivable_candidate"]
    drivable.sort(key=lambda item: (-item["o3d_files_in_model_dir"], item["package"].casefold()))
    return {
        "vehicles_root": str(root),
        "package_count": len(packages),
        "classification_counts": dict(sorted(counts.items())),
        "drivable_candidates": drivable,
        "all_packages": packages,
        "scope_note": "Candidate status is based on root-level .bus configs. Runtime usability, O3D encryption, licensing, and ETS2 conversion compatibility still require review.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vehicles", type=Path, default=DEFAULT_ROOT, help="OMSI 2 Vehicles folder")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Local JSON report path")
    args = parser.parse_args()
    root = args.vehicles.resolve()
    if not root.is_dir():
        raise SystemExit(f"Vehicles folder not found: {root}")
    report = inventory(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "vehicles_root": report["vehicles_root"],
        "package_count": report["package_count"],
        "classification_counts": report["classification_counts"],
        "drivable_candidates": [
            {key: item[key] for key in ("package", "bus_config_count", "o3d_files_in_model_dir", "missing_model_cfgs", "missing_meshes")}
            for item in report["drivable_candidates"]
        ],
        "report": str(args.output.resolve()),
    }, indent=2))


if __name__ == "__main__":
    main()
