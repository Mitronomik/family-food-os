"""Run the Russian method policies on five locked corpus reference profiles.

This is a read-only source-method trial, not canonical publication or import.
"""

import argparse
from dataclasses import asdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.domain.nutrition_methodology import (  # noqa: E402 - standalone repository entrypoint
    NutrientKind as N,
    ObservationMethod as M,
    ObservationState as S,
    ObservationSource,
    SourceObservation,
    RussianNutritionPolicy as P,
    evaluate_observation,
)

CODES = {"10.1.1", "8.1.5.1", "8.1.2.1", "8.1.5.12", "6.5.3"}
FIELDS = {
    "energy_kcal": (N.PUBLISHED_ENERGY, M.PUBLISHED),
    "protein_g": (N.PROTEIN, M.PUBLISHED),
    "fat_g": (N.FAT, M.PUBLISHED),
    "carbohydrates_g": (
        N.AVAILABLE_CARBOHYDRATE,
        M.AVAILABLE_PUBLISHED_ROW_UNSPECIFIED,
    ),
    "fiber_g": (N.FIBRE, M.PUBLISHED),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(corpus):
    lock = json.loads(
        (ROOT / "data/curation/dc2-first-batch-review/input-lock.json").read_text()
    )
    entry = next(
        r
        for r in lock["inputs"]
        if r["path"] == "packages/reference-profiles/normalized/profiles.jsonl"
    )
    path = corpus / entry["path"]
    if sha(path) != entry["sha256"]:
        raise ValueError("Исходные профили изменились.")
    profiles = [
        r
        for r in map(json.loads, path.read_text().splitlines())
        if r["source_code"] in CODES
    ]
    if len(profiles) != 5 or {r["source_code"] for r in profiles} != CODES:
        raise ValueError("Неполный набор профилей.")
    results = []
    for r in sorted(profiles, key=lambda r: r["source_code"]):
        if r["basis_g"] != 100 or r["basis_part"] != "edible":
            raise ValueError("Изменилась база.")
        for field, (kind, method) in FIELDS.items():
            c = r["values"][field]
            state = {
                "published_positive": S.VALUE,
                "below_detection": S.BELOW_DETECTION,
                "missing": S.MISSING,
            }[c["state"]]
            if state != S.VALUE and c["value"] is not None:
                raise ValueError("Неизвестное подменено числом.")
            obs = SourceObservation(
                kind,
                method,
                state,
                Decimal(c["value"]) if c["value"] is not None else None,
                c["unit"],
                Decimal(100),
                ObservationSource(
                    "SC-BOOK-2002",
                    "2002",
                    json.dumps(r["provenance"], sort_keys=True, ensure_ascii=False),
                    r["id"] + ":" + field,
                    r["id"] + ":source-form",
                    c["definition_code"],
                ),
                c["published_value"],
            )
            for policy in P:
                evaluated = evaluate_observation(obs, policy)
                results.append(asdict(evaluated))
    summary = dict(
        profiles=5,
        source_core_observations=25,
        policy_results=len(results),
        canonical_profiles_imported=0,
        source_native_available_carbohydrate_accepted_per_policy=5,
        strict_unknown_values=sum(
            r["amount"] is None for r in results if r["policy"] == P.STRICT_V1
        ),
        explicit_zero_estimates=sum(
            r["estimated"]
            for r in results
            if r["policy"] == P.PUBLISHED_ZERO_ESTIMATE_V1
        ),
        production_ready=False,
        reference_profiles_sha256=entry["sha256"],
        builder_sha256=sha(Path(__file__)),
    )
    return dict(summary=summary, results=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Числовой пакет должен оставаться вне публичного репозитория.")
    if output.exists():
        parser.error("Выберите новый файл; предыдущие результаты сохраняются.")
    result = build(args.corpus)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            default=lambda v: format(v, "f") if isinstance(v, Decimal) else v,
        )
        + "\n"
    )
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
