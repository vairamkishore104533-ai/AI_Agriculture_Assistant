import os, sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

from services.weather_service import WeatherService
ws = WeatherService()

print("API Key loaded:", bool(ws.api_key))

result = ws.fetch_all("Madurai", "Melur")
if result.get("error"):
    print("ERROR:", result["error"])
else:
    daily = result.get("daily", [])
    print("Daily forecast count:", len(daily))
    for d in daily:
        print("  ", d["date"], "(", d["day_name"], ")", "High:", d["temp_max"], "Low:", d["temp_min"], "Rain:", d["rain"])
