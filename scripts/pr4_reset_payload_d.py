#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/build_pr4_recipe_seed.py")
text = path.read_text(encoding="utf-8")
needle = '''            "recipe_source_id": source_id,
            "source_name": SOURCE_NAME,
            "source_url": source_url,
            "source_version": source_version,
            "source_document_sha256": source_hash,
'''
replacement = '''            "recipe_source_id": source_id,
            "source_name": SOURCE_NAME,
            "source_url": source_url,
            "source_version": source_version,
            "accepted_data2_sha256": source_hash,
            "source_document_sha256": source_hash,
'''
if needle not in text:
    raise SystemExit("Expected source-manifest builder block not found")
if text.count(needle) != 1:
    raise SystemExit(f"Expected exactly one source-manifest builder block, found {text.count(needle)}")
path.write_text(text.replace(needle, replacement), encoding="utf-8")
