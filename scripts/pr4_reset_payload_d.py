#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/build_pr4_recipe_seed.py")
text = path.read_text(encoding="utf-8")
needle = '''        sources.append({
            "recipe_source_id": source_id,
            "source_name": SOURCE_NAME,
            "source_url": recipe["source_url"],
            "source_version": f"sha256:{source_hash}",
            "source_original_servings": recipe["source_servings"],
            "source_retrieved_at": source_retrieved_at,
            "source_document_sha256": source_hash,
'''
replacement = '''        sources.append({
            "recipe_source_id": source_id,
            "source_name": SOURCE_NAME,
            "source_url": recipe["source_url"],
            "source_version": f"sha256:{source_hash}",
            "source_original_servings": recipe["source_servings"],
            "source_retrieved_at": source_retrieved_at,
            "accepted_data2_sha256": source_hash,
            "source_document_sha256": source_hash,
'''
count = text.count(needle)
if count != 1:
    raise SystemExit(f"Expected exactly one source-manifest builder block, found {count}")
path.write_text(text.replace(needle, replacement), encoding="utf-8")
