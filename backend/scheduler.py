import json
import re

from anthropic import AsyncAnthropic

from .auth import decrypt_garmin_credentials
from .config import settings
from .garmin import fetch_training_data, get_garmin_client


async def generate_training_schedule(
    garmin_credentials_encrypted: str,
    preferences: dict,
    user_id: int,
) -> dict:
    """
    Fetch Garmin training data via pirate-garmin, then call Claude to generate
    a personalised training schedule and return it as a dict.
    """
    garmin_username, garmin_password = decrypt_garmin_credentials(garmin_credentials_encrypted)

    client = get_garmin_client(garmin_username, garmin_password, user_id)
    garmin_data = await fetch_training_data(client)

    system_prompt = _build_system_prompt(preferences, garmin_data)

    anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await anthropic_client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": "Genereer een trainingsschema op basis van mijn Garmin-data en voorkeuren.",
            }
        ],
    )

    if response.stop_reason == "max_tokens":
        raise ValueError("Claude overschreed max_tokens bij het genereren van het trainingsschema")

    for block in response.content:
        if hasattr(block, "text"):
            return _extract_json(block.text)

    raise ValueError("Claude gaf geen tekstblok terug in de response")


def _build_system_prompt(preferences: dict, garmin_data: dict) -> str:
    days_str = ", ".join(preferences.get("active_days") or [])
    distance = preferences.get("goal_distance") or "10K"
    if distance == "custom":
        distance = f"{preferences.get('goal_distance_km', '?')} km"

    garmin_context = json.dumps(garmin_data, ensure_ascii=False, indent=2)

    return f"""Je bent een professionele hardloopcoach. Maak een gepersonaliseerd trainingsschema.

TRAININGSVOORKEUREN VAN DE GEBRUIKER:
- Actieve trainingsdagen: {days_str}
- Dag voor de lange duurloop: {preferences.get("long_run_day") or "zondag"}
- Doelafstand: {distance}
- Doeltempo: {preferences.get("goal_pace") or "niet opgegeven"}
- Doeltijd: {preferences.get("goal_time") or "niet opgegeven"}
- Schematype: {preferences.get("schema_type") or "fixed"}
- Aantal weken: {preferences.get("schema_weeks") or 12}
- Startdatum: {preferences.get("start_date") or "zo snel mogelijk"}

GARMIN-DATA VAN DE GEBRUIKER:
{garmin_context}

INSTRUCTIES:
1. Analyseer de bovenstaande Garmin-data:
   - Activiteiten van de afgelopen maanden (volume, tempo, afstand)
   - VO2max trend en trainingsbelasting
   - Hersteltijden en slaapkwaliteit
   - Trainingsstatus en gereedheid
2. Schat het huidige niveau in (wekelijks volume, gemiddeld tempo, VO2max).
3. Genereer een schema dat ALLEEN trainingen plaatst op de opgegeven actieve trainingsdagen.
4. Elke trainingsdag krijgt een beschrijving die uitlegt WAAROM die training in het schema staat.
5. Geef het schema terug als JSON in dit exacte formaat — geen andere tekst:

{{
  "schema_type": "fixed",
  "niveau": "recreatief",
  "samenvatting": "Analyse van huidig niveau en aanpak in 2-3 zinnen.",
  "weken": [
    {{
      "week": 1,
      "dagen": [
        {{"dag": "maandag", "type": "rust"}},
        {{"dag": "dinsdag", "type": "interval", "afstand_km": 8, "beschrijving": "Uitleg..."}}
      ]
    }}
  ]
}}

Toegestane trainingstypes: rust, duurloop, interval, tempo, lange_duur, herstel
"""


def _extract_json(text: str) -> dict:
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude response bevat geen geldige JSON: {e}") from e
