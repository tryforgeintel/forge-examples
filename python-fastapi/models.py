"""Request and response models. FastAPI turns them into the /openapi.json that agents read."""

from pydantic import BaseModel, Field


class ForecastInput(BaseModel):
    city: str | None = Field(None, max_length=100, description="City name, e.g. London.")
    lat: float | None = Field(None, ge=-90, le=90, description="Latitude, with lon, instead of city.")
    lon: float | None = Field(None, ge=-180, le=180, description="Longitude, with lat, instead of city.")
    days: int = Field(3, ge=1, le=7, description="Number of days, 1-7.")

    model_config = {"json_schema_extra": {"examples": [{"city": "London", "days": 3}]}}


class Location(BaseModel):
    name: str
    country: str | None
    latitude: float
    longitude: float


class Current(BaseModel):
    time: str
    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    condition: str


class Day(BaseModel):
    date: str
    temperature_max_c: float
    temperature_min_c: float
    precipitation_mm: float | None
    condition: str


class WeatherOutput(BaseModel):
    location: Location
    current: Current


class ForecastOutput(BaseModel):
    location: Location
    days: list[Day]


class Error(BaseModel):
    detail: str
