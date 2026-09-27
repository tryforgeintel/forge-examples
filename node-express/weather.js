// Weather data from Open-Meteo (https://open-meteo.com): free, no API key.
const GEOCODE = "https://geocoding-api.open-meteo.com/v1/search";
const FORECAST = "https://api.open-meteo.com/v1/forecast";

export class NotFoundError extends Error {}
export class UpstreamError extends Error {}

// WMO weather codes, simplified.
const CONDITIONS = {
  0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
  51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 61: "Rain", 63: "Rain", 65: "Heavy rain",
  71: "Snow", 73: "Snow", 75: "Heavy snow", 80: "Rain showers", 81: "Rain showers", 82: "Heavy rain showers",
  95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail",
};
const condition = (code) => CONDITIONS[code] ?? "Unknown";

async function getJson(url, params) {
  let res;
  try {
    res = await fetch(`${url}?${new URLSearchParams(params)}`, { signal: AbortSignal.timeout(8000) });
  } catch (error) {
    throw new UpstreamError(`weather provider unreachable: ${error.cause?.code ?? error.message}`);
  }
  if (!res.ok) throw new UpstreamError(`weather provider returned ${res.status}`);
  return res.json();
}

/** A city name, or lat/lon, to a place with coordinates. */
export async function findPlace({ city, lat, lon }) {
  if (!city) return { name: `${lat},${lon}`, country: null, latitude: lat, longitude: lon };
  const hit = (await getJson(GEOCODE, { name: city, count: 1, language: "en", format: "json" })).results?.[0];
  if (!hit) throw new NotFoundError(`no place found for "${city}"`);
  return { name: hit.name, country: hit.country ?? null, latitude: hit.latitude, longitude: hit.longitude };
}

export async function currentWeather(place) {
  const c = (await getJson(FORECAST, {
    latitude: place.latitude,
    longitude: place.longitude,
    current: "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
    timezone: "auto",
  })).current;
  return {
    time: c.time,
    temperature_c: c.temperature_2m,
    humidity_pct: c.relative_humidity_2m,
    wind_speed_kmh: c.wind_speed_10m,
    condition: condition(c.weather_code),
  };
}

export async function dailyForecast(place, days) {
  const d = (await getJson(FORECAST, {
    latitude: place.latitude,
    longitude: place.longitude,
    daily: "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum",
    forecast_days: days,
    timezone: "auto",
  })).daily;
  return d.time.map((date, i) => ({
    date,
    temperature_max_c: d.temperature_2m_max[i],
    temperature_min_c: d.temperature_2m_min[i],
    precipitation_mm: d.precipitation_sum[i],
    condition: condition(d.weather_code[i]),
  }));
}
