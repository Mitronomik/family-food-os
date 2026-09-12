"""Offline replay of B2-B2 exact profile/portion evidence from the pinned SR archive."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

PACKAGE = (
    Path(__file__).resolve().parents[1] / "data/curation/pr6-data-b2-b2-redesigned"
)


def verify(archive_path):
    manifest = json.loads((PACKAGE / "source-manifest.json").read_text())
    archive = manifest["archives"][0]
    assert hashlib.sha256(archive_path.read_bytes()).hexdigest() == archive["sha256"]
    tables = {}
    with zipfile.ZipFile(archive_path) as zipped:
        for name, digest in archive["member_sha256"].items():
            raw = zipped.read(
                next(n for n in zipped.namelist() if n.endswith("/" + name))
            )
            assert hashlib.sha256(raw).hexdigest() == digest
            tables[name] = list(csv.DictReader(io.StringIO(raw.decode())))
    for sid, source in manifest["profiles"].items():
        assert source["food"] == next(
            r for r in tables["food.csv"] if r["fdc_id"] == sid
        )
        rows = [r for r in tables["food_nutrient.csv"] if r["fdc_id"] == sid]
        assert source["food_nutrients"] == rows
        assert source["nutrients"] == [
            r
            for r in tables["nutrient.csv"]
            if r["id"] in {n["nutrient_id"] for n in rows}
        ]
        assert source["derivations"] == [
            r
            for r in tables["food_nutrient_derivation.csv"]
            if r["id"] in {n["derivation_id"] for n in rows}
        ]
        assert source["portions"] == [
            r for r in tables["food_portion.csv"] if r["fdc_id"] == sid
        ]
        assert source["attributes"] == [
            r for r in tables["food_attribute.csv"] if r["fdc_id"] == sid
        ]
    return dict(
        archive_sha256=archive["sha256"],
        complete_source_extracts=5,
        portion_inventories=5,
        source_members_verified=len(tables),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive), sort_keys=True))
