import pytest


@pytest.mark.asyncio
async def test_get_preferences_not_found(client, auth_headers):
    resp = await client.get("/preferences", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_set_and_get_preferences(client, auth_headers):
    body = {
        "active_days": ["dinsdag", "donderdag", "zondag"],
        "long_run_day": "zondag",
        "goal_distance": "10K",
        "goal_pace": "5:30",
        "goal_time": None,
        "schema_type": "fixed",
        "schema_weeks": 10,
        "start_date": "2026-04-07",
        "goal_distance_km": None,
    }
    put_resp = await client.put("/preferences", json=body, headers=auth_headers)
    assert put_resp.status_code == 200

    get_resp = await client.get("/preferences", headers=auth_headers)
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["active_days"] == ["dinsdag", "donderdag", "zondag"]
    assert data["long_run_day"] == "zondag"


@pytest.mark.asyncio
async def test_garmin_credentials(client, auth_headers):
    status_before = await client.get("/preferences/garmin-status", headers=auth_headers)
    assert status_before.json()["connected"] is False

    put_resp = await client.put(
        "/preferences/garmin-credentials",
        json={"garmin_username": "garmin@example.com", "garmin_password": "garminpass"},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["connected"] is True

    delete_resp = await client.delete("/preferences/garmin-credentials", headers=auth_headers)
    assert delete_resp.json()["connected"] is False
