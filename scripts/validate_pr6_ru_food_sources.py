"""Offline raw USDA replay of the retained RU candidate extracts; no network or DB."""

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/curation/pr6-ru-food-data"


def verify_archives(directory: Path) -> dict[str, int]:
    manifest = json.loads((PACKAGE / "source-manifest.json").read_text())
    checked = 0
    for archive in manifest["archives"]:
        path = directory / (archive["id"] + ".zip")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == archive["sha256"]
        with zipfile.ZipFile(path) as handle:
            tables = {}
            for name, digest in archive["member_sha256"].items():
                names = [n for n in handle.namelist() if n.endswith("/" + name)]
                if digest is None:
                    assert not names
                    tables[name] = []
                    continue
                assert len(names) == 1
                payload = handle.read(names[0])
                assert hashlib.sha256(payload).hexdigest() == digest
                tables[name] = list(csv.DictReader(io.StringIO(payload.decode())))
        for source_id, source in manifest["profiles"].items():
            if source["archive_id"] != archive["id"]:
                continue
            assert source["food"] == next(
                r for r in tables["food.csv"] if r["fdc_id"] == source_id
            )
            rows = [r for r in tables["food_nutrient.csv"] if r["fdc_id"] == source_id]
            assert source["food_nutrients"] == rows
            ids = {r["nutrient_id"] for r in rows}
            assert source["nutrients"] == [
                r for r in tables["nutrient.csv"] if r["id"] in ids
            ]
            ids = {r["derivation_id"] for r in rows}
            assert source["derivations"] == [
                r for r in tables["food_nutrient_derivation.csv"] if r["id"] in ids
            ]
            checked += 1
    return {
        "verified_archives": len(manifest["archives"]),
        "candidate_source_extracts_replayed": checked,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-directory", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify_archives(args.source_directory), sort_keys=True))


if __name__ == "__main__":
    main()
