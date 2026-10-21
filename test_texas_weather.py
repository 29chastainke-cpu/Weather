import unittest
from unittest.mock import patch

import texas_weather


class TexasWeatherTests(unittest.TestCase):
    @patch(
        "texas_weather.get_json",
        return_value={
            "features": [
                {
                    "geometry": {"type": "Polygon", "coordinates": []},
                    "properties": {
                        "event": "Heat Advisory",
                        "headline": "Hot conditions",
                        "description": "Long description",
                        "areaDesc": "Central Texas",
                    },
                }
            ]
        },
    )
    @patch(
        "texas_weather.get_forecast",
        return_value=(
            "https://api.weather.gov/gridpoints/TOP/32,81/forecast",
            [
                {
                    "name": "Today",
                    "temperature": 88,
                    "temperatureUnit": "F",
                    "shortForecast": "Sunny",
                }
            ],
        ),
    )
    def test_loads_city_forecasts_and_compact_alert_features(
        self, mocked_forecast, mocked_alerts
    ):
        data = texas_weather._load_texas_map_data()

        self.assertEqual(len(data["cities"]), len(texas_weather.TEXAS_CITIES))
        self.assertEqual(mocked_forecast.call_count, len(texas_weather.TEXAS_CITIES))
        self.assertEqual(
            data["cities"][0]["temperature"],
            88,
        )
        self.assertEqual(data["cities"][0]["period"], "Today")
        self.assertEqual(
            data["alerts"][0]["properties"]["headline"], "Hot conditions"
        )
        self.assertNotIn("description", data["alerts"][0]["properties"])
        mocked_alerts.assert_called_once_with(
            "https://api.weather.gov/alerts/active?area=TX"
        )

    @patch(
        "texas_weather.get_forecast",
        side_effect=texas_weather.WeatherAPIError("offline"),
    )
    def test_reports_failure_when_no_city_forecast_is_available(self, _mocked):
        with self.assertRaisesRegex(
            texas_weather.WeatherAPIError, "any Texas cities"
        ):
            texas_weather._load_texas_map_data()

    @patch(
        "texas_weather.get_json",
        return_value={
            "host": "https://tilecache.rainviewer.com",
            "generated": 123,
            "radar": {
                "past": [
                    {"time": index, "path": f"/v2/radar/frame-{index}"}
                    for index in range(15)
                ]
            },
        },
    )
    def test_returns_only_latest_twelve_radar_frames(self, mocked_get_json):
        texas_weather._radar_cache_data = None
        texas_weather._radar_cache_created = 0

        data = texas_weather.get_radar_frames()

        self.assertEqual(len(data["frames"]), 12)
        self.assertEqual(data["frames"][0]["time"], 3)
        self.assertEqual(data["frames"][-1]["path"], "/v2/radar/frame-14")
        self.assertEqual(data["host"], "https://tilecache.rainviewer.com")
        self.assertEqual(data["attribution"], "RainViewer")
        mocked_get_json.assert_called_once_with(
            "https://api.rainviewer.com/public/weather-maps.json"
        )

    @patch(
        "texas_weather.get_json",
        return_value={
            "host": "https://tilecache.rainviewer.com",
            "radar": {"past": []},
        },
    )
    def test_reports_when_radar_frames_are_missing(self, _mocked_get_json):
        texas_weather._radar_cache_data = None
        texas_weather._radar_cache_created = 0

        with self.assertRaisesRegex(
            texas_weather.WeatherAPIError, "No recent radar frames"
        ):
            texas_weather.get_radar_frames()


if __name__ == "__main__":
    unittest.main()
