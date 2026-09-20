"""Verify review evidence and reject unsafe mappings without external sources."""

import json
import unittest
from collections import Counter
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

    lock = json.loads((PKG / "input-lock.json").read_text())
    receipt = json.loads((GEN / "input-receipt.json").read_text())
    summary = json.loads((GEN / "summary.json").read_text())

    require(lock["inputs"] == receipt["external_inputs"], "external input receipt drift")
    require(summary["base_commit"] == lock["base_commit"], "base commit drift")
    require(summary["queue"] == lock["queue"], "queue drift")

    for item in receipt["repository_inputs"]:
        require(sha(ROOT / item["path"]) == item["sha256"], "changed repository input")

    groups = json.loads((GEN / "group-reviews.json").read_text())
    occurrences = json.loads((GEN / "occurrence-reviews.json").read_text())
    profiles = json.loads((GEN / "profile-reviews.json").read_text())
    routes = json.loads((GEN / "route-impact.json").read_text())
    decisions = unique(json.loads((PKG / "decisions.json").read_text()))

    require(
        len(groups) == 25 and len(occurrences) == 1532 and len(profiles) == 24,
        "missing review rows",
    )
    groups_by_id = unique(groups)
    unique(occurrences)
    unique(profiles)
    unique(routes)

    require(set(groups_by_id) == set(decisions), "decision/group coverage drift")
    for decision in decisions.values():
        require(decision["publication_ready"] is False, "decision publication promotion")

    for row in occurrences:
        require(row["decision_id"] in decisions, "dangling decision")
        require(
            not row["exact_mapping_accepted"] and row["canonical_food_id"] is None,
            "unreviewed mapping",
        )
        require(
            row["candidate_book_record_ids"]
            == groups_by_id[row["decision_id"]]["candidate_book_record_ids"],
            "candidate drift",
        )

    for row in groups + occurrences + profiles:
        require(row["publication_ready"] is False, "publication promotion")

    for group in groups:
        require(
            group["occurrence_count"]
            == sum(row["decision_id"] == group["id"] for row in occurrences),
            "occurrence count drift",
        )
        for profile in group["existing_profile_evidence"]:
            require(profile["reuse_approved"] is False, "existing profile reuse promotion")

    for profile in profiles:
        require(
            profile["canonical_nutrient_mapping"] is None,
            "canonical nutrient mapping promotion",
        )

    for route in routes:
        require(route["actually_unblocked"] is False, "route promotion")

    candidate_record_ids = {
        record_id
        for group in groups
        for record_id in group["candidate_book_record_ids"]
    }
    require(
        candidate_record_ids == {profile["id"] for profile in profiles},
        "candidate/profile coverage drift",
    )

    expected_dispositions = dict(
        sorted(Counter(row["disposition"] for row in decisions.values()).items())
    )
    expected_scope_routes = sum(
        route["all_dependencies_in_review_scope"] for route in routes
    )
    expected_visual_profiles = sum(
        profile["visual_review_id"] is not None for profile in profiles
    )

    require(summary["reviewed_groups"] == len(groups), "summary group count drift")
    require(
        summary["occurrences_accounted_under_group_review"] == len(occurrences),
        "summary occurrence count drift",
    )
    require(
        summary["exact_book_record_candidates"] == len(profiles),
        "summary profile count drift",
    )
    require(
        summary["visual_profile_candidates"] == expected_visual_profiles,
        "summary visual profile count drift",
    )
    require(
        summary["dispositions"] == expected_dispositions,
        "summary disposition count drift",
    )
    require(
        summary["affected_material_routes"] == len(routes),
        "summary route count drift",
    )
    require(
        summary["routes_all_dependencies_in_review_scope"] == expected_scope_routes,
        "summary scoped-route count drift",
    )
    require(summary["publication_ready_foods"] == 0, "summary publication promotion")
    require(summary["actually_unblocked_recipes"] == 0, "summary recipe promotion")
    require(summary["production_changed"] is False, "summary production promotion")

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
