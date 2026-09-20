"""Verify review evidence and reject unsafe mappings without external sources."""

import json
import unittest
from pathlib import Path

from build_dc2_first_batch_review import require, sha, unique

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data/curation/dc2-first-batch-review"
GEN = PKG / "generated"


def validate():
    expected = {
        "group-reviews.json",
        "profile-reviews.json",
        "occurrence-reviews.json",
        "route-impact.json",
        "summary.json",
        "input-receipt.json",
    }
    hashed = set()
    for line in (GEN / "checksums.sha256").read_text().splitlines():
        digest, name = line.split("  ")
        require(name in expected and name not in hashed, "invalid manifest")
        require(sha(GEN / name) == digest, "modified output")
        hashed.add(name)
    require(hashed == expected, "incomplete manifest")
    for i in json.loads((GEN / "input-receipt.json").read_text())["repository_inputs"]:
        require(sha(ROOT / i["path"]) == i["sha256"], "changed repository input")
    groups = json.loads((GEN / "group-reviews.json").read_text())
    occurrences = json.loads((GEN / "occurrence-reviews.json").read_text())
    profiles = json.loads((GEN / "profile-reviews.json").read_text())
    decisions = unique(json.loads((PKG / "decisions.json").read_text()))
    require(
        len(groups) == 25 and len(occurrences) == 1532 and len(profiles) == 24,
        "missing review rows",
    )
    unique(occurrences)
    unique(profiles)
    for row in occurrences:
        require(row["decision_id"] in decisions, "dangling decision")
        require(
            not row["exact_mapping_accepted"] and row["canonical_food_id"] is None,
            "unreviewed mapping",
        )
        require(
            row["candidate_book_record_ids"]
            == next(
                g["candidate_book_record_ids"]
                for g in groups
                if g["id"] == row["decision_id"]
            ),
            "candidate drift",
        )
    for row in groups + occurrences + profiles:
        require(row["publication_ready"] is False, "publication promotion")
    for g in groups:
        require(
            g["occurrence_count"]
            == sum(r["decision_id"] == g["id"] for r in occurrences),
            "occurrence count drift",
        )
    return groups, profiles


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        groups, cls.profiles = validate()
        cls.groups = {g["label"]: g for g in groups}

    def test_salt_not_plain(self):
        self.assertEqual(
            self.groups["соль поваренная йодированная"]["book_source_codes"], []
        )

    def test_milk_not_arbitrary(self):
        self.assertEqual(self.groups["молоко"]["disposition"], "AMBIGUOUS_SOURCE_FORM")
        self.assertEqual(
            set(self.groups["молоко"]["book_source_codes"]), {"1.2.1.2", "1.2.1.4"}
        )

    def test_sour_cream_mismatch(self):
        self.assertEqual(self.groups["сметана"]["disposition"], "REJECT_FAT_MISMATCH")
        self.assertEqual(
            self.groups["сметана"]["fat_specification_by_source"],
            [["ru-school2022", "15", 4]],
        )

    def test_butter_salt_not_selected(self):
        self.assertEqual(
            set(self.groups["масло сливочное"]["book_source_codes"]), {"5.1.5", "5.1.6"}
        )

    def test_foreign_provenance_not_relabelled(self):
        for g in self.groups.values():
            for p in g["existing_profile_evidence"]:
                self.assertEqual(p["source_name"], "USDA_FDC")
                self.assertFalse(p["reuse_approved"])

    def test_sugar_censoring(self):
        p = next(p for p in self.profiles if p["source_code"] == "10.1.1")
        self.assertEqual(p["field_states"]["protein_g"], "below_detection")
        self.assertIsNone(p["canonical_nutrient_mapping"])

    def test_oil_missing_not_zero(self):
        p = next(p for p in self.profiles if p["source_code"] == "5.4.13")
        self.assertEqual(p["field_states"]["fiber_g"], "missing")

    def test_water_no_invented_book_source(self):
        self.assertEqual(self.groups["вода"]["candidate_book_record_ids"], [])

    def test_tea_not_drink(self):
        self.assertEqual(
            self.groups["чай черный байховый"]["disposition"],
            "REJECT_PREPARED_DRINK_PROXY",
        )

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            unique([{"id": "x"}, {"id": "x"}])


if __name__ == "__main__":
    unittest.main()
