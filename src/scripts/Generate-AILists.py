#!/usr/bin/env python3
"""Write a HK_BigMap ailists.cfg and parklist_p.txt from the vehicles on disk.

The map is a road network with no traffic until these exist: OMSI reads
`ailists.cfg` for the AI groups it spawns (cars plus the bus types that run as
scheduled AI) and `parklist_p.txt` for the scenery vehicles parked at stops.

Only entries whose vehicle file actually exists under the OMSI install are
written, so a pack the user has not installed is skipped instead of producing
a map that fails to load.

Usage:
  python src/scripts/Generate-AILists.py --root . --omsi "A:\\SteamLibrary\\steamapps\\common\\OMSI 2"
"""

import argparse
import os
import sys

# Cars, weighted by how often they actually appear on HK roads.
CARS = [
    ("vehicles\\Toyota_EchoVerso\\ai_Toyota_Echoverso.ovh", 45),
    ("vehicles\\Toyota_Hiace\\ai_Toyota_Hiace.ovh", 30),
    ("vehicles\\Toyota_Noah\\ai_Toyota_Noah.ovh", 30),
    ("vehicles\\Toyota_Crown\\ai_Toyota_Crown_urban.ovh", 40),
    ("vehicles\\Lexus_CT200h\\ai_lexus_ct200h.bus", 40),
    ("vehicles\\Toyota_Prius\\ai_prius_xw30.bus", 50),
    ("vehicles\\Toyota_Prius\\ai_prius_xw30_hktaxi.bus", 60),
    ("vehicles\\Tesla_Model_S\\ai_model_s.bus", 20),
    ("vehicles\\Tesla_Model_X\\ai_model_x.bus", 10),
    ("vehicles\\VW_Golf_7\\ai_golf_7.bus", 50),
    ("vehicles\\Isuzu_N_Series\\ai_isuzu_npr.bus", 120),
    ("vehicles\\Toyota_Coaster_Series7_HK\\Van_Red_Series7_.ovh", 40),
    ("vehicles\\Toyota_Coaster_Series7_HK\\Van_Green_Series7_.ovh", 30),
]

# The operating companies' fleets, weighted roughly by real fleet size.
# KMB dominates, then Citybus/LWB, then the smaller operators.
BUS_GROUPS = [
    ("KMB", [
        ("vehicles\\AI_KMB_DENNIS\\3ATENU_FL_AI.bus", 130),
        ("vehicles\\AI_KMB_DENNIS\\3ATENU_FL_AI_Red.bus", 70),
        ("vehicles\\AI_KMB_DENNIS\\E6X_AI.bus", 89),
        ("vehicles\\AI_KMB_DENNIS\\15XX.bus", 60),
        ("vehicles\\AI_KMB_DENNIS\\25XX.bus", 40),
        ("vehicles\\AI_KMB_Enviro500\\ATEU_LH.bus", 30),
        ("vehicles\\AI_KMB_Enviro500\\ATEU_VH.bus", 30),
        ("vehicles\\AI_KMB_Enviro500\\AVBE_LOH.bus", 10),
        ("vehicles\\AI_KMB_Volvo_Wright\\AVBWU_Hanover.bus", 40),
        ("vehicles\\AI_KMB_Volvo_Wright\\AVBWU_Gorba.bus", 20),
        ("vehicles\\AI_KMB_VOLVO_OLYMPIAN\\KMB_3AV_CT_AI.bus", 15),
        ("vehicles\\AI_KMB_Volvo_V6B\\V6B.bus", 15),
    ]),
    ("Citybus", [
        ("vehicles\\AI_CTB_DENNIS\\63XX.bus", 60),
        ("vehicles\\AI_CTB_DENNIS\\83XX_AI.bus", 40),
        ("vehicles\\AI_CTB_VOLVO_6XX\\*.bus", 20),
        ("vehicles\\AI_CTB_VOLVO_5XX\\*.bus", 15),
        ("vehicles\\AI_CTB_MAN_2500\\*.bus", 8),
    ]),
    ("LWB", [
        ("vehicles\\AI_LWB_DENNIS_UE6X\\3ATENU_FL_AI.bus", 50),
        ("vehicles\\AI_LWB_DENNIS_UE6X\\15XX.bus", 30),
        ("vehicles\\AI_LWB_DENNIS_UE6X\\25XX.bus", 20),
    ]),
    ("NWFB", [
        ("vehicles\\AI_NWFB_VOLVO_OLYMPIAN\\NWFB_VA_AI.bus", 25),
        ("vehicles\\AI_NWFB_VOLVO_OLYMPIAN\\NWFB_VA_RS_AI.bus", 15),
        ("vehicles\\AI_NWS_Enviro500\\*.bus", 20),
        ("vehicles\\AI_NWS_ALX500\\*.bus", 15),
        ("vehicles\\AI_NWS_Volvo_Wright\\*.bus", 12),
    ]),
]

