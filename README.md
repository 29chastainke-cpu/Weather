# Texas Weather

A small browser weather app using the free National Weather Service (NWS) API.
It includes point forecasts and a Texas-wide map with major cities, forecast
temperatures, active NWS alerts, and animated recent radar.

## Run the app

Requires Python 3.10 or newer. No Python packages or API keys are required.

```powershell
python web_app.py
```

Open <http://127.0.0.1:8765> for the coordinate-based forecast, or
<http://127.0.0.1:8765/map> for the Texas map.

The forecast app calls the NWS `/points/{latitude},{longitude}` endpoint, then
uses the forecast URL from its response. Requests include the required
`User-Agent` header.

The map labels major Texas cities and colors their forecast temperatures. It
also shows active NWS alert areas and a recent radar loop with smooth
cross-fades. Radar intensity is recolored from yellow through orange and pink
to purple. Radar is a recent observation loop, not a prediction of future storm
movement. The NWS API does not provide cold-front line geometry, so the map
does not draw unverified front lines.

The map uses Leaflet and OpenStreetMap tiles. Recent radar frames come from
[RainViewer](https://www.rainviewer.com/), credited in the map.

## Run tests

```powershell
python -m unittest -v
```

## Project files

- `weather_app.py` — NWS forecast requests and command-line app
- `web_app.py` — local browser server and API routes
- `texas_weather.py` — Texas city forecasts, alerts, and radar frame metadata
- `texas_map.html` — interactive map and radar playback
- `test_weather_app.py`, `test_texas_weather.py` — unit tests
