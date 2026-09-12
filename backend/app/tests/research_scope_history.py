"""Exercise old per-PR scope guards on their exact accepted research trees.

Content/provenance tests still inspect current artifacts. Frozen scope guards
must not treat later explicitly authorized schema changes as research changes.
"""

import importlib.util
from pathlib import Path
import subprocess


def load_accepted_validator(root: Path, destination: Path, revision: str, script: str):
    subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            str(root),
            str(destination),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "checkout", "--quiet", "--detach", revision],
        cwd=destination,
        check=True,
        capture_output=True,
    )
    spec = importlib.util.spec_from_file_location(
        "accepted_scope_validator", destination / "scripts" / script
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
