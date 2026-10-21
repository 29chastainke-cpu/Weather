import io
import json
import unittest
from contextlib import redirect_stdout
from urllib.error import URLError
from unittest.mock import patch
from urllib.request import Request

import weather_app


class Response:
    def __init__(self, data):
        self.data = json.dumps(data).encode()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self.data


class WeatherAppTests(unittest.TestCase):
    def test_fetches_point_then_forecast_with_user_agent(self):
        responses = [
            Response({"properties": {"forecast": "https://api.weather.gov/forecast"}}),
            Response({"properties": {"periods": [{"name": "Today"}]}}),
        ]
        with patch("weather_app.urlopen", side_effect=responses) as mocked_urlopen:
            url, periods = weather_app.get_forecast(39.7456, -97.0892)

        self.assertEqual(url, "https://api.weather.gov/forecast")
        self.assertEqual(periods, [{"name": "Today"}])
        point_request = mocked_urlopen.call_args_list[0].args[0]
        forecast_request = mocked_urlopen.call_args_list[1].args[0]
        self.assertEqual(
            point_request.full_url,
            "https://api.weather.gov/points/39.7456,-97.0892",
        )
        self.assertIsInstance(point_request, Request)
        self.assertEqual(point_request.get_header("User-agent"), weather_app.USER_AGENT)
        self.assertEqual(
            forecast_request.get_header("User-agent"), weather_app.USER_AGENT
        )

    def test_rejects_out_of_range_coordinates_before_request(self):
        with patch("weather_app.urlopen") as mocked_urlopen:
            with self.assertRaisesRegex(ValueError, "Latitude"):
                weather_app.get_forecast(91, 0)
        mocked_urlopen.assert_not_called()

    def test_reports_network_errors(self):
        with patch("weather_app.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(
                weather_app.WeatherAPIError, "Could not connect"
            ):
                weather_app.get_forecast(39.7456, -97.0892)

    def test_displays_forecast_fields(self):
        output = io.StringIO()
        with redirect_stdout(output):
            weather_app.display_forecast(
                "https://api.weather.gov/forecast",
                [
                    {
                        "name": "Today",
                        "temperature": 72,
                        "temperatureUnit": "F",
                        "shortForecast": "Sunny",
                        "windSpeed": "5 mph",
                        "windDirection": "NW",
                    }
                ],
            )

        displayed = output.getvalue()
        for expected in ("Today", "72 F", "Sunny", "5 mph NW"):
            self.assertIn(expected, displayed)


if __name__ == "__main__":
    unittest.main()
