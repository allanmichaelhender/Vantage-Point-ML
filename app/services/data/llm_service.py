import os
import json
import httpx  # For the-odds-api requests
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Database imports
from sqlalchemy import select, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

# Models (Make sure these match your actual file names)
from app.models.player_state import PlayerState


class LLMService:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.odds_key = os.getenv("THE_ODDS_API_KEY")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    async def get_elite_100(self, session: AsyncSession):
        """Fetch top 100 active players from Postgres"""
        one_year_ago = datetime.now() - timedelta(days=365)
        stmt = (
            select(
                PlayerState.player_id, PlayerState.player_name, PlayerState.current_elo
            )
            .where(
                PlayerState.last_match_date >= one_year_ago
            )  # Ensure your column name matches
            .order_by(desc(PlayerState.current_elo))
            .limit(100)
        )
        result = await session.execute(stmt)
        rows = result.all()
        # return [{"name": p.name, "id": p.id, "elo": p.elo} for p in result.scalars().all()]
        return [
            {"id": p.player_id, "name": p.player_name, "elo": p.current_elo}
            for p in rows
        ]

    async def get_raw_markets(self):
        api_key = self.odds_key.strip()
        # 🎯 FIX: Remove the trailing slash after 'sports'
        base_url = "https://api.the-odds-api.com/v4/sports"

        async with httpx.AsyncClient() as client:
            # print("🔍 Discovery: Finding active Tennis tournaments...")
            # Use params= for the apiKey to ensure it's encoded correctly
            sports_resp = await client.get(base_url, params={"apiKey": api_key})

            all_sports = sports_resp.json()

            # 🔍 DEBUG: See what we actually got
            if isinstance(all_sports, dict):
                # print(
                #     f"⚠️ API returned a Dictionary (likely Welcome message): {all_sports.get('message')}"
                # )
                return []

            # 2. FILTER: Active Men's Singles Tennis
            active_keys = [
                s["key"]
                for s in all_sports
                if isinstance(s, dict)  # Defensive check
                and s.get("active") is True
                and s.get("group") == "Tennis"
                and s.get("description") == "Men's Singles"
            ]

            # print(active_keys)

            # 3. LOOP: Get Odds for each active key
            master_data = {"matches": []}
            for sport_key in active_keys:
                odds_url = f"{base_url}/{sport_key}/odds/"
                odds_params = {
                    "apiKey": api_key,
                    "regions": "eu,uk",
                    "bookmakers": "pinnacle,bet365,betfair_ex_uk",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                }

                # print(f"   -> Fetching odds for {sport_key}...")
                odds_resp = await client.get(odds_url, params=odds_params)
                raw_matches = odds_resp.json()

                for match in raw_matches:
                    # 1. Create the flat entry
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

                    # 2. Pluck the odds from the bookies we care about
                    for bookie in match.get("bookmakers", []):
                        # Map key to our flat prefix
                        prefix = {
                            "bet365": "b365",
                            "pinnacle": "pin",
                            "betfair_ex_uk": "bf",
                        }.get(bookie["key"])

                        if not prefix:
                            continue

                        # Get the H2H market
                        h2h = next(
                            (m for m in bookie["markets"] if m["key"] == "h2h"), None
                        )
                        if h2h:
                            for outcome in h2h["outcomes"]:
                                # Assign to p1 or p2 based on name match
                                side = "p1" if outcome["name"] == entry["p1"] else "p2"
                                entry[f"{prefix}_{side}"] = outcome["price"]

                    # 3. Add to our master list
                    master_data["matches"].append(entry)

            return master_data

    async def sync_upcoming_matches(self, session: AsyncSession):
        elite_100 = await self.get_elite_100(session)
      #  match_data = await self.get_raw_markets()

  
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

        place_holder_matches = [{'p1_name': 'Ben Shelton', 'p1_id': 'S0S1', 'p2_name': 'Reilly Opelka', 'p2_id': 'O522', 'pin_p1': 1.42, 'pin_p2': 3.06, 'bf_p1': 2.28, 'bf_p2': 1.61, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-06T20:55:00Z'}, {'p1_name': 'Lorenzo Musetti', 'p1_id': 'M0EJ', 'p2_name': 'Marton Fucsovics', 'p2_id': 'F724', 'pin_p1': 1.67, 'pin_p2': 2.28, 'bf_p1': 1.52, 'bf_p2': 2.9, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-06T21:14:00Z'}, {'p1_name': 'Gael Monfils', 'p1_id': 'MC65', 'p2_name': 'Felix Auger-Aliassime', 'p2_id': 'AG37', 'pin_p1': 5.01, 'pin_p2': 1.21, 'bf_p1': 5.1, 'bf_p2': 1.24, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-06T22:00:00Z'}, {'p1_name': 'Jenson Brooksby', 'p1_id': 'B0CD', 'p2_name': 'Frances Tiafoe', 'p2_id': 'TD51', 'pin_p1': 1.96, 'pin_p2': 1.93, 'bf_p1': 1.97, 'bf_p2': 2.0, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-06T22:00:00Z'}, {'p1_name': 'Tomas Martin Etcheverry', 'p1_id': 'EA24', 'p2_name': 'Denis Shapovalov', 'p2_id': 'SU55', 'pin_p1': 2.65, 'pin_p2': 1.53, 'bf_p1': 2.72, 'bf_p2': 1.56, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-06T23:30:00Z'}, {'p1_name': 'Marcos Giron', 'p1_id': 'GC88', 'p2_name': 'Jakub Mensik', 'p2_id': 'M0NI', 'pin_p1': 3.27, 'pin_p2': 1.38, 'bf_p1': 3.5, 'bf_p2': 1.38, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T01:00:00Z'}, {'p1_name': 'Zizou Bergs', 'p1_id': 'BU13', 'p2_name': 'Tommy Paul', 'p2_id': 'PL56', 'pin_p1': 4.18, 'pin_p2': 1.27, 'bf_p1': 4.4, 'bf_p2': 1.27, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T03:30:00Z'}, {'p1_name': 'Daniil Medvedev', 'p1_id': 'MM58', 'p2_name': 'Alejandro Tabilo', 'p2_id': 'TE30', 'pin_p1': 1.26, 'pin_p2': 4.21, 'bf_p1': 1.27, 'bf_p2': 4.2, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Ugo Humbert', 'p1_id': 'HH26', 'p2_name': 'Alex Michelsen', 'p2_id': 'M0QI', 'pin_p1': 1.87, 'pin_p2': 2.0, 'bf_p1': 1.91, 'bf_p2': 2.02, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Sebastian Korda', 'p1_id': 'K0AH', 'p2_name': 'Alex de Minaur', 'p2_id': 'DH58', 'pin_p1': 2.39, 'pin_p2': 1.62, 'bf_p1': 2.4, 'bf_p2': 1.68, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Alexander Bublik', 'p1_id': 'BK92', 'p2_name': 'Vit Kopriva', 'p2_id': 'KI82', 'pin_p1': 1.28, 'pin_p2': 3.98, 'bf_p1': 1.29, 'bf_p2': 4.0, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Alexander Shevchenko', 'p1_id': 'S0H2', 'p2_name': 'Casper Ruud', 'p2_id': 'RH16', 'pin_p1': 4.82, 'pin_p2': 1.21, 'bf_p1': 4.8, 'bf_p2': 1.22, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Andrey Rublev', 'p1_id': 'RE44', 'p2_name': 'Gabriel Diallo', 'p2_id': 'D0F6', 'pin_p1': 1.4, 'pin_p2': 3.2, 'bf_p1': 1.4, 'bf_p2': 3.3, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Juan Manuel Cerundolo', 'p1_id': 'C0C8', 'p2_name': 'Arthur Rinderknech', 'p2_id': 'RC91', 'pin_p1': 2.79, 'pin_p2': 1.48, 'bf_p1': 2.82, 'bf_p2': 1.51, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Francisco Cerundolo', 'p1_id': 'C0AU', 'p2_name': 'Benjamin Bonzi', 'p2_id': 'BM95', 'pin_p1': 1.35, 'pin_p2': 3.42, 'bf_p1': 1.38, 'bf_p2': 3.4, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Carlos Alcaraz', 'p1_id': 'A0E2', 'p2_name': 'Grigor Dimitrov', 'p2_id': 'D875', 'pin_p1': 1.04, 'pin_p2': 16.02, 'bf_p1': 1.04, 'bf_p2': 21.0, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Roberto Bautista Agut', 'p1_id': 'BD06', 'p2_name': 'Jack Draper', 'p2_id': 'D0CO', 'pin_p1': 6.36, 'pin_p2': 1.14, 'bf_p1': 6.6, 'bf_p2': 1.15, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Sebastian Baez', 'p1_id': 'B0BI', 'p2_name': 'Jiri Lehecka', 'p2_id': 'L0BV', 'pin_p1': 3.32, 'pin_p2': 1.36, 'bf_p1': 3.35, 'bf_p2': 1.41, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Karen Khachanov', 'p1_id': 'KE29', 'p2_name': 'Joao Fonseca', 'p2_id': 'F0FV', 'pin_p1': 2.29, 'pin_p2': 1.69, 'bf_p1': 2.3, 'bf_p2': 1.73, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}, {'p1_name': 'Novak Djokovic', 'p1_id': 'D643', 'p2_name': 'Kamil Majchrzak', 'p2_id': 'MQ75', 'pin_p1': 1.1, 'pin_p2': 8.41, 'bf_p1': 1.12, 'bf_p2': 8.2, 'tournament': 'ATP Indian Wells', 'commence_time': '2026-03-07T19:00:00Z'}]

        response = self.model.generate_content(
            prompt.format(
                elite_db=json.dumps(elite_100),
                matches_and_markets=json.dumps(place_holder_matches),
            ),
            generation_config={"response_mime_type": "application/json"},
        )

        try:
            # 3. Parse and return the structured data
            data = json.loads(response.text)
            # print(data.get("featured_matches", []))
            return data.get("featured_matches", [])
        except Exception as e:
            print(f"❌ Gemini Parsing Error: {e}")
            return []
