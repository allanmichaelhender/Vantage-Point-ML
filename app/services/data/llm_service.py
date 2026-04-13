import os
import json
import httpx 
import google.generativeai as genai
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.player_state import PlayerState

class LLMService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.odds_key = os.getenv("THE_ODDS_API_KEY")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    # Class method to fetch top playesr
    async def get_elite_100(self, session: AsyncSession):
        six_months_ago = datetime.now() - timedelta(days=182)
        stmt = (
            select(
                PlayerState.player_id, PlayerState.player_name, PlayerState.current_elo
            )
            .where(
                PlayerState.last_match_date >= six_months_ago
            ) 
            .order_by(desc(PlayerState.current_elo))
            .limit(100)
        )
        result = await session.execute(stmt)
        rows = result.all()
        return [
            {"id": p.player_id, "name": p.player_name, "elo": p.current_elo}
            for p in rows
        ]

    async def get_raw_markets(self):
        api_key = self.odds_key.strip()
        base_url = "https://api.the-odds-api.com/v4/sports"

        async with httpx.AsyncClient() as client:

            # First we need to query all upcoming tournaments for all sports
            sports_resp = await client.get(base_url, params={"apiKey": api_key})
            all_sports = sports_resp.json()

            # We filter down to get the key (tournament name) for every upcoming atp tennis event
            active_keys = [
                s["key"]
                for s in all_sports
                if isinstance(s, dict)  # Defensive check
                and s.get("active") is True
                and s.get("group") == "Tennis"
                and s.get("description") == "Men's Singles"
            ]


            # Loop over the active keys/upcoming or ongoing tournaments to get Odds for each active key
            master_data = {"matches": []} # Initialising the data structure
            for sport_key in active_keys: # Loop over upcoming tournaments
                odds_url = f"{base_url}/{sport_key}/odds/"
                odds_params = {
                    "apiKey": api_key,
                    "regions": "eu,uk",
                    "bookmakers": "pinnacle,bet365,betfair_ex_uk",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                }

                odds_resp = await client.get(odds_url, params=odds_params)
                raw_matches = odds_resp.json() # Converts the response object into a dict

                for match in raw_matches:
                    # First we create the template for each match, to be appended later into our master data dict
                    entry = {
                        "p1": match["home_team"],
                        "p2": match["away_team"],
                        "tournament": match["sport_title"],
                        "commence_time": match["commence_time"],
                        "b365_p1": None,
                        "b365_p2": None,
                        "pin_p1": None,
                        "pin_p2": None,
                        "bf_p1": None,
                        "bf_p2": None,
                    }

                    # Loop over every bookie in the match datais
                    for bookie in match.get("bookmakers", []):
                        # For every bookie, we check if it matches our three and then rename with the mapping dict
                        prefix = {
                            "bet365": "b365",
                            "pinnacle": "pin",
                            "betfair_ex_uk": "bf",
                        }.get(bookie["key"])

                        if not prefix:
                            continue

                        # We use an generator expression and the next function to loop each betting option until we hit h2h, or return none
                        h2h = next(
                            (m for m in bookie["markets"] if m["key"] == "h2h"), None
                        )
                        if h2h:
                            for outcome in h2h["outcomes"]:
                                # Assign to p1 or p2 based on name match
                                side = "p1" if outcome["name"] == entry["p1"] else "p2"
                                entry[f"{prefix}_{side}"] = outcome["price"]

                    # Add to our master list
                    master_data["matches"].append(entry)

            return master_data

    async def sync_upcoming_matches(self, session: AsyncSession):
        elite_100 = await self.get_elite_100(session)
        match_data = await self.get_raw_markets()

  
        prompt = """
<task>
  You are a Tennis Data Quant. Cross-reference the <live_markets> against the <elite_player_db> to select the 6 most statistically significant matches.
</task>

<elite_player_db>
  {elite_db}
</elite_player_db>

<live_markets>
  {matches_and_markets}
</live_markets>

<matching_rules>
  1. Primary Key: Use fuzzy string matching to link names (e.g., "J. Sinner" = "Jannik Sinner").
  2. ID Injection: For every match, provide the 'p1_id' and 'p2_id' found in the <elite_player_db>.
  3. Null Handling: If a player in the market is NOT in the Top 100 DB, set their ID to null.
  4. Predict Surface: Return the surface for each match by looking at the tournament, choose from ["Hard", "Clay", "Grass"]
  5. 6 Matches: Only return 6 matches total.
</matching_rules>

<selection_priority>
  1. Priority 1: BOTH players have an ID in the Elite DB.
  2. Priority 2: BOTH players are Elite and has a high Elo (>1800).
  3. Priority 3: One players is Elite and has a high Elo (>1700).
</selection_priority>

<output_format>
  Return ONLY a valid JSON object. No preamble.
  {{
    "featured_matches": [
      {{
        "p1_name": "string",
        "p1_id": "string_or_null",
        "p2_name": "string",
        "p2_id": "string_or_null",
        "pin_p1": float,
        "pin_p2": float,
        "bf_p1": float,
        "bf_p2": float,
        "tournament": "string",
        "commence_time": "string",
        "surface": "string"
      }}
    ]
  }}
</output_format>

"""

        response = self.model.generate_content(
            prompt.format(
                elite_db=json.dumps(elite_100), # json.dumps converts python dict into a json string
                matches_and_markets=json.dumps(match_data),
            ),
            generation_config={"response_mime_type": "application/json"},
        )

        try:
            # Parse and return the structured data
            data = json.loads(response.text)
            return data.get("featured_matches", [])
        except Exception as e:
            print(f"❌ Gemini Parsing Error: {e}")
            return []


llmservice=LLMService()