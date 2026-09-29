#!/usr/bin/env python3
"""Validate committed R1-D source admission inventory against repository inputs."""

from __future__ import annotations

import json
from pathlib import Path

from build_r1d_planner_source_inventory import ROOT, build

PACKAGE = ROOT / "data/curation/r1d-planner-admission"


def main() -> None:
    expected_inventory, expected_summary = build()
    actual_inventory = [
        json.loads(line)
        for line in (PACKAGE / "source-inventory.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    actual_summary = json.loads((PACKAGE / "summary.json").read_text(encoding="utf-8"))

    if actual_inventory != expected_inventory:
        raise SystemExit("R1-D source inventory differs from deterministic rebuild.")
    if actual_summary != expected_summary:
        raise SystemExit("R1-D summary differs from deterministic rebuild.")

    if len(actual_inventory) != 547:
        raise SystemExit("R1-D inventory must contain exactly 547 retained recipe identities.")
    expected_families = {"USSR82": 68, "ru-school2022": 265, "RU-MR-2019": 214}
    actual_families = {
        family: values["retained"]
        for family, values in actual_summary["source_family_counts"].items()
    }
    if actual_families != expected_families:
        raise SystemExit(f"R1-D source-family counts drifted: {actual_families!r}")

    print("R1-D Planner source admission inventory: OK")


if __name__ == "__main__":
    main()
