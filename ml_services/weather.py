"""
CityPulse-X Weather Service — OpenWeatherMap API client with caching.
"""

import os
import time
import httpx

OWM_API_KEY = os.getenv("OWM_API_KEY", "")
WEATHER_CITY = os.getenv("DEFAULT_CITY", "Patna")

WEATHER_CACHE = {
    "condition": "clear", "temp": 0, "feels_like": 0, "humidity": 0,
    "wind_speed": 0, "description": "clear sky", "icon": "01d",
    "city": WEATHER_CITY, "last_fetch": 0
}
WEATHER_FETCH_INTERVAL = 60  # seconds


def _map_owm_to_citypulse(weather_id, sunrise, sunset, dt):
    """Map OpenWeatherMap condition ID to CityPulse weather category."""
    is_night = dt < sunrise or dt > sunset
    if is_night:
        return "night"
    if 200 <= weather_id <= 531:  # Thunderstorm, Drizzle, Rain
        return "rain"
    if 600 <= weather_id <= 622:  # Snow
        return "fog"
    if weather_id == 741:  # Fog
        return "fog"
    if 701 <= weather_id <= 771:  # Mist, Smoke, Haze, Dust, Sand
        return "haze"
    return "clear"


async def fetch_weather_from_api():
    """Fetch current weather from OpenWeatherMap. Caches for 60s. Falls back to clear."""
    global WEATHER_CACHE
    now = time.time()
    if now - WEATHER_CACHE["last_fetch"] < WEATHER_FETCH_INTERVAL:
        return WEATHER_CACHE
    if not OWM_API_KEY:
        print("PY-LOG: No OWM API key set. Defaulting to clear.")
        WEATHER_CACHE["last_fetch"] = now
        return WEATHER_CACHE
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={WEATHER_CITY}&appid={OWM_API_KEY}&units=metric"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"PY-LOG: OWM API error {resp.status_code}. Keeping last known weather.")
                WEATHER_CACHE["last_fetch"] = now
                return WEATHER_CACHE
            data = resp.json()
        w = data["weather"][0]
        sys_data = data.get("sys", {})
        sunrise = sys_data.get("sunrise", 0)
        sunset = sys_data.get("sunset", 0)
        dt = data.get("dt", 0)
        condition = _map_owm_to_citypulse(w["id"], sunrise, sunset, dt)
        WEATHER_CACHE = {
            "condition": condition,
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "description": w["description"],
            "icon": w["icon"],
            "city": data.get("name", WEATHER_CITY),
            "visibility": data.get("visibility", 10000),
            "last_fetch": now
        }
        print(f"PY-LOG: Weather updated — {WEATHER_CACHE['city']}: {condition} ({w['description']}, {WEATHER_CACHE['temp']}°C)")
    except Exception as e:
        print(f"PY-LOG: Weather fetch failed: {e}. Defaulting to clear.")
        WEATHER_CACHE["condition"] = "clear"
        WEATHER_CACHE["last_fetch"] = now
    return WEATHER_CACHE


def get_weather_payload():
    """Return a clean dict (no internal fields) for API/WS responses."""
    return {k: v for k, v in WEATHER_CACHE.items() if k != "last_fetch"}
