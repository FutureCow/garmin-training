from datetime import date
from pathlib import Path
from typing import Any

from pirate_garmin.client import GarminClient
from pirate_garmin.endpoints import render_endpoint, resolve_endpoint

from .config import settings


def get_garmin_client(username: str, password: str, user_id: int) -> GarminClient:
    """
    Create a pirate-garmin client with per-user token storage.

    Tokens are cached in GARMIN_TOKENS_DIR/{user_id}/ so each user has an
    isolated session. First-time login requires Playwright (browser-based auth).
    Subsequent calls reuse the cached tokens automatically.
    """
    app_dir = Path(settings.garmin_tokens_dir) / str(user_id)
    app_dir.mkdir(parents=True, exist_ok=True)
    return GarminClient.create(username=username, password=password, app_dir=app_dir)


async def fetch_training_data(client: GarminClient) -> dict[str, Any]:
    """
    Fetch all relevant training data from Garmin Connect.
    Returns a dict with activities, training status, sleep and readiness.
    Individual endpoint failures are captured as {"error": "..."} so a
    single unavailable endpoint does not abort the whole fetch.
    """
    profile = await client.get_profile_bundle()
    data: dict[str, Any] = {"display_name": profile.display_name}

    async def _fetch(key: str, endpoint_key: str, host: str, query: dict) -> None:
        try:
            endpoint = resolve_endpoint(endpoint_key)
            path, params = render_endpoint(
                endpoint,
                path_values={},
                query_values=query,
                profile=profile,
            )
            data[key] = await client.request_json(host, path, params)
        except Exception as exc:
            data[key] = {"error": str(exc)}

    # Recent activities (last 100 — covers roughly 3–6 months for most runners)
    await _fetch(
        "activities",
        "activities.search",
        "connectapi",
        {"start": "0", "limit": "100"},
    )

    # Training readiness score
    await _fetch("training_readiness", "training_readiness", "connectapi", {})

    # Training status: includes VO2max trend, training load, recovery time
    await _fetch("training_status", "training_status", "connectapi", {})

    # Sleep data for today
    await _fetch(
        "sleep",
        "sleep.daily",
        "services",
        {"date": date.today().isoformat()},
    )

    # Daily wellness summary (resting HR, stress, body battery)
    await _fetch(
        "daily_summary",
        "user_summary.daily",
        "connectapi",
        {"calendarDate": date.today().isoformat()},
    )

    return data
