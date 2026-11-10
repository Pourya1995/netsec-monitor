# Architecture

## Overview

The project has a small presentation layer (interactive CLI), a data-access layer, and a local SQLite database. `raw-sql/database.py` uses parameterized `sqlite3` statements. `peewee-orm/database.py` defines Peewee models and wraps them with a matching data-manager API. The CLIs use those managers and do not contain SQL/model persistence logic.

## Entities and relationships

- **User** (`users`): account metadata (`username`, `email`, `password_hash`, `role`).
- **Device** (`devices`): monitored host metadata (`hostname`, `ip_address`, `device_type`, `status`, `location`).
- **Service** (`services`): service/port hosted on a device. `device_id` references `devices.id`; one device has many services.
- **SecurityEvent** (`monitor_logs`): monitoring check (`status_code`, `latency_ms`, `checked_at`) associated with a device; one device has many events.
- **Alert** (`security_alerts`): security finding (`alert_type`, `severity`, `description`, `created_at`) associated with a device; one device can raise many alerts.
- **Incident** (`incidents`): response record with `alert_id` and optional `assigned_user_id`; one alert can have many incidents and one user can be assigned many incidents.

Every table has an integer primary key. Foreign keys are enforced. Deleting a device cascades to its services, monitor logs, and alerts; deleting an alert cascades to incidents; deleting a user sets incident assignment to NULL. User and device remain independent, matching the supplied ERD (which does not show a user FK on devices).

## Operational boundaries

SQLite is suitable for a local demo and single-user workflows. The project does not ingest live packets, run scheduled checks, provide a web API, or implement production authentication/authorization. Use proper password hashing and access controls before adapting the sample for real user credentials.