PARKED = [
    "Vehicles\\Toyota_Prius\\Parked_prius_xw30_hktaxi.sco",
    "Vehicles\\Toyota_Prius\\Parked_prius_xw30.sco",
    "Vehicles\\Tesla_Model_S\\Parked_model_s.sco",
    "Vehicles\\Toyota_Alphard\\Parked_alphard.sco",
    "Vehicles\\VW_Golf_7\\Parked_golf_7.sco",
    "Vehicles\\Toyota_Echoverso\\Toyota_parked_Echoverso.sco",
    "Vehicles\\Toyota_Hiace\\Toyota_parked_Hiace.sco",
    "Vehicles\\Toyota_Coaster_Series7_HK\\Coaster_parked.sco",
]


def resolve(omsi, rel):
    """Expand a trailing \\*.bus against the install; return the file names that exist."""
    if rel.endswith("\\*.bus"):
        folder = os.path.join(omsi, rel[:-6].replace("\\", os.sep))
        if not os.path.isdir(folder):
            return []
        return [rel[:-5] + n for n in sorted(os.listdir(folder)) if n.lower().endswith(".bus")]
    path = os.path.join(omsi, rel.replace("\\", os.sep))
    return [rel] if os.path.isfile(path) else []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--omsi", required=True, help="OMSI 2 installation directory")
    ap.add_argument("--map", default="HK_BigMap")
    args = ap.parse_args()

    omsi = os.path.abspath(args.omsi)
    if not os.path.isdir(omsi):
        sys.exit(f"not an OMSI directory: {omsi}")
    out_dir = os.path.join(os.path.abspath(args.root), "maps", args.map)
    if not os.path.isdir(out_dir):
        sys.exit(f"map not found: {out_dir}")

    lines = []
    written = skipped = 0

    # 1. private cars: one group so OMSI spreads them over the whole map
    car_lines = []
    for rel, weight in CARS:
        for found in resolve(omsi, rel):
            car_lines.append(f"{found}\t{weight}")
            written += 1
        if not resolve(omsi, rel):
            skipped += 1
    if car_lines:
        lines += ["[aigroup_2]", "NormalCars", "HK_BigMap AI", *car_lines, "[end]", ""]

    # 2. one group per operator, so a route can be given the right fleet
    for name, fleet in BUS_GROUPS:
        group_lines = []
        for rel, weight in fleet:
            hits = resolve(omsi, rel)
            if not hits:
                skipped += 1
                continue
            for found in hits:
                # a wildcard expands to many vehicles; share the weight between them
                group_lines.append(f"{found}\t{max(1, weight // len(hits))}")
                written += 1
        if group_lines:
            lines += ["[aigroup_2]", name, "HK_BigMap AI", *group_lines, "[end]", ""]

    write_ansi(os.path.join(out_dir, "ailists.cfg"), lines)

    parked = [p for p in PARKED if os.path.isfile(os.path.join(omsi, p.replace("\\", os.sep)))]
    write_ansi(os.path.join(out_dir, "parklist_p.txt"), parked)

    print(f"ailists.cfg:  {written} vehicle entries, {skipped} unavailable")
    print(f"parklist_p.txt: {len(parked)} parked vehicles")
    print(f"-> {out_dir}")


def write_ansi(path, lines):
    """ailists.cfg / parklist_p.txt are ANSI (Windows-1252), unlike the map files."""
    with open(path, "w", encoding="cp1252", errors="replace", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

