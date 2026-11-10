# FastAPI NetSec Monitor

FastAPI + Peewee + SQLite REST API matching the NetSec Monitor tables used by the Flask implementation. The API manages `users`, `devices`, `services`, `monitor_logs` (security events), `security_alerts` (alerts), and `incidents`, with the same foreign keys and cascade/SET NULL behavior.

## Run

```bash
python -m venv .venv
# activate the environment, then:
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive Swagger UI or `/redoc` for ReDoc. The HTML overview is at `/` and the API index is at `/api`.

Database is created automatically at `instance/netsec_monitor.db`. Set `NETSEC_DB_PATH=/path/to/netsec_monitor.db` to select another SQLite file. SQLite foreign-key enforcement is enabled. The `password_hash` field is stored as provided; this demo does not implement authentication or hash passwords.

## Endpoints

Each collection supports `GET` (list with `q`, relevant field filters, `limit`, and `offset`) and `POST` (201). Each `/{id}` supports `GET`, `PATCH` (partial update), `PUT` (replace supplied mutable values), and `DELETE` (204). Missing records return 404; invalid request data returns 422; uniqueness/FK conflicts return 409.

| Resource | API route | SQLite table |
|---|---|---|
| Users | `/api/users` | `users` |
| Devices | `/api/devices` | `devices` |
| Services | `/api/services` | `services` |
| Security events | `/api/security-events` | `monitor_logs` |
| Alerts | `/api/alerts` | `security_alerts` |
| Incidents | `/api/incidents` | `incidents` |

Foreign-key IDs are supplied as `device_id`, `alert_id`, and nullable `assigned_user_id`. Deleting a device cascades to services, events and alerts; deleting an alert cascades to incidents; deleting a user sets incident assignment to null.

## Example

```bash
curl -X POST http://127.0.0.1:8000/api/devices \
  -H 'Content-Type: application/json' \
  -d '{"hostname":"edge-01","ip_address":"192.0.2.10"}'
curl 'http://127.0.0.1:8000/api/devices?q=edge'
```
