"""Flask weather dashboard backed by Peewee and SQLite."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from peewee import SqliteDatabase
from models import WeatherObservation

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("WEATHER_DB_PATH", str(INSTANCE_DIR / "weather.db"))).expanduser().resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
db = SqliteDatabase(str(DB_PATH), pragmas={"foreign_keys": 1})


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me"),
                      WEATHER_PROVIDER=os.environ.get("WEATHER_PROVIDER", "openweathermap").lower(),
                      OPENWEATHERMAP_API_KEY=os.environ.get("OPENWEATHERMAP_API_KEY", ""),
                      REQUEST_TIMEOUT=float(os.environ.get("WEATHER_REQUEST_TIMEOUT", "8")),
                      HISTORY_LIMIT=25)
    if test_config:
        app.config.update(test_config)

    @app.before_request
    def connect_db():
        if db.is_closed():
            db.connect(reuse_if_open=True)
        db.create_tables([WeatherObservation])

    @app.teardown_request
    def close_db(_exc):
        if not db.is_closed():
            db.close()

    def fetch_weather(city):
        """Fetch current conditions; provider can be openweathermap or open-meteo."""
        provider = app.config["WEATHER_PROVIDER"]
        timeout = app.config["REQUEST_TIMEOUT"]
        if provider == "openweathermap":
            key = app.config["OPENWEATHERMAP_API_KEY"]
            if not key:
                raise ValueError("Set OPENWEATHERMAP_API_KEY to use OpenWeatherMap.")
            response = requests.get("https://api.openweathermap.org/data/2.5/weather",
                params={"q": city, "appid": key, "units": "metric"}, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            return {"provider": provider, "city": payload.get("name", city),
                    "temperature": payload["main"]["temp"], "feels_like": payload["main"].get("feels_like"),
                    "humidity": payload["main"].get("humidity"),
                    "description": payload.get("weather", [{}])[0].get("description", ""), "raw": payload}
        if provider == "open-meteo":
            geo = requests.get("https://geocoding-api.open-meteo.com/v1/search",
                               params={"name": city, "count": 1, "language": "en", "format": "json"}, timeout=timeout)
            geo.raise_for_status()
            results = geo.json().get("results", [])
            if not results:
                raise ValueError(f"Could not find a location named {city!r}.")
            place = results[0]
            response = requests.get("https://api.open-meteo.com/v1/forecast",
                params={"latitude": place["latitude"], "longitude": place["longitude"],
                        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
                        "timezone": "auto"}, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            current = payload["current"]
            return {"provider": provider, "city": place.get("name", city),
                    "temperature": current["temperature_2m"], "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "description": f"Weather code {current.get('weather_code', 'n/a')}", "raw": payload}
        raise ValueError("WEATHER_PROVIDER must be 'openweathermap' or 'open-meteo'.")

    @app.get("/")
    def index():
        history = (WeatherObservation.select().order_by(WeatherObservation.created_at.desc())
                   .limit(app.config["HISTORY_LIMIT"]))
        return render_template("index.html", history=history, provider=app.config["WEATHER_PROVIDER"])

    @app.post("/weather")
    def weather():
        city = request.form.get("city", "").strip()
        if not city or len(city) > 120:
            flash("Enter a city name (up to 120 characters).", "error")
            return redirect(url_for("index"))
        try:
            result = fetch_weather(city)
            WeatherObservation.create(city=result["city"], provider=result["provider"],
                temperature=float(result["temperature"]), feels_like=result["feels_like"],
                humidity=result["humidity"], description=result["description"],
                raw_json=json.dumps(result["raw"], ensure_ascii=False))
            flash(f"Weather for {result['city']} saved to the local database.", "success")
        except requests.Timeout:
            flash("Weather provider timed out. Please try again.", "error")
        except requests.RequestException as exc:
            flash(f"Weather provider request failed: {exc}", "error")
        except (ValueError, KeyError, TypeError) as exc:
            flash(str(exc) or "The provider returned an invalid response.", "error")
        return redirect(url_for("index"))

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": app.config["WEATHER_PROVIDER"]}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
