"""Source-input annotations; no runtime publication or mutation of corpus v0.3."""
import argparse
import hashlib
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'data/curation/dc2-exact-input-mappings'
VERSION = 'dc2-exact-input-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def unique(items, key='id'):
    result = {r[key]: r for r in items}
    if len(result) != len(items):
        raise ValueError('duplicate ' + key)
    return result


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def build(corpus):
    lock = read(PACKAGE / 'input-lock.json')
    for item in lock['inputs']:
        path = (corpus if item['root'] == 'corpus' else ROOT) / item['path']
        if sha(path) != item['sha256']:
            raise ValueError('input checksum mismatch: ' + item['path'])
    foods = unique(rows(corpus / 'packages/recipe-closure/normalized/food-identities.jsonl'))
    bindings = unique(rows(corpus / 'packages/recipe-closure/normalized/ingredient-bindings.jsonl'))
    by_demand = unique([r['payload'] for r in bindings.values()], 'demand_id')
    pages = unique(rows(corpus / 'packages/school2022/extracted/pages.jsonl'))
    forms = read(PACKAGE / 'forms.json')
    candidates = unique(forms, 'book_candidate_id')
    exceptions = unique(read(PACKAGE / 'exceptions.json'), 'demand_id')
    prior = read(ROOT / 'data/curation/dc2-first-batch-review/generated/occurrence-reviews.json')
    output = []
    seen = set()
    for old in prior:
        matching = set(old['candidate_book_record_ids']) & candidates.keys()
        if old['source_id'] != 'ru-school2022' or not matching:
            continue
        if len(matching) != 1:
            raise ValueError('ambiguous form')
        form = candidates[matching.pop()]
        food = foods[old['id']]
        payload = food['payload']
        demand = payload['source_demand_id']
        binding = by_demand[demand]
        if binding['food_identity_id'] != food['id'] or binding['card_id'] != old['card_id']:
            raise ValueError('binding identity mismatch')
        quantity = binding['source_quantity']
        if quantity['unit'] != 'g' or quantity['unit_status'] != 'source_header_explicit':
            raise ValueError('unsupported mass basis')
        gross, net = Decimal(quantity['gross_mass_g']), Decimal(quantity['net_mass_g'])
        if not (gross.is_finite() and net.is_finite() and gross >= net >= 0):
            raise ValueError('invalid source mass')
        exception = exceptions.get(demand)
        flags = [exception['kind']] if exception else []
        if exception:
            seen.add(demand)
        if form['id'].endswith(':beet'):
            flags.append('peeling_after_heat_or_unspecified_physical_net_stage')
        if form['id'].endswith(':rice'):
            flags.append('hydration_and_drain_path_requires_recipe_specific_coefficients')
        process_pages = [old['locator']['pdf_page']]
        if old['card_id'] == 'ru-school2022:recipe:54-20м':
            process_pages.append(131)
        evidence_pages = sorted(set(form['evidence_pdf_pages'] + process_pages))
        output.append(dict(
            id=food['id'] + ':input-mapping:v1', food_identity_id=food['id'],
            demand_id=demand, card_id=old['card_id'], source_name=payload['source_name'],
            source_input_form_id=form['id'], source_identity_status='source_supported_review_proposal',
            book_candidate_id=form['book_candidate_id'], canonical_food_id=None,
            nutrient_equivalence_accepted=False, publication_ready=False,
            source_quantity=quantity,
            source_accounting_basis='standard_raw_material_consumption_gross_net',
            physical_net_weighing_stage='not_established_by_accounting_table',
            net_mass_semantics_override='normative_source_net_not_certified_physical_preheat_mass',
            retained_fraction_status='unknown', retained_fraction=None,
            additional_cold_loss_application_allowed=False,
            nutrient_calculation_ready=False,
            material_use_hold='suspected_source_duplicate_prefix' in flags,
            flags=flags, locator=old['locator'],
            preparation_context_sha256=payload['preparation_context_sha256'],
            full_process_sha256=hashlib.sha256(payload['preparation_context_source'].encode()).hexdigest(),
            evidence=[dict(page_id='ru-school2022:page:'+str(n),
                           record_sha256=hashlib.sha256(dumps(pages['ru-school2022:page:'+str(n)]).encode()).hexdigest()) for n in evidence_pages],
            transformation_version=VERSION))
    if seen != exceptions.keys():
        raise ValueError('exception target missing')
    counts = Counter(r['source_input_form_id'] for r in output)
    if counts != {f['id']: f['expected_occurrences'] for f in forms}:
        raise ValueError('scope coverage changed')
    unique(output)
    held = {r['food_identity_id'] for r in output if r['material_use_hold']}
    route_holds = []
    for route in rows(corpus / 'packages/recipe-closure/normalized/resolved-executions.jsonl'):
        affected = sorted({i['food_identity_id'] for i in route['payload']['ingredients']} & held)
        if affected:
            route_holds.append(dict(id=route['id'], affected_food_identity_ids=affected,
                                    material_execution_ready_override=False,
                                    reason='suspected_source_duplicate_prefix'))
    receipt = dict(lock=lock, transformation_version=VERSION,
                   builder_sha256=sha(Path(__file__)),
                   config_sha256={n: sha(PACKAGE/n) for n in ['forms.json','exceptions.json']})
    return {'mappings.json': sorted(output, key=lambda r:r['id']),
            'route-holds.json': sorted(route_holds, key=lambda r:r['id']),
            'input-receipt.json': receipt,
            'summary.json': dict(occurrences=len(output), by_form=dict(counts),
                                 source_table_hold_occurrences=len(held),
                                 affected_routes=len(route_holds),
                                 publication_ready=0, nutrient_calculation_ready=0)}


