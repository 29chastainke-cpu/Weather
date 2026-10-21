"""A small command-line weather app using the National Weather Service API."""

import json
import math
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE_URL = "https://api.weather.gov"
USER_AGENT = "StudentWeatherApp/1.0 (student weather project)"
REQUEST_TIMEOUT_SECONDS = 15


class WeatherAPIError(Exception):
    """Raised when a weather API request fails or returns unexpected data."""


def get_json(url):
    request = Request(
        url,
        headers={
            "Accept": "application/geo+json",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            return json.loads(response.read())
    except HTTPError as error:
        raise WeatherAPIError(
            f"The National Weather Service returned HTTP {error.code}."
        ) from error
    except URLError as error:
        raise WeatherAPIError(
            "Could not connect to the National Weather Service."
        ) from error
    except TimeoutError as error:
        raise WeatherAPIError(
            "The National Weather Service request timed out."
        ) from error
    except OSError as error:
        raise WeatherAPIError(
            "A network error interrupted the National Weather Service request."
        ) from error
    except (json.JSONDecodeError, UnicodeError) as error:
        raise WeatherAPIError(
            "The National Weather Service returned unreadable data."
        ) from error


def validate_coordinates(latitude, longitude):
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be a number from -90 to 90.")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be a number from -180 to 180.")


def get_forecast_url(latitude, longitude):
    points_url = f"{API_BASE_URL}/points/{latitude},{longitude}"
    points_data = get_json(points_url)

    try:
        forecast_url = points_data["properties"]["forecast"]
    except (KeyError, TypeError) as error:
        raise WeatherAPIError(
            "The location response did not include a forecast URL."
        ) from error

    if not isinstance(forecast_url, str):
        raise WeatherAPIError(
            "The location response contained an invalid forecast URL."
        )
    return forecast_url


def get_forecast(latitude, longitude):
    validate_coordinates(latitude, longitude)
    forecast_url = get_forecast_url(latitude, longitude)
    forecast_data = get_json(forecast_url)

    try:
        periods = forecast_data["properties"]["periods"]
    except (KeyError, TypeError) as error:
        raise WeatherAPIError(
            "The forecast response did not include forecast periods."
        ) from error

    if not isinstance(periods, list):
        raise WeatherAPIError("The forecast response contained invalid periods.")
    if any(not isinstance(period, dict) for period in periods):
        raise WeatherAPIError("The forecast response contained an invalid period.")
    return forecast_url, periods


def display_forecast(forecast_url, periods):
    print(f"\nForecast URL: {forecast_url}")

    if not periods:
        print("\nNo forecast periods were returned for this location.")
        return

    print("\nWeather forecast")
    for period in periods:
        name = period.get("name", "Forecast")
        temperature = period.get("temperature", "Not available")
        temperature_unit = period.get("temperatureUnit", "")
        short_forecast = period.get("shortForecast", "Not available")
        wind_speed = period.get("windSpeed", "Not available")
        wind_direction = period.get("windDirection", "Not available")

        print(f"\n{name}")
        print(f"  Temperature: {temperature} {temperature_unit}".rstrip())
        print(f"  Conditions: {short_forecast}")
        print(f"  Wind: {wind_speed} {wind_direction}")


def main():
    print("National Weather Service Weather App")
    try:
        latitude = float(input("Latitude: "))
        longitude = float(input("Longitude: "))
        forecast_url, periods = get_forecast(latitude, longitude)
    except ValueError as error:
        print(f"Invalid coordinates: {error}")
        return
    except WeatherAPIError as error:
        print(
            "Weather information is currently unavailable.\n"
            f"{error}\n"
            "Please try again."
        )
        return

    display_forecast(forecast_url, periods)


if __name__ == "__main__":
    main()
