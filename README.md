# NetSec Monitor

A small, educational network/security monitoring data-management project with three complementary implementations: direct SQLite CRUD, a Peewee ORM CLI, and a Flask weather-monitoring web service that stores external API observations in SQLite.

## Project layout

- `raw-sql/` — standard-library SQLite implementation and interactive CLI.
- `peewee-orm/` — Peewee models, data manager, and interactive CLI.
- `flask-weather-app/` — Flask dashboard using Peewee and Requests to collect and persist weather data.
- `docs/architecture.md` — entities and relationships for the NetSec CRUD schema.
- `docs/ERD.png` — supplied ER diagram.

## NetSec schema

| Entity | Purpose / key fields |
| --- | --- |
| User | username (unique), email, password hash, role |
| Device | hostname, IP address, type, status, location |
| Service | device FK, name, port, status |
| SecurityEvent (monitor log) | device FK, status code, latency, check time |
| Alert | device FK, type, severity, description, creation time |
| Incident | alert FK, assigned-user FK, title, status, creation time |

The two CLI variants provide CRUD operations for the same SQLite schema. IDs are integer primary keys. Passwords are represented only by a `password_hash` field; the demo does not implement authentication or hash passwords.

## Requirements

- Python 3.9 or newer
- Raw SQL: Python standard library only
- Peewee CLI: install `peewee>=3.17.0`
- Flask service: Flask, Peewee, and Requests (see `flask-weather-app/requirements.txt`)

## Run the NetSec CLI implementations

Run from the project root; each CLI creates its own `netsec_monitor.db` inside its implementation folder.

```bash
cd raw-sql && python main.py
```

```bash
cd peewee-orm
python -m pip install -r requirements.txt
python main.py
```

Use the numbered menus to create, list, view, update, or delete records. Create parent device/user/alert records first for related records. Local database files are ignored by Git.

## Run the Flask weather monitor

```bash
cd flask-weather-app
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `OPENWEATHERMAP_API_KEY` and use the default `WEATHER_PROVIDER=openweathermap`, or set `WEATHER_PROVIDER=open-meteo` to use Open-Meteo geocoding/current weather without an API key. Environment variables may be exported directly; the app does not require a dotenv loader. Launch with `python app.py` and visit `http://127.0.0.1:5000`. The service retrieves current weather for a city, stores each result via Peewee in `flask-weather-app/instance/weather.db` (an absolute path anchored to the app, overridable with `WEATHER_DB_PATH`), and shows recent observations. Requests use a finite timeout. See `flask-weather-app/README.md` for configuration and deployment caveats.

## Notes

These are educational starters, not production monitoring/security services. The NetSec CLI project does not collect network telemetry or implement authentication/authorization. The weather site has no authentication, rate limiting, CSRF protection, or production server setup. Secure secrets and add appropriate protections before public deployment. Back up local databases before destructive changes.
