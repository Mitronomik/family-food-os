from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.config import DATABASE_PATH_ENV, DatabaseConfig
from app.db.migrations import apply_migrations
from app.main import create_app


@pytest.fixture
def household_api(monkeypatch, tmp_path):
    database_path = tmp_path / "household-api.sqlite"
    monkeypatch.setenv(DATABASE_PATH_ENV, str(database_path))
    apply_migrations(DatabaseConfig(path=database_path))
    with TestClient(create_app()) as client:
        yield client


def create_household(client, *, name="Family Home", timezone="Europe/Moscow"):
    response = client.post(
        "/api/households",
        json={
            "name": name,
            "timezone": timezone,
            "city": "Saint Petersburg",
            "default_weekly_budget": "12000.50",
            "default_cooking_profile": "easy_week",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def member_payload(name):
    return {
        "name": name,
        "birth_date": "1990-05-20",
        "sex": "female",
        "height_cm": "168.2",
        "weight_kg": "62.345",
        "activity_level": "moderate",
        "goal": "maintain",
    }


def test_complete_household_acceptance_path(household_api):
    client = household_api
    created = create_household(client)
    household_id = created["id"]

    members = []
    for name in ("Anna", "Sergey", "Child"):
        response = client.post(
            f"/api/households/{household_id}/members",
            json=member_payload(name),
        )
        assert response.status_code == 201, response.text
        members.append(response.json())

    household_update = client.patch(
        f"/api/households/{household_id}",
        json={
            "name": "Updated Family Home",
            "default_weekly_budget": "13500",
        },
    )
    assert household_update.status_code == 200

    member_update = client.patch(
        f"/api/households/{household_id}/members/{members[1]['id']}",
        json={"name": "Sergey Updated", "active": False, "weight_kg": None},
    )
    assert member_update.status_code == 200

    state_response = client.get(f"/api/households/{household_id}")
    members_response = client.get(f"/api/households/{household_id}/members")
    assert state_response.status_code == 200
    assert members_response.status_code == 200

    state = state_response.json()
    listed = members_response.json()["members"]
    assert state["id"] == household_id
    assert state["name"] == "Updated Family Home"
    assert state["default_weekly_budget"] == "13500.00"
    assert [member["id"] for member in state["members"]] == [
        member["id"] for member in listed
    ]
    assert {member["household_id"] for member in listed} == {household_id}
    assert len(listed) == 3
    updated = next(member for member in listed if member["id"] == members[1]["id"])
    assert updated["name"] == "Sergey Updated"
    assert updated["active"] is False
    assert updated["weight_kg"] is None


def test_invalid_timezone_returns_stable_validation_response(household_api):
    response = household_api.post(
        "/api/households",
        json={"name": "Home", "timezone": "Mars/Olympus_Mons"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_timezone"
    assert response.json()["detail"]["field"] == "timezone"


def test_missing_household_and_member_return_404(household_api):
    unknown_household = uuid4()
    get_response = household_api.get(f"/api/households/{unknown_household}")
    add_response = household_api.post(
        f"/api/households/{unknown_household}/members",
        json=member_payload("Anna"),
    )
    assert get_response.status_code == 404
    assert add_response.status_code == 404

    household = create_household(household_api)
    missing_member = household_api.patch(
        f"/api/households/{household['id']}/members/{uuid4()}",
        json={"active": False},
    )
    assert missing_member.status_code == 404
    assert missing_member.json()["detail"] == (
        "Household member was not found in this Household."
    )


def test_cross_household_member_mismatch_returns_404_without_data_leak(household_api):
    first = create_household(household_api, name="First")
    second = create_household(household_api, name="Second")
    member = household_api.post(
        f"/api/households/{first['id']}/members",
        json=member_payload("Anna"),
    ).json()

    wrong_scope = household_api.patch(
        f"/api/households/{second['id']}/members/{member['id']}",
        json={"name": "Leaked"},
    )

    assert wrong_scope.status_code == 404
    state = household_api.get(f"/api/households/{first['id']}").json()
    assert state["members"][0]["name"] == "Anna"


def test_unknown_fields_and_fake_owner_id_are_rejected(household_api):
    owner_response = household_api.post(
        "/api/households",
        json={
            "name": "Home",
            "timezone": "UTC",
            "owner_id": str(uuid4()),
        },
    )
    future_concept = household_api.post(
        "/api/households",
        json={
            "name": "Home",
            "timezone": "UTC",
            "excluded_ingredients": ["mushrooms"],
        },
    )

    assert owner_response.status_code == 422
    assert future_concept.status_code == 422
    assert owner_response.json()["detail"][0]["type"] == "extra_forbidden"


def test_float_money_and_measurements_are_rejected(household_api):
    money = household_api.post(
        "/api/households",
        json={
            "name": "Home",
            "timezone": "UTC",
            "default_weekly_budget": 10.5,
        },
    )
    household = create_household(household_api)
    measurement = household_api.post(
        f"/api/households/{household['id']}/members",
        json={**member_payload("Anna"), "weight_kg": 62.5},
    )

    assert money.status_code == 422
    assert measurement.status_code == 422


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity", "1E+999999"])
def test_malformed_budget_is_http_safe_validation(household_api, value):
    response = household_api.post(
        "/api/households",
        json={
            "name": "Home",
            "timezone": "UTC",
            "default_weekly_budget": value,
        },
    )

    assert response.status_code == 422


def test_negative_sub_cent_budget_is_rejected_before_rounding(household_api):
    response = household_api.post(
        "/api/households",
        json={
            "name": "Home",
            "timezone": "UTC",
            "default_weekly_budget": "-0.004",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "negative_money"
    assert response.json()["detail"]["value"] == "-0.004"


@pytest.mark.parametrize("field", ["height_cm", "weight_kg"])
@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_member_measurement_is_http_safe_validation(
    household_api, field, value
):
    household = create_household(household_api)

    response = household_api.post(
        f"/api/households/{household['id']}/members",
        json={**member_payload("Anna"), field: value},
    )

    assert response.status_code == 422


def test_existing_legacy_client_api_remains_available(household_api):
    response = household_api.get("/api/clients")

    assert response.status_code == 200
    assert response.json() == {"clients": []}


def test_no_unauthenticated_global_household_list_route_exists(household_api):
    response = household_api.get("/api/households")

    assert response.status_code == 405
