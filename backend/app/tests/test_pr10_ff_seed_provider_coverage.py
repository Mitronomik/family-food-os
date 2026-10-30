"""Static guard for all 12 trusted seed modules / 22 composer sites."""

import ast
from pathlib import Path

SEED = Path(__file__).resolve().parents[1] / "seed"

SITES = {
    "r1f_prepared_output.py": 1,
    "r1h_school2022_main.py": 1,
    "r2_breakfast_capacity.py": 1,
    "r2b_fish_main_diversity.py": 1,
    "r2c_breakfast_grain_diversity.py": 1,
    "r2e_cottage_casserole.py": 1,
    "r2f_cheese_sandwich.py": 1,
    "r3a_school2022_main_batch.py": 3,
    "r3b_school2022_breakfast_batch.py": 3,
    "r3c_school2022_main_batch.py": 4,
    "r3d_final_dc3_batch.py": 4,
    "dc4_a3_russian_step_corrections.py": 1,
}


def test_entire_accepted_12_module_22_composer_inventory_is_present():
    assert len(SITES) == 12
    assert sum(SITES.values()) == 22
    for name, count in SITES.items():
        tree = ast.parse((SEED / name).read_text(encoding="utf-8"))
        sites = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "create_food_recipe_catalogue_service"
        ]
        assert len(sites) == count, name
        for call in sites:
            surrounding = next((
                node for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.lineno <= call.lineno <= node.end_lineno
                and not any(
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and child is not node
                    and child.lineno <= call.lineno <= child.end_lineno
                    for child in ast.walk(node)
                )
            ), None)
            assert surrounding is not None
            if name == "r3c_school2022_main_batch.py" and (
                surrounding.name == "_ensure_prerequisite_batch"
            ):
                # This one read-only availability probe intentionally retains
                # ordinary composer with no allocatable Recipe ID.
                assert len(call.keywords) == 0
            else:
                assert any(k.arg is None for k in call.keywords), (
                    name, surrounding.name, call.lineno
                )


def test_every_seed_entrypoint_is_opt_in_only():
    for name in SITES:
        tree = ast.parse((SEED / name).read_text(encoding="utf-8"))
        for fn in tree.body:
            if not isinstance(fn, ast.FunctionDef):
                continue
            if fn.name.startswith(("seed_r", "publish_r", "activate_r")) or (
                fn.name == "seed_dc4_a3_russian_step_corrections"
            ):
                assert "id_provider" in [a.arg for a in fn.args.kwonlyargs], (
                    name, fn.name
                )
                assert fn.args.kw_defaults[-1] is not None, (name, fn.name)
        assert not any(
            isinstance(n, ast.ImportFrom)
            and n.module in {"app.domain.planner", "app.services.planner"}
            and any(alias.name == "uuid4" for alias in n.names)
            for n in ast.walk(tree)
        )
