import json
import re
from anthropic import AsyncAnthropic

from .auth import decrypt_garmin_credentials
from .config import settings
from .garmin import garmin_mcp_session


async def generate_training_schedule(
    garmin_credentials_encrypted: str,
    preferences: dict,
) -> dict:
    """
    Spawn the garmin-connect-mcp MCP server, call Claude with the MCP tools,
    and return the generated training schedule as a dict.
    """
    garmin_username, garmin_password = decrypt_garmin_credentials(garmin_credentials_encrypted)

    async with garmin_mcp_session(garmin_username, garmin_password) as session:
        tools_response = await session.list_tools()

        anthropic_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in tools_response.tools
        ]

        system_prompt = _build_system_prompt(preferences)
        messages = [
            {
                "role": "user",
                "content": "Genereer een trainingsschema op basis van mijn Garmin-data en voorkeuren.",
            }
        ]

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)

        MAX_ITERATIONS = 20
        iteration = 0

        while True:
            iteration += 1
            if iteration > MAX_ITERATIONS:
                raise ValueError(f"Claude did not finish within {MAX_ITERATIONS} tool-use iterations")

            response = await client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=system_prompt,
                tools=anthropic_tools,
                messages=messages,
            )

            if response.stop_reason == "max_tokens":
                raise ValueError("Claude exceeded max_tokens before completing the training schedule")

            if response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return _extract_json(block.text)
                raise ValueError("Claude returned end_turn but no text block was found")

            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            # Execute tool calls and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await session.call_tool(block.name, block.input)
                    result_text = (
                        result.content[0].text
                        if result.content
                        else ""
                    )
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

            if not tool_results:
                raise ValueError("Claude stopped with tool_use but emitted no tool_use blocks")
            messages.append({"role": "user", "content": tool_results})


def _build_system_prompt(preferences: dict) -> str:
    days_str = ", ".join(preferences.get("active_days") or [])
    distance = preferences.get("goal_distance") or "10K"
    if distance == "custom":
        distance = f"{preferences.get('goal_distance_km', '?')} km"

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

INSTRUCTIES:
1. Gebruik de beschikbare Garmin tools om de trainingsdata op te halen:
   - Activiteiten van de afgelopen 3-6 maanden
   - VO2max trend
   - Gemiddelde hartslagdata
   - Hersteltijden en slaapdata
2. Analyseer het huidige niveau (wekelijks volume, gemiddeld tempo, VO2max).
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
        raise ValueError(f"Claude response did not contain valid JSON: {e}") from e
