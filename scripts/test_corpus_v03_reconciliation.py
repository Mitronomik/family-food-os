"""Adversarial checks of the metadata acceptance boundary."""

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from validate_corpus_v03_reconciliation import validate

PACKAGE = (
    Path(__file__).resolve().parents[1]
    / "data/curation/corpus-v03-reconciliation/generated"
)


class ReconciliationTest(unittest.TestCase):
    def mutate(self, name, change, rewrite_hashes=True):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "package"
            shutil.copytree(PACKAGE, root)
            path = root / name
            if name.endswith("jsonl"):
                data = [json.loads(v) for v in path.read_text().splitlines()]
                change(data)
                path.write_text("".join(json.dumps(v) + "\n" for v in data))
            else:
                data = json.loads(path.read_text())
                change(data)
                path.write_text(json.dumps(data))
            if rewrite_hashes:
                entries = []
                for line in (root / "checksums.sha256").read_text().splitlines():
                    _, filename = line.split("  ")
                    entries.append(
                        hashlib.sha256((root / filename).read_bytes()).hexdigest()
                        + "  "
                        + filename
                    )
                (root / "checksums.sha256").write_text("\n".join(entries) + "\n")
            with self.assertRaises((ValueError, KeyError)):
                validate(root)

    def test_wrong_group(self):
        def change(rows):
            rows[0]["review_group_id"] = next(
                r["review_group_id"]
                for r in rows
                if r["review_group_id"] != rows[0]["review_group_id"]
            )

        self.mutate("food-demand.jsonl", change)

    def test_wrong_batch_group(self):
        self.mutate("review-batches.json", lambda d: d[0]["review_group_ids"].clear())

    def test_wrong_book_edition(self):
        self.mutate(
            "book-reference-index.jsonl",
            lambda d: d[0].update(source_pdf_sha256="0" * 64),
        )

    def test_valid(self):
        self.assertEqual(validate(PACKAGE)["production_publications"], 0)

    def test_hash(self):
        self.mutate("summary.json", lambda d: d.update(production_changed=True), False)

    def test_duplicate(self):
        self.mutate("food-demand.jsonl", lambda d: d.append(d[0]))

    def test_identity(self):
        self.mutate(
            "food-demand.jsonl", lambda d: d[0].update(canonical_food_id="invented")
        )

    def test_lexical_equivalence(self):
        self.mutate(
            "food-review-groups.jsonl",
            lambda d: d[0].update(is_semantic_equivalence=True),
        )

    def test_history(self):
        self.mutate(
            "recipe-crosswalk.jsonl", lambda d: d[0].update(v03_card_id="invented")
        )

    def test_lost_dependency(self):
        self.mutate(
            "review-batches.json",
            lambda d: next(b for b in d if b["id"].startswith("DC3"))[
                "dependencies"
            ].clear(),
        )

    def test_publish(self):
        self.mutate(
            "review-batches.json", lambda d: d[0].update(publication_ready=True)
        )

    def test_deleted_route(self):
        self.mutate("route-index.jsonl", lambda d: d.pop())

    def test_promoted_pr70(self):
        self.mutate(
            "pr70-food-crosswalk.jsonl",
            lambda d: d[0].update(exact_v03_mapping="invented"),
        )

    def test_clinical_gate(self):
        def change(rows):
            next(r for r in rows if r["material_ready"] and r["clinical_scope"]).update(
                clinical_scope=False
            )

        self.mutate("route-index.jsonl", change)


if __name__ == "__main__":
    unittest.main()
