# National Weather Service Weather App

A small weather app that uses the free National Weather Service API. It needs
no API key and sends a descriptive `User-Agent` header with every request.

## Run

From this folder, start the browser app:

```powershell
python web_app.py
```

Open <http://127.0.0.1:8765> in a browser. Enter a latitude and longitude and
select **Get forecast**. The app calls the NWS `/points` endpoint, gets the
forecast URL from its JSON response, then requests and displays the forecast
periods, temperature, conditions, wind speed, and wind direction.

Example coordinates: latitude `39.7456`, longitude `-97.0892`.

## Deploy to Render

The repository includes a Render Blueprint in `render.yaml`. To publish a
public website:

1. Sign in to [Render](https://render.com/).
2. Choose **New** > **Blueprint** and connect the
   [Weather GitHub repository](https://github.com/29chastainke-cpu/Weather).
3. Select the `main` branch and deploy the `texas-weather` web service defined
   in `render.yaml`.
4. Open the public `onrender.com` URL Render assigns to the service.

The server binds to Render's `PORT` and `HOST` environment variables in
deployment, and uses `127.0.0.1:8765` for local development. No paid API key
or Python package installation is required.

Open <http://127.0.0.1:8765/map> for the Texas map. It labels major Texas
cities, colors their forecast temperatures by range, and shows active NWS
weather alert areas using colors for alert types. Map tiles are provided by
OpenStreetMap. Temperature markers show the first NWS forecast period rather
than live observations. The NWS API does not provide cold-front line geometry,
so the map does not draw unverified front lines.

The map also includes an animated recent-radar layer. Recent scans play in a
continuous loop with cross-fades between frames; use **Play/Pause** to control
the animation. Radar echoes are recolored from light yellow through orange and
pink to dark purple by reflectivity intensity. The
National Weather Service API used for forecasts does not publish animated
radar imagery, so this layer uses RainViewer's public radar API and credits
RainViewer on the map. The radar is a recent observation loop, not a forecast
of where a weather system will move next.

The original command-line version is still available with `python weather_app.py`.

## Test

```powershell
python -m unittest
```
