"""Run the weather app as a local browser interface."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from weather_app import WeatherAPIError, get_forecast
from texas_weather import get_radar_frames, get_texas_map_data


HOST = "127.0.0.1"
PORT = 8765

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Weather Forecast</title>
  <style>
    :root { color-scheme: light; font-family: "Segoe UI", sans-serif; color: #172d45; background: #edf4fa; }
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; padding: 48px 20px; }
    main { width: min(900px, 100%); margin: auto; }
    header { padding: 12px 0 26px; }
    .eyebrow { color: #147d91; font-size: 12px; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; }
    h1 { margin: 8px 0; font-size: clamp(32px, 6vw, 48px); }
    .intro { color: #60758b; margin: 0; }
    form, .forecast { background: white; border: 1px solid #dce7ef; border-radius: 16px; box-shadow: 0 8px 26px #243c5510; }
    form { display: flex; flex-wrap: wrap; align-items: end; gap: 14px; padding: 20px; }
    label { display: grid; gap: 7px; color: #60758b; font-size: 13px; font-weight: 600; }
    input { width: 170px; max-width: 38vw; padding: 11px 12px; border: 1px solid #cfdae5; border-radius: 8px; color: #172d45; font: inherit; }
    button { padding: 12px 20px; border: 0; border-radius: 8px; background: #147d91; color: white; cursor: pointer; font: inherit; font-weight: 700; }
    button:disabled { opacity: .6; cursor: wait; }
    #status { min-height: 24px; margin: 16px 2px; color: #60758b; }
    #status.error { color: #b42318; }
    .forecast { overflow: hidden; }
    .forecast-head { padding: 18px 20px; border-bottom: 1px solid #e3ebf1; }
    .forecast-head h2 { margin: 0 0 5px; font-size: 18px; }
    .forecast-head a { color: #147d91; font-size: 12px; overflow-wrap: anywhere; }
    .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 1px; background: #e3ebf1; }
    .card { background: white; padding: 18px 20px; }
    .card h3 { margin: 0 0 10px; font-size: 16px; }
    .temp { font-size: 28px; font-weight: 700; }
    .conditions { min-height: 40px; margin: 4px 0 14px; color: #60758b; }
    .details { display: flex; justify-content: space-between; gap: 12px; padding-top: 10px; border-top: 1px solid #edf1f5; font-size: 13px; }
    .details span:first-child { color: #60758b; }
    [hidden] { display: none !important; }
    @media (max-width: 500px) { body { padding: 24px 14px; } input { width: 100%; max-width: none; } label { flex: 1 1 42%; } button { width: 100%; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">National Weather Service</div>
      <h1>Weather forecast</h1>
      <p class="intro">A local forecast, straight from the NWS.</p>
    </header>
    <form id="location-form">
      <label>Latitude<input id="latitude" name="latitude" type="number" step="any" min="-90" max="90" value="39.7456" required></label>
      <label>Longitude<input id="longitude" name="longitude" type="number" step="any" min="-180" max="180" value="-97.0892" required></label>
      <button id="submit" type="submit">Get forecast</button>
    </form>
    <p id="status" role="status">Loading forecast…</p>
    <section id="forecast" class="forecast" hidden>
      <div class="forecast-head"><h2>Forecast</h2><a id="forecast-link" target="_blank" rel="noopener noreferrer"></a></div>
      <div id="cards" class="cards"></div>
    </section>
  </main>
  <script>
    const form = document.querySelector("#location-form");
    const status = document.querySelector("#status");
    const button = document.querySelector("#submit");
    const forecast = document.querySelector("#forecast");
    const cards = document.querySelector("#cards");
    const forecastLink = document.querySelector("#forecast-link");

    function addDetail(container, label, value) {
      const row = document.createElement("div");
      row.className = "details";
      const name = document.createElement("span");
      name.textContent = label;
      const data = document.createElement("strong");
      data.textContent = value || "Not available";
      row.append(name, data);
      container.append(row);
    }

    function showForecast(url, periods) {
      cards.replaceChildren();
      forecastLink.href = url;
      forecastLink.textContent = url;
      for (const period of periods) {
        const card = document.createElement("article");
        card.className = "card";
        const heading = document.createElement("h3");
        heading.textContent = period.name || "Forecast";
        const temperature = document.createElement("div");
        temperature.className = "temp";
        temperature.textContent = period.temperature == null
          ? "—"
          : `${period.temperature} ${period.temperatureUnit || ""}`.trim();
        const conditions = document.createElement("p");
        conditions.className = "conditions";
        conditions.textContent = period.shortForecast || "Conditions unavailable";
        card.append(heading, temperature, conditions);
        addDetail(card, "Wind speed", period.windSpeed);
        addDetail(card, "Wind direction", period.windDirection);
        cards.append(card);
      }
      forecast.hidden = false;
      status.className = "";
      status.textContent = periods.length
        ? `Showing ${periods.length} forecast periods.`
        : "No forecast periods were returned for this location.";
    }

    async function loadForecast(event) {
      event?.preventDefault();
      button.disabled = true;
      forecast.hidden = true;
      status.className = "";
      status.textContent = "Getting forecast…";
      try {
        const response = await fetch("/forecast", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            latitude: Number(form.elements.latitude.value),
            longitude: Number(form.elements.longitude.value)
          })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Weather is unavailable.");
        showForecast(data.url, data.periods);
      } catch (error) {
        status.className = "error";
        status.textContent = `Weather information is currently unavailable. ${error.message} Please try again.`;
      } finally {
        button.disabled = false;
      }
    }

    form.addEventListener("submit", loadForecast);
    loadForecast();
  </script>
</body>
</html>
"""


class WeatherHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/map", "/map/"):
            body = Path(__file__).with_name("texas_map.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/texas-weather":
            try:
                self._send_json(200, get_texas_map_data())
            except WeatherAPIError as error:
                self._send_json(502, {"error": str(error)})
            return
        if self.path == "/radar-frames":
            try:
                self._send_json(200, get_radar_frames())
            except WeatherAPIError as error:
                self._send_json(502, {"error": str(error)})
            return
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Not found")
            return
        body = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/forecast":
            self.send_error(404, "Not found")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 4096:
                raise ValueError("Request body must contain valid coordinates.")
            payload = json.loads(self.rfile.read(length))
            latitude = float(payload["latitude"])
            longitude = float(payload["longitude"])
            forecast_url, periods = get_forecast(latitude, longitude)
            self._send_json(
                200, {"url": forecast_url, "periods": periods}
            )
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            self._send_json(400, {"error": f"Invalid coordinates: {error}"})
        except WeatherAPIError as error:
            self._send_json(502, {"error": str(error)})

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        print(f"{self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), WeatherHandler)
    print(f"Weather app running at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping weather app.")
    finally:
        server.server_close()
