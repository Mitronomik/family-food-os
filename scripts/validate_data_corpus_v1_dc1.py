#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

EXPECTED_CANDIDATES = 68
EXPECTED_RELATIONSHIPS = 991
EXPECTED_DEMANDS = 96
EXPECTED_EXISTING = 33
EXPECTED_DC2_REQUIRED = 63
EXPECTED_PR39_CANDIDATES = 350
EXPECTED_PR39_MAPPINGS = 363
EXPECTED_PRODUCTION_NUTRITION_ROWS = 183
EXPECTED_SAFE_SIMPLE = 5
EXPECTED_REVIEW_REQUIRED = 63


def fail(msg: str) -> None:
    raise SystemExit(f"DC1 PACKAGE VALIDATION ERROR: {msg}")


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str,str]]:
    with path.open(encoding='utf-8-sig',newline='') as f:
        return [{k:(v or '') for k,v in r.items()} for r in csv.DictReader(f)]


def dec(value: str, ctx: str) -> Decimal:
    try: d=Decimal(value)
    except (InvalidOperation,ValueError): fail(f"invalid Decimal {ctx}: {value!r}")
    if not d.is_finite(): fail(f"non-finite Decimal {ctx}: {value!r}")
    return d


def split_ids(value: str) -> set[str]:
    return {v.strip() for v in value.split('|') if v.strip()}


