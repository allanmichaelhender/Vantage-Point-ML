import os
import json
import google.generativeai as genai
from datetime import datetime


class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        # Standard config (remove the client_options part)
        genai.configure(api_key=api_key)
        
        # 1. Use the FULL model path (this often triggers the correct routing)
        # 2. Define the tool explicitly
        self.model = genai.GenerativeModel(
            model_name='models/gemini-2.0-flash',
            tools=[{'google_search_retrieval': {}}]
        )

    async def sync_upcoming_matches(self):
        # The prompt with strict XML instructions
        prompt = f"""
        <context>
        Today is {datetime.now().strftime("%A, %d %B %Y")}. 
        You are a professional tennis data aggregator.
        </context>

        <task>
        Search the web for the top 20 upcoming mens ATP singles matches scheduled within the next 72 hours.
        Target tournaments: Current or soon to be starting ATP events.
        </task>

        <data_requirements>
        For each match, extract:
        1. Full Player Names (e.g., 'Jannik Sinner', 'Carlos Alcaraz').
        2. Match Date and Time (UTC).
        3. Tournament name, Surface (Hard, Clay, or Grass), and Round (e.g., R64, R32, SF).
        4. Current Decimal Odds from exactly two bookmakers: BET365 and PINNACLE.
        </data_requirements>

        <constraints>
        - Return EXACTLY 20 matches.
        - Prioritize matches involving seeded players or high-rank matchups.
        - Output ONLY a valid JSON object.
        </constraints>

        <output_format>
        {{
          "matches": [
            {{
              "p1_name": "string",
              "p2_name": "string",
              "match_date": "YYYY-MM-DD HH:MM:SS",
              "tournament": "string",
              "surface": "string",
              "round": "string",
              "b365_p1": float,
              "b365_p2": float,
              "pin_p1": float,
              "pin_p2": float
            }}
          ]
        }}
        </output_format>
        """

        response = self.model.generate_content(prompt)

        # Clean the response (Gemini sometimes wraps JSON in ```json blocks)
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
