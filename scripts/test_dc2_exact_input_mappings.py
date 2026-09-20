"""Offline invariants including adversarial edits with refreshed checksums."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import build_dc2_exact_input_mappings as subject


class ExactInputTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name)
        for source in subject.PACKAGE.rglob('*.json'):
            dest = self.package/source.relative_to(subject.PACKAGE)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(source.read_bytes())
        self.patch = patch.object(subject, 'PACKAGE', self.package)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def alter(self, name, change):
        path = self.package/'generated'/name
        value = json.loads(path.read_text())
        change(value)
        path.write_text(subject.dumps(value))
        manifest = self.package/'generated/checksums.json'
        data = json.loads(manifest.read_text())
        data[name] = subject.sha(path)
        manifest.write_text(subject.dumps(data))

    def refresh_receipt_config(self, name):
        receipt = self.package/'generated/input-receipt.json'
        data = json.loads(receipt.read_text())
        data['config_sha256'][name] = subject.sha(self.package/name)
        receipt.write_text(subject.dumps(data))
        manifest = self.package/'generated/checksums.json'
        checksums = json.loads(manifest.read_text())
        checksums['input-receipt.json'] = subject.sha(receipt)
        manifest.write_text(subject.dumps(checksums))

    def test_valid(self):
        self.assertEqual(211, len(subject.validate_committed()))

    def test_authority_and_mass_tampering(self):
        for field, value in [
            ('publication_ready', True),
            ('nutrient_calculation_ready', True),
            ('canonical_food_id', 'invented'),
            ('retained_fraction', '1'),
            ('nutrient_equivalence_accepted', True),
            ('additional_cold_loss_application_allowed', True),
            ('physical_net_weighing_stage', 'raw_preheat'),
            ('source_identity_status', 'accepted'),
            ('source_accounting_basis', 'actual_physical_net'),
            ('net_mass_semantics_override', 'physical_preheat_mass'),
            ('retained_fraction_status', 'known'),
            ('transformation_version', 'dc2-exact-input-v2'),
            ('preparation_context_sha256', 'invented'),
            ('flags', ['invented_authority']),
        ]:
            with self.subTest(field=field):
                original = (self.package/'generated/mappings.json').read_text()
                self.alter('mappings.json', lambda rs:rs[0].update({field:value}))
                with self.assertRaises(ValueError): subject.validate_committed()
                (self.package/'generated/mappings.json').write_text(original)

    def test_form_authority_tampering_with_refreshed_receipt(self):
        forms = self.package/'forms.json'
        original_forms = forms.read_text()
        receipt = self.package/'generated/input-receipt.json'
        original_receipt = receipt.read_text()
        manifest = self.package/'generated/checksums.json'
        original_manifest = manifest.read_text()
        for field, value in [
            ('canonical_food_id', 'invented'),
            ('nutrient_equivalence_accepted', True),
        ]:
            with self.subTest(field=field):
                data = json.loads(original_forms)
                data[0][field] = value
                forms.write_text(subject.dumps(data))
                self.refresh_receipt_config('forms.json')
                with self.assertRaisesRegex(ValueError, 'form authority'):
                    subject.validate_committed()
                forms.write_text(original_forms)
                receipt.write_text(original_receipt)
                manifest.write_text(original_manifest)

    def test_source_nutrition_policy_tampering(self):
        path = self.package/'source-nutrition-policy.json'
        data = json.loads(path.read_text())
        data['source_published_values_second_heat_loss_application_allowed'] = True
        path.write_text(subject.dumps(data))
        with self.assertRaisesRegex(ValueError, 'source nutrition policy'):
            subject.validate_committed()

    def test_missing_route_hold(self):
        self.alter('route-holds.json', lambda rs:rs.pop())
        with self.assertRaisesRegex(ValueError,'route holds'): subject.validate_committed()

    def test_lost_exception(self):
        self.alter('mappings.json', lambda rs:next(r for r in rs if r['material_use_hold']).update(material_use_hold=False))
        with self.assertRaisesRegex(ValueError,'exception'): subject.validate_committed()

    def test_wrong_summary(self):
        self.alter('summary.json', lambda r:r.update(occurrences=212))
        with self.assertRaisesRegex(ValueError,'summary'): subject.validate_committed()

    def test_missing_manifest_file(self):
        path=self.package/'generated/checksums.json'
        data=json.loads(path.read_text());del data['route-holds.json'];path.write_text(subject.dumps(data))
        with self.assertRaisesRegex(ValueError,'manifest'): subject.validate_committed()

    def test_changed_input_lock(self):
        path=self.package/'input-lock.json';data=json.loads(path.read_text());data['base_commit']='wrong';path.write_text(subject.dumps(data))
        with self.assertRaisesRegex(ValueError,'receipt'): subject.validate_committed()

    def test_wrong_identity(self):
        self.alter('mappings.json', lambda rs:rs[0].update(demand_id='wrong'))
        with self.assertRaisesRegex(ValueError,'crosswalk'): subject.validate_committed()


if __name__ == '__main__':
    unittest.main()
