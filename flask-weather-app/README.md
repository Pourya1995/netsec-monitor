# Flask Weather App

Small weather dashboard integrated into NetSec Monitor. It uses Flask for the web UI, Peewee for persistence, Requests for HTTP, and SQLite for local observation history.

## Features

- City lookup and current conditions, saved into `weather_observations`.
- OpenWeatherMap integration (default; requires an API key) and optional Open-Meteo integration (geocoding plus current conditions, no key).
- Absolute SQLite database path derived from this module (`instance/weather.db` by default), independent of the shell's working directory. Override with `WEATHER_DB_PATH`.
- Bounded HTTP timeouts, response status checks and user-friendly handling of network/provider errors.
- `/health` endpoint and a recent-observation dashboard.

## Setup

```bash
cd flask-weather-app
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
```

Set `OPENWEATHERMAP_API_KEY` and keep `WEATHER_PROVIDER=openweathermap`, or choose `WEATHER_PROVIDER=open-meteo` (no key). Export variables in your shell or load the `.env` values using your preferred environment manager; `.env` is intentionally ignored by Git. Run with `python app.py`; visit http://127.0.0.1:5000. Set `FLASK_SECRET_KEY` for deployments and never enable debug mode on a public server.

The database folder is created automatically. Do not commit API credentials, virtual environments, bytecode, or local databases. This demo has no authentication, rate limiting, CSRF protection, or production deployment configuration; add these before exposing it publicly.
