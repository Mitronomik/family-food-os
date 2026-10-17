"""Unsupported operational placeholders must never report successful execution."""

from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]
PLACEHOLDERS = (
    "dev_start.sh",
    "start_local.sh",
    "dev_setup.sh",
    "create_backup.sh",
    "restore_backup.sh",
)


@pytest.mark.parametrize("script_name", PLACEHOLDERS)
def test_unsupported_operational_script_fails_closed(
    script_name: str, tmp_path: Path
) -> None:
    script = ROOT / "scripts" / script_name
    assert script.is_file()
    result = subprocess.run(
        ["bash", str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 78
    assert result.stdout == ""
    assert result.stderr == (
        f"ERROR: scripts/{script_name} is not implemented. "
        "No operation was performed.\n"
    )
    assert list(tmp_path.iterdir()) == []