def write(result, output):
    output.mkdir(parents=True, exist_ok=True)
    for name, value in result.items():
        (output/name).write_text(dumps(value))
    (output/'checksums.json').write_text(dumps({n:sha(output/n) for n in sorted(result)}))


def validate_committed():
    output = PACKAGE/'generated'
    receipt = read(output/'input-receipt.json')
    if receipt['lock'] != read(PACKAGE/'input-lock.json') or receipt['builder_sha256'] != sha(Path(__file__)):
        raise ValueError('stale receipt')
    for name, value in receipt['config_sha256'].items():
        if value != sha(PACKAGE/name):
            raise ValueError('stale configuration')
    for item in receipt['lock']['inputs']:
        if item['root'] == 'repo' and sha(ROOT/item['path']) != item['sha256']:
            raise ValueError('changed repository input')
    checksums = read(output/'checksums.json')
    if set(checksums) != {'mappings.json', 'route-holds.json', 'input-receipt.json', 'summary.json'}:
        raise ValueError('invalid output manifest')
    for name, value in checksums.items():
        if value != sha(output/name):
            raise ValueError('output checksum mismatch')
    mappings = read(output/'mappings.json')
    unique(mappings)
    if any(r['publication_ready'] or r['nutrient_calculation_ready'] or r['canonical_food_id'] is not None or r['retained_fraction'] is not None for r in mappings):
        raise ValueError('unauthorized authority')
    prior = unique(read(ROOT/'data/curation/dc2-first-batch-review/generated/occurrence-reviews.json'))
    forms = unique(read(PACKAGE/'forms.json'))
    for r in mappings:
        old = prior[r['food_identity_id']]
        if (old['source_id'] != 'ru-school2022' or old['source_demand_id'] != r['demand_id']
                or old['card_id'] != r['card_id'] or old['locator'] != r['locator']
                or r['book_candidate_id'] != forms[r['source_input_form_id']]['book_candidate_id']
                or r['book_candidate_id'] not in old['candidate_book_record_ids']):
            raise ValueError('mapping crosswalk mismatch')
        if (r['additional_cold_loss_application_allowed']
                or r['physical_net_weighing_stage'] != 'not_established_by_accounting_table'
                or r['nutrient_equivalence_accepted']):
            raise ValueError('unsupported mass or nutrient assertion')
    exceptions = unique(read(PACKAGE/'exceptions.json'), 'demand_id')
    for r in mappings:
        e = exceptions.get(r['demand_id'])
        expected = bool(e and e['kind'] == 'suspected_source_duplicate_prefix')
        if r['material_use_hold'] != expected or (e and e['kind'] not in r['flags']):
            raise ValueError('lost exception')
    held = {r['food_identity_id'] for r in mappings if r['material_use_hold']}
    routes = read(output/'route-holds.json')
    unique(routes)
    route_index = {r['id']:r for r in rows(ROOT/'data/curation/corpus-v03-reconciliation/generated/route-index.jsonl')}
    expected_routes = []
    for route in route_index.values():
        affected = sorted(set(route['food_occurrence_ids']) & held)
        if affected:
            expected_routes.append(dict(id=route['id'], affected_food_identity_ids=affected,
                material_execution_ready_override=False, reason='suspected_source_duplicate_prefix'))
    if routes != sorted(expected_routes, key=lambda r:r['id']):
        raise ValueError('invalid route holds')
    counts = Counter(r['source_input_form_id'] for r in mappings)
    if read(output/'summary.json') != dict(occurrences=len(mappings), by_form=dict(counts),
            source_table_hold_occurrences=len(held), affected_routes=len(routes),
            publication_ready=0, nutrient_calculation_ready=0):
        raise ValueError('summary mismatch')
    counts = Counter(r['source_input_form_id'] for r in mappings)
    if counts != {f['id']:f['expected_occurrences'] for f in read(PACKAGE/'forms.json')}:
        raise ValueError('coverage mismatch')
    return mappings


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path)
    parser.add_argument('--output', type=Path, default=PACKAGE/'generated')
    parser.add_argument('--validate-committed', action='store_true')
    args = parser.parse_args()
    if args.validate_committed:
        print('Validated', len(validate_committed()), 'source-input mappings')
    elif args.corpus:
        write(build(args.corpus), args.output)
    else:
        parser.error('--corpus or --validate-committed is required')
