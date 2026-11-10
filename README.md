# NetSec Monitor

A small, self-contained network and security monitoring data-management project. It provides two interchangeable implementations of the same SQLite schema: direct `sqlite3` access and a Peewee ORM layer. Both ship with interactive terminal menus for users, devices, services, security events, and alerts.

## Project layout

- `raw-sql/` — standard-library SQLite implementation and CLI.
- `peewee-orm/` — Peewee models, data manager, and CLI.
- `docs/architecture.md` — entities and relationships.
- `docs/ERD.png` — supplied ER diagram.

## Schema

| Entity | Purpose / key fields |
| --- | --- |
| User | username (unique), email, password hash, role |
| Device | hostname, IP address, type, status, location |
| Service | device FK, name, port, status |
| SecurityEvent (monitor log) | device FK, status code, latency, check time |
| Alert | device FK, type, severity, description, creation time |
| Incident | alert FK, assigned-user FK, title, status, creation time |

IDs are integer primary keys. Foreign keys are enabled and use cascading deletion for dependent records where appropriate. Passwords are represented only by a `password_hash` field; this demo does not implement authentication or hash passwords for you. Store a real password hash from a suitable authentication library in production.

## Requirements

- Python 3.9 or newer
- Raw SQL version: Python standard library only
- Peewee version: install `peewee>=3.17.0`

## Setup and running

Run commands from the project root. Each implementation creates `netsec_monitor.db` in its own directory on first launch.

### Raw SQLite

```bash
cd raw-sql
python main.py
```

### Peewee ORM

```bash
cd peewee-orm
python -m pip install -r requirements.txt
python main.py
```

Use the numbered menus to select an entity and then create, list, view, update, or delete records. For related records, create the parent device/user/alert first and use its numeric ID. Press `0` to return or exit. Local database files are ignored by Git.

## Notes

This is an educational CRUD starter, not a production monitoring agent. It does not collect network telemetry, authenticate users, or provide authorization. Back up the database before destructive changes. The supplied ERD includes monitor logs, alerts, and incidents; the CLI calls monitor logs “Security events.”
