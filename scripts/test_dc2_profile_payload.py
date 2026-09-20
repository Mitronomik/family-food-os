"""Offline compatibility tests; all numbers here are synthetic test data."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import build_dc2_profile_payload as subject


def cell(value='1', state='published_positive'):
    return dict(value=value, published_value=value, state=state, detection_limit=None)


class ProfilePayloadTest(unittest.TestCase):
    def test_source_positive(self):
        subject.validate_cell(cell())

    def test_unknown_not_zero(self):
        with self.assertRaises(ValueError): subject.validate_cell(cell('0','below_detection'))
        c=cell(None,'below_detection');c['published_value']='0';subject.validate_cell(c)

    def test_nan_and_negative(self):
        for value in ['NaN','-1','0','Infinity']:
            with self.subTest(value=value),self.assertRaises(ValueError): subject.validate_cell(cell(value))

    def test_changed_number(self):
        c=cell();c['published_value']='2'
        with self.assertRaises(ValueError): subject.validate_cell(c)

    def test_current_domain_requires_legacy_carbs(self):
        p=dict(id='test',source_code='synthetic',observations=[dict(source_field=f,source_value=cell()) for f in subject.FIELDS])
        result=subject.probe_profile(p)
        self.assertEqual(['carbohydrates_g'],result['unsupported_legacy_fields'])
        self.assertFalse(result['database_write_attempted'])

    def test_current_domain_cannot_anchor_below_detection(self):
        p=dict(id='test',source_code='synthetic',observations=[dict(source_field=f,source_value=cell(None if f in ['protein_g','fat_g'] else '1')) for f in subject.FIELDS])
        self.assertEqual(['protein_g','fat_g','carbohydrates_g'],subject.probe_profile(p)['unsupported_legacy_fields'])

    def test_unrelated_domain_failure_is_not_macro_evidence(self):
        from app.domain.errors import DomainIssue, DomainIssueCode, DomainValidationError
        p=dict(id='test',source_code='synthetic',observations=[dict(source_field=f,source_value=cell()) for f in subject.FIELDS])
        error=DomainValidationError(DomainIssue(DomainIssueCode.INVALID_IDENTIFIER,'bad ID',field='id'))
        with patch.object(subject,'FoodNutritionProfile',side_effect=error):
            with self.assertRaises(DomainValidationError): subject.probe_profile(p)

    def test_refuse_repository_output(self):
        with self.assertRaisesRegex(ValueError,'outside public'): subject.write({},subject.ROOT/'data/test-private')

    def test_preserve_old_output(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'existing').write_text('keep')
            with self.assertRaisesRegex(ValueError,'empty'): subject.write({},p)
            self.assertEqual('keep',(p/'existing').read_text())

    def test_changed_input_fails_before_extraction(self):
        with patch.object(subject,'load',return_value={'inputs':[{'root':'corpus','path':'changed','sha256':'wrong'}]}):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);(p/'changed').write_text('new')
                with self.assertRaisesRegex(ValueError,'changed input'): subject.build(p)


if __name__=='__main__': unittest.main()
