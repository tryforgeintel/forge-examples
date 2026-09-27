"""Weather data from Open-Meteo (https://open-meteo.com): free, no API key."""

import httpx

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"


class NotFoundError(Exception):
    pass


class UpstreamError(Exception):
    pass


# WMO weather codes, simplified.
CONDITIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 61: "Rain", 63: "Rain", 65: "Heavy rain",
    71: "Snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers", 81: "Rain showers",
    82: "Heavy rain showers", 95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
}  # fmt: skip


def condition(code: int) -> str:
    return CONDITIONS.get(code, "Unknown")


async def get_json(url: str, params: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(url, params=params)
    except httpx.HTTPError as error:
        raise UpstreamError(f"weather provider unreachable: {error}") from error
    if response.status_code != 200:
        raise UpstreamError(f"weather provider returned {response.status_code}")
    return response.json()


async def find_place(city: str | None, lat: float | None, lon: float | None) -> dict:
    """A city name, or lat/lon, to a place with coordinates."""
    if not city:
        return {"name": f"{lat},{lon}", "country": None, "latitude": lat, "longitude": lon}
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    results = (await get_json(GEOCODE, params)).get("results") or []
    if not results:
        raise NotFoundError(f'no place found for "{city}"')
    hit = results[0]
    return {
        "name": hit["name"],
        "country": hit.get("country"),
        "latitude": hit["latitude"],
        "longitude": hit["longitude"],
    }


async def current_weather(place: dict) -> dict:
    current = (
        await get_json(
            FORECAST,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "timezone": "auto",
            },
        )
    )["current"]
    return {
        "time": current["time"],
        "temperature_c": current["temperature_2m"],
        "humidity_pct": current["relative_humidity_2m"],
        "wind_speed_kmh": current["wind_speed_10m"],
        "condition": condition(current["weather_code"]),
    }


async def daily_forecast(place: dict, days: int) -> list[dict]:
    daily = (
        await get_json(
            FORECAST,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
                "forecast_days": days,
                "timezone": "auto",
            },
        )
    )["daily"]
    return [
        {
            "date": date,
            "temperature_max_c": daily["temperature_2m_max"][i],
            "temperature_min_c": daily["temperature_2m_min"][i],
            "precipitation_mm": daily["precipitation_sum"][i],
            "condition": condition(daily["weather_code"][i]),
        }
        for i, date in enumerate(daily["time"])
    ]
