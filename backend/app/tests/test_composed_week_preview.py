"""Working internal composed-week menu + Shopping v1b mobile preview.

Test against persisted MealPlan 0044 and exact source-pinned RecipeVersions;
the synthetic fixture is NOT a source-approved real family menu.
"""

import os
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

import pytest
from app.tests.persistence.test_meal_plan_composition_persistence import (
    _compose,
    _setup,
    _write,
)
from app.tests.persistence.test_meal_plan_full_week_composition import _week_21_42

from scripts.composed_week_preview import (
    SCHEMA,
    ComposedWeekPreviewBlocked,
    preview_from_database,
    render_html,
    write_preview_html,
)

CAPTURED = datetime(2026, 11, 16, 12, 0, tzinfo=UTC)


def _persist_composed_week(tmp_path):
    config, engine, home, people, old, recipes, selections = _setup(tmp_path)
    composed = _compose(old, people, recipes, selections)
    _write(engine, composed, people)
    return config, engine, home, composed


def test_composed_week_mobile_preview_uses_persisted_plan_and_exact_shopping(tmp_path):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        preview = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        assert preview["schema"] == SCHEMA
        assert preview["status"] == "DIAGNOSTIC_ONLY"
        assert preview["shopping_status"] == "COMPLETE"
        assert preview["price_status"] == "UNKNOWN"
        assert preview["physical_portions"] == "NOT_PROVEN"
        assert preview["nutrition"] == "NOT_ASSESSED"
        assert preview["prep_safety"] == "NOT_PROVEN"
        assert len(preview["days"]) == 7
        all_events = [e for day in preview["days"] for e in day["events"]]
        assert len(all_events) == 7
        multi = [e for e in all_events if e["source_kind"] == "COOK_COMPOSITION"]
        assert len(multi) == 1
        assert [c["course_ru"] for c in multi[0]["courses"]] == [
            "Первое",
            "Второе",
            "Десерт",
        ]
        assert [c["servings"][0]["factor"] for c in multi[0]["courses"]] == [
            "1.000000",
            "1.000000",
            "0.500000",
        ]
        assert len(preview["grocery"]) == 1
        # Source fixture has 25 g per recipe base serving; six legacy
        # 1.25 Servings plus composed (1 + 1 + 0.5) = exactly 250 g.
        assert preview["grocery"][0] == {
            "food_ru": "Картофель",
            "unit": "g",
            "required": "250.000",
            "at_home": "0.000",
            "to_buy": "250.000",
        }

        html = render_html(preview)
        assert html.startswith("<!doctype html><html lang='ru'>")
        for phrase in (
            "Первое",
            "Второе",
            "Десерт",
            "Купить",
            "250.000",
            "Только внутренняя демонстрация",
            "не масса готового блюда",
        ):
            assert phrase in html
        # Preview is read-only: no persisted ShoppingList is generated.
        with sqlite3.connect(config.path) as db:
            assert db.execute("SELECT COUNT(*) FROM shopping_lists").fetchone()[0] == 0
    finally:
        engine.dispose()


def test_composed_week_preview_is_reproducible_in_separate_python_process(tmp_path):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        expected = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        output = tmp_path / "composed-week.html"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.composed_week_preview",
                "--sqlite",
                str(config.path),
                "--household",
                str(home.id),
                "--plan",
                str(composed.plan.id),
                "--captured-at",
                CAPTURED.isoformat(),
                "--out",
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        assert output.read_text(encoding="utf-8") == render_html(expected)
        with sqlite3.connect(config.path) as db:
            assert db.execute("SELECT COUNT(*) FROM shopping_lists").fetchone()[0] == 0
    finally:
        engine.dispose()


def test_composed_week_preview_fails_closed_on_cross_household_and_bad_plan(tmp_path):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        for household_id, plan_id in (
            (uuid4(), composed.plan.id),
            (home.id, uuid4()),
        ):
            with pytest.raises(ComposedWeekPreviewBlocked):
                preview_from_database(
                    database_path=config.path,
                    household_id=household_id,
                    plan_id=plan_id,
                    captured_at=CAPTURED,
                )
    finally:
        engine.dispose()


def test_composed_week_preview_escapes_untrusted_source_display_and_denies_promotion(
    tmp_path,
):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        data = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        multi = next(
            event
            for day in data["days"]
            for event in day["events"]
            if event["source_kind"] == "COOK_COMPOSITION"
        )
        multi["courses"][0]["recipe_ru"] = "<script>alert('x')</script>"
        html = render_html(data)
        assert "&lt;script&gt;" in html
        assert "<script>" not in html

        data["status"] = "CONSUMER_READY"
        with pytest.raises(ComposedWeekPreviewBlocked):
            render_html(data)
    finally:
        engine.dispose()


