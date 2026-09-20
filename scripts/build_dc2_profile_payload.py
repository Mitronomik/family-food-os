"""Prepare five source-native profiles and probe current domain compatibility.

Numeric outputs belong outside the repository while source reuse is unresolved.
No database, seed, registry or runtime publication is modified.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT/'data/curation/dc2-first-profile-payload'
sys.path.insert(0, str(ROOT/'backend'))
from app.domain.food_ingredients import FoodNutritionProfile
from app.domain.errors import DomainValidationError

VERSION = 'dc2-profile-payload-v1'
FIELDS = {'energy_kcal','protein_g','fat_g','carbohydrates_g','fiber_g','ash_g',
          'water_g','organic_acids_g','starch_g','sugars_g','cholesterol_mg','saturated_fat_g'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def validate_cell(cell):
    state = cell['state']
    if state not in {'published_positive','below_detection','missing'}:
        raise ValueError('unreviewed value state')
    if state == 'published_positive':
        value = Decimal(cell['value'])
        if not value.is_finite() or value <= 0 or cell['value'] != cell['published_value']:
            raise ValueError('invalid published positive')
    elif cell['value'] is not None:
        raise ValueError('unknown is not a number')
    if state == 'below_detection' and (cell['published_value'] != '0' or cell['detection_limit'] is not None):
        raise ValueError('changed below-detection semantics')


def probe_profile(profile):
    """Use real domain validation with ephemeral UUID4-shaped IDs, not persisted IDs."""
    cells = {r['source_field']: r for r in profile['observations']}
    def amount(field):
        value = cells[field]['source_value']['value']
        return Decimal(value) if value is not None else None
    missing = [f for f in ['protein_g','fat_g'] if amount(f) is None]
    # Source-native carbohydrate is preserved but is not silently cast to legacy.
    missing.append('carbohydrates_g')
    now = datetime(2026, 9, 20, tzinfo=timezone.utc)
    try:
        FoodNutritionProfile(
            id=UUID('10000000-0000-4000-8000-000000000001'),
            food_ingredient_id=UUID('10000000-0000-4000-8000-000000000002'),
            basis_grams=Decimal('100'), kcal=amount('energy_kcal'),
            protein_g=amount('protein_g'), fat_g=amount('fat_g'),
            carbohydrates_g=None, fiber_g=amount('fiber_g'),
            source_name='SC-BOOK-2002', source_id=profile['source_code'],
            source_version='2002', source_data_type='published_compositional_profile',
            verified_at=now, estimated=None, is_current=False, created_at=now)
    except DomainValidationError as exc:
        if exc.issue.field not in missing or exc.issue.code.value != 'invalid_decimal':
            raise
        return dict(profile_id=profile['id'], status='rejected_by_current_domain',
                    unsupported_legacy_fields=missing, first_rejected_field=exc.issue.field,
                    domain_issue_code=exc.issue.code.value, database_write_attempted=False)
    raise ValueError('Domain contract changed: rerun explicit compatibility review')


def build(corpus):
    lock = load(PACKAGE/'input-lock.json')
    for item in lock['inputs']:
        path = (corpus if item['root']=='corpus' else ROOT)/item['path']
        if digest(path) != item['sha256']:
            raise ValueError('changed input: '+item['path'])
    source_rows = [json.loads(line) for line in (corpus/'packages/reference-profiles/normalized/profiles.jsonl').read_text().splitlines()]
    source = {r['source_code']:r for r in source_rows}
    if len(source) != len(source_rows):
        raise ValueError('duplicate source codes')
    output = []
    counts = Counter()
    for identity in load(PACKAGE/'identity-plan.json'):
        row = source[identity['book_source_code']]
        if row['basis_g'] != 100 or row['basis_part'] != 'edible' or set(row['values']) != FIELDS:
            raise ValueError('changed source basis or fields')
        observations = []
        for field, cell in sorted(row['values'].items()):
            validate_cell(cell)
            counts[cell['state']] += 1
            observations.append(dict(id=row['id']+':'+field, source_field=field,
                source_value=cell, canonical_nutrient_code=None,
                canonical_mapping_status='source_native_only_pending_component_review',
                method='unspecified_with_book_general_method' if field=='carbohydrates_g' else 'source_definition_reference',
                independently_measured=False, planner_usable=False))
        output.append(dict(id='dc2-profile-draft:'+row['source_code']+':v1',
            source_reference_id=row['id'], source_code=row['source_code'],
            source_name=row['source_name'], source_edition='2002', basis_g='100', basis_part='edible',
            identity_plan=identity, profile_uuid=None, provenance=row['provenance'],
            observations=observations, source_value_type=row['value_type'],
            rights_status='BLOCKED_PENDING_RIGHTS_REVIEW', publication_ready=False,
            transformation_version=VERSION))
    output.sort(key=lambda r:r['id'])
    probes = [probe_profile(r) for r in output]
    summary = dict(profiles=len(output), observations=sum(counts.values()),
                   source_states=dict(counts), required_source_fields_per_profile=6,
                   additional_reviewed_source_fields_per_profile=6,
                   canonical_numeric_values=0, imported_profiles=0,
                   domain_rejections=len(probes), rights_status='BLOCKED_PENDING_RIGHTS_REVIEW',
                   full_book_nutrient_coverage=False,
                   scope='all twelve fields in five reviewed reference profiles; additional book columns remain separate')
    return {'profiles.json':output,'domain-probe.json':probes,'summary.json':summary,
            'receipt.json':dict(input_lock=lock, builder_sha256=digest(Path(__file__)),
                                identity_plan_sha256=digest(PACKAGE/'identity-plan.json'),
                                transformation_version=VERSION)}


def write(result, directory):
    directory = directory.resolve()
    if directory == ROOT or ROOT in directory.parents:
        raise ValueError('numeric payload must remain outside public repository')
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('output directory must be empty; preserve previous packages')
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in result.items():
        (directory/name).write_text(encoded(value))
    (directory/'checksums.json').write_text(encoded({n:digest(directory/n) for n in sorted(result)}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args=parser.parse_args()
    result=build(args.corpus)
    write(result,args.output)
    print(encoded(result['summary.json']))
