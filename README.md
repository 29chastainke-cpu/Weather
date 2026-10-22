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

## Publish with GitHub Pages

The repository includes a GitHub Actions Pages workflow. After the workflow
completes, open
<https://29chastainke-cpu.github.io/Weather/> for the forecast or
<https://29chastainke-cpu.github.io/Weather/texas_map.html> for the Texas map.
Both pages include a direct link to the
[GitHub repository](https://github.com/29chastainke-cpu/Weather).

The Pages version is static HTML and JavaScript. The browser requests live
forecasts and alerts from the National Weather Service API and radar frames
from RainViewer; it does not run the Python server. The NWS API accepts the
browser's built-in `User-Agent` and no API key is needed. Local development
can still use `python web_app.py`.

The Texas map labels major Texas cities, colors their forecast temperatures by
range, and shows active NWS weather alert areas using colors for alert types.
Map tiles are provided by OpenStreetMap. Temperature markers show the first
NWS forecast period rather than live observations. The NWS API does not
provide cold-front line geometry, so the map does not draw unverified fronts.

The map also includes an animated recent-radar layer. Recent scans play in a
continuous loop with cross-fades between frames; use **Play/Pause** to control
the animation. Radar uses RainViewer's native reflectivity palette, including
pink for strong echoes, and loads tiles as images without cross-origin canvas
access. The National Weather Service API does not publish animated radar
imagery, so this layer uses RainViewer's public radar API and credits
RainViewer on the map. The radar is a recent observation loop, not a forecast
of where a weather system will move next.

The original command-line version is still available with `python weather_app.py`.

## Test

```powershell
python -m unittest
```