def test_missing_sqlite_path_does_not_create_a_database(tmp_path):
    absent = tmp_path / "must-not-be-created.sqlite"
    with pytest.raises(ComposedWeekPreviewBlocked, match="не найдена"):
        preview_from_database(
            database_path=absent,
            household_id=uuid4(),
            plan_id=uuid4(),
            captured_at=CAPTURED,
        )
    assert not absent.exists()


def test_complete_21_event_three_member_composed_week_is_visible_without_phantom_meals(
    tmp_path,
):
    config, engine, home, people, old, recipes, selections = _week_21_42(tmp_path)
    try:
        # Only the first member is actually at home for Tuesday lunch;
        # the other two must not acquire invented composed portions.
        composed = _compose(old, people[:1], recipes, selections, target_index=4)
        _write(engine, composed, people)
        preview = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        assert len(preview["days"]) == 7
        assert [len(day["events"]) for day in preview["days"]] == [3] * 7
        events = [e for day in preview["days"] for e in day["events"]]
        assert len(events) == 21
        multi = [e for e in events if e["source_kind"] == "COOK_COMPOSITION"]
        assert len(multi) == 1
        composition_members = {
            s["member_id"] for part in multi[0]["courses"] for s in part["servings"]
        }
        assert composition_members == {str(people[0].id)}
        # Every original other course/attendance stays in the complete week.
        served = sum(
            len(course["servings"]) for event in events for course in event["courses"]
        )
        assert served == 44
        assert preview["grocery"][0]["required"] == "1343.750"
        assert preview["grocery"][0]["to_buy"] == "1343.750"
        assert "Первое" in render_html(preview)
        assert preview["physical_portions"] == "NOT_PROVEN"
    finally:
        engine.dispose()


def _run_cli(config, home, composed, out):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.composed_week_preview",
            "--sqlite",
            str(config.path),
            "--household",
            str(home.id),
            "--plan",
            str(composed.plan.id),
            "--captured-at",
            CAPTURED.isoformat(),
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize(
    "alias", ("same_path", "relative_alias", "symlink", "hardlink")
)
def test_cli_refuses_sqlite_output_alias_without_modifying_source(tmp_path, alias):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        source = config.path
        if alias == "same_path":
            output = source
        elif alias == "relative_alias":
            output = source.parent / "alias-directory" / ".." / source.name
            (source.parent / "alias-directory").mkdir()
        elif alias == "symlink":
            output = tmp_path / "linked.html"
            output.symlink_to(source)
        else:
            output = tmp_path / "hardlinked.html"
            os.link(source, output)

        before = sha256(source.read_bytes()).hexdigest()
        outcome = _run_cli(config, home, composed, output)
        assert outcome.returncode != 0
        assert "SQLite-базой" in outcome.stderr
        assert sha256(source.read_bytes()).hexdigest() == before
        with sqlite3.connect(source) as db:
            assert db.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert db.execute("SELECT COUNT(*) FROM shopping_lists").fetchone() == (0,)
        assert not tuple(source.parent.glob(".*.tmp"))
    finally:
        engine.dispose()


def test_atomic_html_publication_preserves_previous_file_on_replace_failure(
    tmp_path, monkeypatch
):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        preview = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        output = tmp_path / "week.html"
        output.write_text(render_html(preview), encoding="utf-8")
        original = output.read_bytes()
        database_before = sha256(config.path.read_bytes()).hexdigest()

        def fail_replace(_from, _to):
            raise OSError("simulated storage failure")

        monkeypatch.setattr("scripts.composed_week_preview.os.replace", fail_replace)
        with pytest.raises(ComposedWeekPreviewBlocked, match="атомарно"):
            write_preview_html(
                preview=preview, database_path=config.path, output_path=output
            )
        assert output.read_bytes() == original
        assert sha256(config.path.read_bytes()).hexdigest() == database_before
        assert not tuple(tmp_path.glob(".week.html.*.tmp"))
    finally:
        engine.dispose()


def test_atomic_writer_refuses_unrelated_existing_file_and_can_replace_own_html(
    tmp_path,
):
    config, engine, home, composed = _persist_composed_week(tmp_path)
    try:
        preview = preview_from_database(
            database_path=config.path,
            household_id=home.id,
            plan_id=composed.plan.id,
            captured_at=CAPTURED,
        )
        output = tmp_path / "week.html"
        output.write_text("do not replace this", encoding="utf-8")
        with pytest.raises(ComposedWeekPreviewBlocked, match="не являющийся"):
            write_preview_html(
                preview=preview, database_path=config.path, output_path=output
            )
        assert output.read_text(encoding="utf-8") == "do not replace this"

        output.unlink()
        write_preview_html(
            preview=preview, database_path=config.path, output_path=output
        )
        first = output.read_bytes()
        write_preview_html(
            preview=preview, database_path=config.path, output_path=output
        )
        assert output.read_bytes() == first
        assert not tuple(tmp_path.glob(".week.html.*.tmp"))
    finally:
        engine.dispose()
