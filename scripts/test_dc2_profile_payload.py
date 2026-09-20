"""Offline compatibility and repository-metadata fail-closed tests."""

import json
import shutil
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import build_dc2_profile_payload as subject


def cell(value="1", state="published_positive"):
    return {
        "value": value,
        "published_value": value,
        "state": state,
        "detection_limit": None,
    }


class ProfilePayloadTest(unittest.TestCase):
    def setUp(self):
        self.original_package = subject.PACKAGE

    def package_copy(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name)
        for source in self.original_package.glob("*.json"):
            shutil.copy2(source, target / source.name)
        patcher = patch.object(subject, "PACKAGE", target)
        patcher.start()
        self.addCleanup(patcher.stop)
        return target

    def test_repository_contract_valid(self):
        receipt = subject.validate_repository_contract()
        self.assertEqual("repository_metadata_only", receipt["acceptance_evidence"])
        self.assertFalse(receipt["external_full_build_claim_used_for_acceptance"])
        self.assertFalse(receipt["production_publication_ready"])
        self.assertFalse(receipt["database_write_attempted"])
        self.assertEqual(5, len(receipt["domain_blockers"]))

    def test_source_positive(self):
        subject.validate_cell(cell())

    def test_unknown_not_zero(self):
        with self.assertRaises(ValueError):
            subject.validate_cell(cell("0", "below_detection"))
        candidate = cell(None, "below_detection")
        candidate["published_value"] = "0"
        subject.validate_cell(candidate)

    def test_nan_and_negative(self):
        for value in ["NaN", "-1", "0", "Infinity"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                subject.validate_cell(cell(value))

    def test_changed_number(self):
        candidate = cell()
        candidate["published_value"] = "2"
        with self.assertRaises(ValueError):
            subject.validate_cell(candidate)

    def test_current_domain_requires_legacy_carbs(self):
        profile = {
            "id": "test",
            "source_code": "synthetic",
            "observations": [
                {"source_field": field, "source_value": cell()}
                for field in subject.FIELDS
            ],
        }
        result = subject.probe_profile(profile)
        self.assertEqual(
            ["carbohydrates_g"], result["unsupported_legacy_fields"]
        )
        self.assertFalse(result["database_write_attempted"])

    def test_current_domain_cannot_anchor_below_detection(self):
        profile = {
            "id": "test",
            "source_code": "synthetic",
            "observations": [
                {
                    "source_field": field,
                    "source_value": cell(
                        None if field in ["protein_g", "fat_g"] else "1",
                        "below_detection"
                        if field in ["protein_g", "fat_g"]
                        else "published_positive",
                    ),
                }
                for field in subject.FIELDS
            ],
        }
        for observation in profile["observations"]:
            if observation["source_value"]["state"] == "below_detection":
                observation["source_value"]["published_value"] = "0"
        self.assertEqual(
            ["protein_g", "fat_g", "carbohydrates_g"],
            subject.probe_profile(profile)["unsupported_legacy_fields"],
        )

    def test_unrelated_domain_failure_is_not_macro_evidence(self):
        from app.domain.errors import (
            DomainIssue,
            DomainIssueCode,
            DomainValidationError,
        )

        profile = {
            "id": "test",
            "source_code": "synthetic",
            "observations": [
                {"source_field": field, "source_value": cell()}
                for field in subject.FIELDS
            ],
        }
        error = DomainValidationError(
            DomainIssue(
                DomainIssueCode.INVALID_IDENTIFIER,
                "bad ID",
                field="id",
            )
        )
        with patch.object(subject, "FoodNutritionProfile", side_effect=error):
            with self.assertRaises(DomainValidationError):
                subject.probe_profile(profile)

    def test_identity_plan_drift_rejected(self):
        package = self.package_copy()
        path = package / "identity-plan.json"
        data = json.loads(path.read_text())
        data[0]["canonical_food_id"] = "invented"
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "identity plan"):
            subject.validate_repository_contract()

    def test_identity_code_drift_rejected(self):
        package = self.package_copy()
        path = package / "identity-plan.json"
        data = json.loads(path.read_text())
        data[0]["proposed_canonical_code"] = "RICE_WHITE"
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "identity action/code"):
            subject.validate_repository_contract()

    def test_rights_promotion_rejected(self):
        package = self.package_copy()
        path = package / "source-use-review.json"
        data = json.loads(path.read_text())
        data["rights_status"] = "OPEN_REUSE"
        data["explicit_reuse_permission"] = "found"
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "rights review"):
            subject.validate_repository_contract()

    def test_outbound_request_claim_rejected(self):
        package = self.package_copy()
        path = package / "source-use-review.json"
        data = json.loads(path.read_text())
        data["outbound_request_sent"] = True
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "rights review"):
            subject.validate_repository_contract()

    def test_verification_summary_promotion_rejected(self):
        package = self.package_copy()
        path = package / "verification-summary.json"
        data = json.loads(path.read_text())
        data["imported_profiles"] = 5
        data["canonical_numeric_values"] = 60
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "verification summary"):
            subject.validate_repository_contract()

    def test_verification_receipt_drift_rejected(self):
        package = self.package_copy()
        path = package / "verification-receipt.json"
        data = json.loads(path.read_text())
        data["production_publication_ready"] = True
        path.write_text(subject.encoded(data))
        with self.assertRaisesRegex(ValueError, "verification receipt"):
            subject.validate_repository_contract()

    def test_refuse_repository_output(self):
        with self.assertRaisesRegex(ValueError, "outside public"):
            subject.write({}, subject.ROOT / "data/test-private")

    def test_preserve_old_output(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "existing").write_text("keep")
            with self.assertRaisesRegex(ValueError, "empty"):
                subject.write({}, path)
            self.assertEqual("keep", (path / "existing").read_text())

    def test_changed_external_input_fails_before_extraction(self):
        with patch.object(subject, "validate_repository_contract", return_value={}):
            with patch.object(
                subject,
                "load",
                return_value={
                    "inputs": [
                        {
                            "root": "corpus",
                            "path": "changed",
                            "sha256": "wrong",
                        }
                    ]
                },
            ):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory)
                    (path / "changed").write_text("new")
                    with self.assertRaisesRegex(ValueError, "changed input"):
                        subject.build(path)


if __name__ == "__main__":
    unittest.main()
