"""Deterministically compile the reviewed B2-A slice, with explicit row comparisons."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.seed.recipe_corrections import (  # noqa: E402
    B1,
    CURATION,
    DIRECTORY,
    INPUT_PATHS,
    OPERATION,
    PR4,
    STARTING_MAIN,
    build_promotion,
    digest,
    read_json,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    corrections, assessments = build_promotion(
        read_json(ROOT / CURATION),
        read_json(ROOT / PR4)["recipes"],
        read_json(ROOT / B1 / "assessments.json")["assessments"],
    )
    payloads = {"corrections.json": corrections, "assessments.json": assessments}
    if args.write:
        DIRECTORY.mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        encoded = (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        )
        if args.write:
            (DIRECTORY / name).write_text(encoded)
        elif (DIRECTORY / name).read_text() != encoded:
            raise SystemExit("B2-A promotion differs: " + name)
    manifest = dict(
        schema_version=1,
        operation=OPERATION,
        starting_main=STARTING_MAIN,
        input_sha256={p: digest(ROOT / p) for p in sorted(INPUT_PATHS)},
        payload_sha256={p: digest(DIRECTORY / p) for p in sorted(payloads)},
        recipe_version_count=len(corrections["corrections"]),
        assessment_count=len(assessments["assessments"]),
        status_counts=dict(
            sorted(
                Counter(
                    e["assessment"]["status_code"] for e in assessments["assessments"]
                ).items()
            )
        ),
        issue_counts=dict(
            sorted(
                Counter(
                    i
                    for e in assessments["assessments"]
                    for i in e["assessment"]["issues"]
                ).items()
            )
        ),
    )
    encoded = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if args.write:
        (DIRECTORY / "manifest.json").write_text(encoded)
    elif (DIRECTORY / "manifest.json").read_text() != encoded:
        raise SystemExit("B2-A manifest differs.")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
