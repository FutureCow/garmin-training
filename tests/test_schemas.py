import pytest
from unittest.mock import AsyncMock, patch


MOCK_SCHEMA = {
    "schema_type": "fixed",
    "niveau": "recreatief",
    "samenvatting": "Test schema",
    "weken": [
        {
            "week": 1,
            "dagen": [
                {"dag": "dinsdag", "type": "duurloop", "afstand_km": 8, "beschrijving": "Test"},
                {"dag": "zondag", "type": "lange_duur", "afstand_km": 14, "beschrijving": "Test"},
            ],
        }
    ],
}


async def setup_user_with_prefs(client, auth_headers):
    await client.put(
        "/preferences/garmin-credentials",
        json={"garmin_username": "u", "garmin_password": "p"},
        headers=auth_headers,
    )
    await client.put(
        "/preferences",
        json={
            "active_days": ["dinsdag", "zondag"],
            "long_run_day": "zondag",
            "goal_distance": "10K",
            "goal_pace": None,
            "goal_time": None,
            "schema_type": "fixed",
            "schema_weeks": 8,
            "start_date": None,
            "goal_distance_km": None,
        },
        headers=auth_headers,
    )


@pytest.mark.asyncio
async def test_generate_schema(client, auth_headers):
    await setup_user_with_prefs(client, auth_headers)

    with patch(
        "backend.routes.schemas.generate_training_schedule",
        new_callable=AsyncMock,
        return_value=MOCK_SCHEMA,
    ):
        resp = await client.post("/schemas/generate", headers=auth_headers)

    assert resp.status_code == 201
    data = resp.json()
    assert data["schema_type"] == "fixed"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_and_get_active_schema(client, auth_headers):
    await setup_user_with_prefs(client, auth_headers)

    with patch(
        "backend.routes.schemas.generate_training_schedule",
        new_callable=AsyncMock,
        return_value=MOCK_SCHEMA,
    ):
        await client.post("/schemas/generate", headers=auth_headers)

    list_resp = await client.get("/schemas", headers=auth_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    active_resp = await client.get("/schemas/active", headers=auth_headers)
    assert active_resp.status_code == 200
    assert active_resp.json()["is_active"] is True


@pytest.mark.asyncio
async def test_generate_without_garmin_credentials(client, auth_headers):
    resp = await client.post("/schemas/generate", headers=auth_headers)
    assert resp.status_code == 400
