"""Texas city forecasts and active weather alerts for the map page."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from threading import Lock
from time import monotonic
from urllib.parse import urlparse

from weather_app import API_BASE_URL, WeatherAPIError, get_forecast, get_json


TEXAS_CITIES = (
    {"name": "Amarillo", "latitude": 35.222, "longitude": -101.831},
    {"name": "Lubbock", "latitude": 33.578, "longitude": -101.855},
    {"name": "Wichita Falls", "latitude": 33.914, "longitude": -98.493},
    {"name": "El Paso", "latitude": 31.762, "longitude": -106.486},
    {"name": "Midland", "latitude": 31.998, "longitude": -102.078},
    {"name": "Abilene", "latitude": 32.449, "longitude": -99.733},
    {"name": "Tyler", "latitude": 32.351, "longitude": -95.301},
    {"name": "Fort Worth", "latitude": 32.755, "longitude": -97.330},
    {"name": "Dallas", "latitude": 32.777, "longitude": -96.797},
    {"name": "Waco", "latitude": 31.549, "longitude": -97.147},
    {"name": "Austin", "latitude": 30.267, "longitude": -97.743},
    {"name": "Houston", "latitude": 29.760, "longitude": -95.370},
    {"name": "San Antonio", "latitude": 29.425, "longitude": -98.494},
    {"name": "Beaumont", "latitude": 30.080, "longitude": -94.127},
    {"name": "Laredo", "latitude": 27.507, "longitude": -99.508},
    {"name": "Corpus Christi", "latitude": 27.801, "longitude": -97.396},
    {"name": "McAllen", "latitude": 26.204, "longitude": -98.230},
    {"name": "Brownsville", "latitude": 25.902, "longitude": -97.498},
)

_CACHE_SECONDS = 600
_cache_lock = Lock()
_cache_created = 0.0
_cache_data = None
_radar_cache_created = 0.0
_radar_cache_data = None


def _get_city_forecast(city):
    forecast_url, periods = get_forecast(city["latitude"], city["longitude"])
    if not periods:
        raise WeatherAPIError("No forecast periods were returned.")

    period = periods[0]
    return {
        **city,
        "temperature": period.get("temperature"),
        "temperatureUnit": period.get("temperatureUnit", "F"),
        "forecast": period.get("shortForecast", "Not available"),
        "period": period.get("name", "Current forecast period"),
        "forecastUrl": forecast_url,
    }


def _load_texas_map_data():
    cities = []
    errors = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_get_city_forecast, city): city for city in TEXAS_CITIES
        }
        for future in as_completed(futures):
            city = futures[future]
            try:
                cities.append(future.result())
            except WeatherAPIError as error:
                errors.append(f"{city['name']}: {error}")

    if not cities:
        raise WeatherAPIError(
            "Forecasts could not be loaded for any Texas cities. "
            + "; ".join(errors[:3])
        )

    try:
        alert_data = get_json(f"{API_BASE_URL}/alerts/active?area=TX")
        alert_features = alert_data["features"]
        if not isinstance(alert_features, list):
            raise TypeError("The alerts response did not contain a feature list.")
        alerts = []
        for feature in alert_features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                properties = {}
            alerts.append(
                {
                    "type": "Feature",
                    "geometry": feature.get("geometry"),
                    "properties": {
                        key: properties.get(key)
                        for key in (
                            "event",
                            "headline",
                            "severity",
                            "urgency",
                            "certainty",
                            "areaDesc",
                            "effective",
                            "ends",
                            "senderName",
                        )
                    },
                }
            )
    except (WeatherAPIError, KeyError, TypeError) as error:
        alerts = []
        errors.append(f"Active alerts could not be loaded: {error}")

    return {
        "cities": sorted(cities, key=lambda city: city["name"]),
        "alerts": alerts,
        "errors": errors,
    }


def get_texas_map_data():
    """Return cached forecasts for major Texas cities and active NWS alerts."""
    global _cache_created, _cache_data

    with _cache_lock:
        if _cache_data is not None and monotonic() - _cache_created < _CACHE_SECONDS:
            return _cache_data

    data = _load_texas_map_data()
    with _cache_lock:
        _cache_data = data
        _cache_created = monotonic()
    return data


def get_radar_frames():
    """Return recent radar tile frames and their timestamps from RainViewer."""
    global _radar_cache_created, _radar_cache_data

    with _cache_lock:
        if (
            _radar_cache_data is not None
            and monotonic() - _radar_cache_created < 300
        ):
            return _radar_cache_data

    radar_data = get_json("https://api.rainviewer.com/public/weather-maps.json")
    try:
        host = radar_data["host"]
        past_frames = radar_data["radar"]["past"]
        parsed_host = urlparse(host)
        if (
            parsed_host.scheme != "https"
            or parsed_host.hostname is None
            or not (
                parsed_host.hostname == "rainviewer.com"
                or parsed_host.hostname.endswith(".rainviewer.com")
            )
        ):
            raise TypeError("The radar API returned an invalid tile host.")
        frames = [
            {"time": int(frame["time"]), "path": frame["path"]}
            for frame in past_frames
            if isinstance(frame, dict)
            and isinstance(frame.get("path"), str)
            and re.fullmatch(r"/v2/radar/[A-Za-z0-9_-]+", frame["path"])
        ]
    except (KeyError, TypeError, ValueError) as error:
        raise WeatherAPIError(
            "The radar API returned invalid frame data."
        ) from error

    if not frames:
        raise WeatherAPIError("No recent radar frames are currently available.")

    data = {
        "host": host.rstrip("/"),
        "generated": radar_data.get("generated"),
        "frames": frames[-12:],
        "attribution": "RainViewer",
        "attributionUrl": "https://www.rainviewer.com/",
    }
    with _cache_lock:
        _radar_cache_data = data
        _radar_cache_created = monotonic()
    return data
