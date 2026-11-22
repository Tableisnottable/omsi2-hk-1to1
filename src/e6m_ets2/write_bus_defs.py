"""Add the locally converted ATENU model to the native ETS2 coach mod."""
from __future__ import annotations

import json
import re
from pathlib import Path

from build_e6m import BASE
from settings import ROOT, VERSION

SOURCE_DEFS = BASE / "def/vehicle/bus/adl.e6m.coach"
TARGET_DEFS = BASE / "def/vehicle/bus/adl.atenu.coach"
REPLACEMENTS = (("E6M", "ATENU"), ("e6m", "atenu"))


def rewritten(text: str) -> str:
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def copy_definition(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rewritten(source.read_text(encoding="utf-8-sig")), encoding="utf-8")


def clone_tree(source: Path, target: Path) -> int:
    if not source.is_dir():
        raise FileNotFoundError(f"Run write_defs.py first; source definition tree not found: {source}")
    count = 0
    for file in source.rglob("*.sii"):
        relative = Path(rewritten(file.relative_to(source).as_posix()))
        copy_definition(file, target / relative)
        count += 1
    if not count:
        raise ValueError(f"No SII files found under {source}")
    return count


def main() -> None:
    copied = clone_tree(SOURCE_DEFS, TARGET_DEFS)
    paths = (
        ("def/vehicle/bus_dealer/adl/adl_e6m.sii", "def/vehicle/bus_dealer/adl/adl_atenu.sii"),
        ("def/vehicle/bus_desktop/adl.e6m.sii", "def/vehicle/bus_desktop/adl.atenu.sii"),
        ("def/camera/units/interior_adl_e6m.sui", "def/camera/units/interior_adl_atenu.sui"),
        ("def/camera/units/interior_adl_e6m_oculus.sui", "def/camera/units/interior_adl_atenu_oculus.sui"),
        ("def/camera/camera_storage.e6m.sii", "def/camera/camera_storage.atenu.sii"),
        ("def/camera/camera_storage.oculus.e6m.sii", "def/camera/camera_storage.oculus.atenu.sii"),
    )
    for source, target in paths:
        copy_definition(BASE / source, BASE / target)
    copied += len(paths)

    manifest = BASE / "manifest.sii"
    manifest_text = manifest.read_text(encoding="utf-8-sig")
    manifest_text = re.sub(r'(?m)(display_name:\s*")[^"]+',
                           r'\1KMB Bus Conversion Pack - E6M and ATENU', manifest_text)
    manifest.write_text(manifest_text, encoding="utf-8")
    description = BASE / "mod_description.txt"
    if description.is_file():
        text = description.read_text(encoding="utf-8-sig")
        text = text.replace("KMB ADL Enviro500 MMC E6M - local conversion prototype.",
                            "KMB E6M and ATENU - local conversion prototypes.")
        text = text.replace("Truck prototype: Access Mod Dealer > Scania > ADL E6M.\n", "")
        text = text.replace("Coach mode: select Coaches mode and look in the ADL bus dealer for E6M.",
                            "Coach mode: select Coaches mode and look in the ADL bus dealer for E6M or ATENU.")
        description.write_text(text, encoding="utf-8")

    report = {
        "version": VERSION,
        "vehicle": "ADL Enviro500 ATENU",
        "definition_files_written": copied,
        "coach_definition_root": str(TARGET_DEFS),
        "dealer_entries": ["def/vehicle/bus_dealer/adl/adl_atenu.sii",
                           "def/vehicle/bus_desktop/adl.atenu.sii"],
        "model_key": "adl_atenu",
        "notes": ["Definitions clone the working E6M three-axle coach template.",
                  "Engine and passenger capacity are provisional; OMSI scripts and animations are not ported.",
                  "Runtime dealer and driving behavior remain unverified."],
    }
    report_path = ROOT / "work/bus_models/atenu_definitions.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
