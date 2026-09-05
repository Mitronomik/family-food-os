#!/usr/bin/env python3
from pathlib import Path

path = Path("scripts/build_pr4_recipe_seed.py")
text = path.read_text(encoding="utf-8")
if text.startswith("#!/usr/bin/env python3\n"):
    text = text.removeprefix("#!/usr/bin/env python3\n")
text = text.replace(
    'raise ValueError(f"Expected object in {path}")',
    'raise TypeError(f"Expected object in {path}")',
)
path.write_text(text, encoding="utf-8")
