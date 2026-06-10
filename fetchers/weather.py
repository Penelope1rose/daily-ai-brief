"""
wttr.in API — live weather for Singapore.
Free, no API key required.
"""

import requests


def fetch() -> dict:
    """Return current weather + 3-period forecast for Singapore."""
    fallback = {
        "temp": "30",
        "feels_like": "35",
        "condition": "Partly Cloudy",
        "icon": "⛅",
        "humidity": "80%",
        "wind": "15 km/h",
        "uv": "High",
        "forecast": [
            {"period": "Morning",   "icon": "🌤️", "temp": "28°C", "desc": "Warm, sunny spells"},
            {"period": "Afternoon", "icon": "⛈️", "temp": "33°C", "desc": "Thunderstorms likely"},
            {"period": "Evening",   "icon": "🌦️", "temp": "28°C", "desc": "Clearing showers"},
        ],
        "live": False,
    }

    try:
        resp = requests.get(
            "https://wttr.in/Singapore",
            params={"format": "j1"},
            timeout=10,
            headers={"User-Agent": "DailyAIBrief/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        cur = data["current_condition"][0]
        desc = cur["weatherDesc"][0]["value"]
        temp_c = int(cur["temp_C"])
        feels_c = int(cur["FeelsLikeC"])
        humidity = cur["humidity"]
        wind_kmph = cur["windspeedKmph"]
        uv = cur.get("uvIndex", "N/A")

        # Map condition to emoji
        def condition_icon(desc_str: str) -> str:
            d = desc_str.lower()
            if "thunder" in d or "storm" in d: return "⛈️"
            if "rain" in d or "drizzle" in d or "shower" in d: return "🌧️"
            if "cloud" in d and "partly" in d: return "⛅"
            if "cloud" in d or "overcast" in d: return "☁️"
            if "fog" in d or "mist" in d or "haze" in d: return "🌫️"
            if "clear" in d or "sunny" in d: return "☀️"
            return "🌤️"

        # Build 3-period forecast from hourly (3 AM, 12 PM, 6 PM slots = indices 0, 4, 6 of hourly)
        today = data["weather"][0]
        hourly = today.get("hourly", [])
        slots = [
            ("Morning",   hourly[1] if len(hourly) > 1 else None),
            ("Afternoon", hourly[4] if len(hourly) > 4 else None),
            ("Evening",   hourly[6] if len(hourly) > 6 else None),
        ]
        forecast = []
        for period, slot in slots:
            if slot:
                sdesc = slot["weatherDesc"][0]["value"]
                stemp = slot["tempC"]
                forecast.append({
                    "period": period,
                    "icon": condition_icon(sdesc),
                    "temp": f"{stemp}°C",
                    "desc": sdesc,
                })
            else:
                forecast.append(fallback["forecast"][len(forecast)])

        uv_label = "Low" if int(uv or 0) < 3 else "Moderate" if int(uv or 0) < 6 else "High" if int(uv or 0) < 9 else "Very High"

        result = {
            "temp": str(temp_c),
            "feels_like": str(feels_c),
            "condition": desc,
            "icon": condition_icon(desc),
            "humidity": f"{humidity}%",
            "wind": f"{wind_kmph} km/h",
            "uv": uv_label,
            "forecast": forecast,
            "live": True,
        }
        print(f"[weather] live data: {temp_c}°C, {desc}")
        return result

    except Exception as e:
        print(f"[weather] failed ({e}), using fallback")
        return fallback
