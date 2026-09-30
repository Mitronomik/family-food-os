"""Validate the committed R1-E blocker map against deterministic rebuild."""

from __future__ import annotations

import json

from build_r1e_corpus_blockers import OUT, build


def main() -> None:
    expected_rows, expected_summary, expected_batch = build()
    actual_rows = [
        json.loads(line)
        for line in (OUT / "blocker-map.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    actual_summary = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    actual_batch = json.loads((OUT / "selected-batch.json").read_text(encoding="utf-8"))

    if actual_rows != expected_rows:
        raise SystemExit("R1-E blocker map differs from deterministic rebuild.")
    if actual_summary != expected_summary:
        raise SystemExit("R1-E summary differs from deterministic rebuild.")
    if actual_batch != expected_batch:
        raise SystemExit("R1-E selected batch differs from deterministic rebuild.")

    if len(actual_rows) != 547:
        raise SystemExit("R1-E must retain exactly 547 recipe identities.")
    if any(not row["next_blocker"] for row in actual_rows):
        raise SystemExit("Every R1-E row must have one deterministic next blocker.")
    if actual_batch["candidate_count"] != 4:
        raise SystemExit("First R1-E breakfast batch must contain four candidates.")

    print("R1-E corpus blocker map: OK")


if __name__ == "__main__":
    main()