def validate(pkg: Path, *, check_checksums: bool=True) -> dict[str,int]:
    required=[
        'candidate-recipes.csv','food-demand.csv','compatibility.csv',
        'batch-plan.json','source-artifacts.json','summary.json','README.md'
    ]
    for n in required:
        if not (pkg/n).exists(): fail(f"missing package file {n}")

    candidates=read_csv(pkg/'candidate-recipes.csv')
    demands=read_csv(pkg/'food-demand.csv')
    compat=read_csv(pkg/'compatibility.csv')
    relationship_parts=sorted(pkg.glob('source-relationships-part*.csv'))
    if len(relationship_parts)!=4: fail(f'expected 4 source relationship shards, got {len(relationship_parts)}')
    rels=[]
    for part in relationship_parts: rels.extend(read_csv(part))
    summary=json.loads((pkg/'summary.json').read_text(encoding='utf-8'))
    plan=json.loads((pkg/'batch-plan.json').read_text(encoding='utf-8'))
    artifacts=json.loads((pkg/'source-artifacts.json').read_text(encoding='utf-8'))

    if len(candidates)!=EXPECTED_CANDIDATES: fail(f"candidate count: {len(candidates)}")
    if len(rels)!=EXPECTED_RELATIONSHIPS: fail(f"relationship count: {len(rels)}")
    if len(demands)!=EXPECTED_DEMANDS: fail(f"demand count: {len(demands)}")
    if len(compat)!=EXPECTED_CANDIDATES: fail(f"compatibility count: {len(compat)}")

    cids=[r['source_recipe_id'] for r in candidates]
    if len(set(cids))!=len(cids): fail('duplicate candidate IDs')
    dids=[r['external_ingredient_id'] for r in demands]
    if len(set(dids))!=len(dids): fail('duplicate food-demand external IDs')
    compat_ids=[r['source_recipe_id'] for r in compat]
    if set(compat_ids)!=set(cids) or len(set(compat_ids))!=len(compat_ids): fail('compatibility candidate IDs mismatch')

    rel_by_recipe=defaultdict(list)
    rel_keys=set()
    for r in rels:
        rid=r['source_recipe_id']; iid=r['resolved_ingredient_id']
        if rid not in set(cids): fail(f"relationship references unknown candidate {rid}")
        if iid not in set(dids): fail(f"relationship references unknown demand ID {iid}")
        amount=dec(r['amount_g'],f"{rid}/{iid}/amount_g")
        if amount<=0: fail(f"unknown/invalid amount substituted by zero/non-positive for {rid}/{iid}")
        key=tuple(r[k] for k in ['relationship_source','source_recipe_id','variant','original_ingredient_id','resolved_ingredient_id','original_ingredient','amount_g','amount_status','choice_group','optional','relationship_source_url','nutrient_input_eligible'])
        if key in rel_keys: fail(f"duplicate relationship row {key}")
        rel_keys.add(key); rel_by_recipe[rid].append(r)

    for c in candidates:
        rid=c['source_recipe_id']; actual=rel_by_recipe.get(rid,[])
        if not actual: fail(f"candidate {rid} lost all source relationships")
        if int(c['source_relationship_rows_v22_5'])!=len(actual): fail(f"candidate {rid} relationship summary mismatch")
        if int(c['source_relationship_rows_v22_5'])<=0 or int(c['source_calc_rows_v22_13'])<=0: fail(f"candidate {rid} has zero relationship/calc rows")
        if c['production_ready']!='NO': fail(f"candidate {rid} incorrectly marked production-ready")
        if c['variant_selection_status']=='SIMPLE_SOURCE_BRANCH_CANDIDATE':
            if int(c['source_variant_count'])!=1 or c['choice_groups'] or int(c['optional_row_count'])!=0 or c['boundary_review_reasons']:
                fail(f"candidate {rid} assigned simple status with unresolved source-structure alternative/boundary")
            if c['relationship_compatibility_status']!='CALC_ROWS_MATCH_RELATIONSHIP_ROWS_MATCH':
                fail(f"candidate {rid} assigned simple status with unresolved relationship compatibility")
            if c['semantic_label_review_ids']:
                fail(f"candidate {rid} assigned simple status with semantic-label debt")
        elif c['variant_selection_status']!='REVIEW_REQUIRED':
            fail(f"candidate {rid} unknown variant-selection status")
        if c['variant_selection_status']=='REVIEW_REQUIRED' and c['proposed_dc3_batch']!='DC3-C_REVIEW_REQUIRED':
            fail(f"candidate {rid} review-required status escaped review batch")
        if int(c['source_variant_count'])>1 and c['single_variant_required_ids']:
            fail(f"candidate {rid} has selected-variant dependencies despite unresolved multi-variant state")

    existing=sum(r['map_state'] in {'EXACT_EXISTING','ALIAS_EXISTING'} for r in demands)
    dc2=sum(r['map_state'] in {'NEW_FOOD_CANDIDATE','FORM_SPLIT_CANDIDATE'} for r in demands)
    if existing!=EXPECTED_EXISTING or dc2!=EXPECTED_DC2_REQUIRED: fail(f"mapping split drift {existing}/{dc2}")
    if any(r['production_ready']!='NO' for r in demands): fail('food demand marked production-ready')
    for r in demands:
        state=r['map_state']
        assignment=r.get('authority_assignment_status','')
        if not assignment: fail(f"food demand {r['external_ingredient_id']} missing authority assignment status")
        if state in {'EXACT_EXISTING','ALIAS_EXISTING'}:
            if r['current_profile_presence_status']!='PRESENT_IN_REQUIRED_PRODUCTION_SEED':
                fail(f"existing mapping {r['external_ingredient_id']} lacks required production profile")
            if r['profile_suitability_for_recipe_form']!='PROFILE_PRESENT_FORM_REVIEW_REQUIRED':
                fail(f"existing mapping {r['external_ingredient_id']} profile/form status is not review-required")
            if not r['authority_source_candidate'] or not r['authority_record_candidate']:
                fail(f"existing mapping {r['external_ingredient_id']} lacks exact current profile provenance")
            if r['proposed_dc2_batch']!='REUSE_EXISTING_PROFILE_FORM_REVIEW':
                fail(f"existing mapping {r['external_ingredient_id']} prematurely bypasses profile/form review")
        else:
            if assignment.startswith('BLOCKED_'):
                if r['authority_source_candidate'] or r['authority_record_candidate']:
                    fail(f"blocked demand {r['external_ingredient_id']} carries premature authority record")
            elif assignment=='CANDIDATE_SOURCE_FAMILY_IDENTIFIED_EXACT_RECORD_UNPINNED':
                if not r['authority_source_candidate'] or r['authority_record_candidate']:
                    fail(f"candidate-family assignment malformed for {r['external_ingredient_id']}")
            else:
                fail(f"unexpected authority assignment status for {r['external_ingredient_id']}: {assignment}")
    if any(r['proposed_dc2_batch']=='REUSE_NO_DC2_WRITE' for r in demands):
        fail('legacy REUSE_NO_DC2_WRITE is forbidden before exact profile/form review')

    # Summary must be derived/reconcilable with serialized facts.
    cs=summary['candidate_selection']; fs=summary['food_demand']
    expected_summary={
        'candidate_count':len(candidates),
        'relationship_count':len(rels),
        'demand_count':len(demands),
        'existing':existing,
        'dc2':dc2,
        'one_variant':sum(int(r['source_variant_count'])==1 for r in candidates),
        'multi_variant':sum(int(r['source_variant_count'])>1 for r in candidates),
        'simple':sum(r['variant_selection_status']=='SIMPLE_SOURCE_BRANCH_CANDIDATE' for r in candidates),
        'review':sum(r['variant_selection_status']=='REVIEW_REQUIRED' for r in candidates),
    }
    actual_summary={
        'candidate_count':cs['recipe_family_count'],
        'relationship_count':cs['source_relationship_rows_v22_5'],
        'demand_count':fs['demand_row_count'],
        'existing':fs['accepted_existing_identity_mapping_count'],
        'dc2':fs['dc2_required_identity_count'],
        'one_variant':cs['source_variant_structure']['one_source_variant'],
        'multi_variant':cs['source_variant_structure']['multiple_source_variants'],
        'simple':cs['source_variant_structure']['safe_simple_source_branch_candidate'],
        'review':cs['source_variant_structure']['review_required'],
    }
    if expected_summary!=actual_summary: fail(f"summary mismatch expected={expected_summary} actual={actual_summary}")
    if expected_summary['simple']!=EXPECTED_SAFE_SIMPLE or expected_summary['review']!=EXPECTED_REVIEW_REQUIRED:
        fail(f"safe branch split drift {expected_summary['simple']}/{expected_summary['review']}")

    repo_meta=artifacts.get('repository',{})
    loaded=repo_meta.get('mapping_rows_loaded',{})
    if loaded.get('candidate_rows_total_from_full_pr39_package')!=EXPECTED_PR39_CANDIDATES:
        fail('source-artifacts does not prove full 350-row PR39 candidate input')
    if loaded.get('ingredient_mapping_rows_total_from_full_pr39_package')!=EXPECTED_PR39_MAPPINGS:
        fail('source-artifacts does not prove full 363-row PR39 mapping input')
    nutrition_meta=artifacts.get('production_nutrition_seed',{})
    if nutrition_meta.get('row_count')!=EXPECTED_PRODUCTION_NUTRITION_ROWS:
        fail('source-artifacts production nutrition row count mismatch')
    if nutrition_meta.get('relevant_existing_profiles_identified')!=EXPECTED_EXISTING:
        fail('source-artifacts does not prove current profiles for all 33 existing mappings')
    if not nutrition_meta.get('git_blob_sha1'):
        fail('source-artifacts missing production nutrition seed blob identity')

    # Batches must partition exactly once.
    for section, universe, field, listkey in [
        ('dc2',set(dids),'external_ingredient_id','external_ingredient_ids'),
        ('dc3',set(cids),'source_recipe_id','source_recipe_ids'),
    ]:
        flat=[]
        for name,group in plan[section].items():
            if group['count']!=len(group[listkey]): fail(f"{section}/{name} declared count mismatch")
            flat.extend(group[listkey])
        if set(flat)!=universe: fail(f"{section} batches omit or add IDs")
        dup=[k for k,n in Counter(flat).items() if n!=1]
        if dup: fail(f"{section} batches overlap: {dup}")

    if check_checksums:
        cfile=pkg/'checksums.sha256'
        if not cfile.exists(): fail('missing checksums.sha256')
        for line in cfile.read_text(encoding='utf-8').splitlines():
            if not line.strip(): continue
            digest,name=line.split('  ',1)
            if not (pkg/name).exists(): fail(f"checksum target missing {name}")
            if sha256(pkg/name)!=digest: fail(f"checksum mismatch {name}")

    return expected_summary


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('package')
    ap.add_argument('--skip-checksums',action='store_true',help='for adversarial mutation tests only')
    args=ap.parse_args()
    result=validate(Path(args.package),check_checksums=not args.skip_checksums)
    print(json.dumps({'status':'PASS',**result},indent=2,sort_keys=True))

if __name__=='__main__': main()
