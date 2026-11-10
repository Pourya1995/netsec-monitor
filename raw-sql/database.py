"""SQLite schema and CRUD manager for NetSec Monitor (standard library only)."""
from pathlib import Path
import sqlite3

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE,
 email TEXT NOT NULL, password_hash TEXT NOT NULL DEFAULT '', role TEXT NOT NULL DEFAULT 'analyst');
CREATE TABLE IF NOT EXISTS devices (
 id INTEGER PRIMARY KEY AUTOINCREMENT, hostname TEXT NOT NULL,
 ip_address TEXT NOT NULL, device_type TEXT NOT NULL DEFAULT 'unknown',
 status TEXT NOT NULL DEFAULT 'unknown', location TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS services (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id INTEGER NOT NULL,
 service_name TEXT NOT NULL, port INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'unknown',
 FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS monitor_logs (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id INTEGER NOT NULL,
 status_code INTEGER NOT NULL, latency_ms INTEGER NOT NULL DEFAULT 0,
 checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS security_alerts (
 id INTEGER PRIMARY KEY AUTOINCREMENT, device_id INTEGER NOT NULL,
 alert_type TEXT NOT NULL, severity TEXT NOT NULL DEFAULT 'medium',
 description TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS incidents (
 id INTEGER PRIMARY KEY AUTOINCREMENT, alert_id INTEGER NOT NULL,
 assigned_user_id INTEGER, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(alert_id) REFERENCES security_alerts(id) ON DELETE CASCADE,
 FOREIGN KEY(assigned_user_id) REFERENCES users(id) ON DELETE SET NULL);
"""

ENTITIES = {
 'users': ('Users', ('username','email','password_hash','role')),
 'devices': ('Devices', ('hostname','ip_address','device_type','status','location')),
 'services': ('Services', ('device_id','service_name','port','status')),
 'monitor_logs': ('Security events', ('device_id','status_code','latency_ms','checked_at')),
 'security_alerts': ('Alerts', ('device_id','alert_type','severity','description','created_at')),
}

class RawDataManager:
    """CRUD operations over a SQLite database; values are always parameterized."""
    def __init__(self, db_path=None):
        self.db_path = str(db_path or Path(__file__).with_name('netsec_monitor.db'))
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute('PRAGMA foreign_keys = ON')
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self): self.connection.close()

    def create(self, entity, **values):
        self._check_entity(entity, values)
        cols = ', '.join(values)
        marks = ', '.join('?' for _ in values)
        cur = self.connection.execute(f'INSERT INTO {entity} ({cols}) VALUES ({marks})', tuple(values.values()))
        self.connection.commit()
        return self.get(entity, cur.lastrowid)

    def list(self, entity):
        self._check_entity(entity)
        return [dict(r) for r in self.connection.execute(f'SELECT * FROM {entity} ORDER BY id')]

    def get(self, entity, record_id):
        self._check_entity(entity)
        row = self.connection.execute(f'SELECT * FROM {entity} WHERE id = ?', (record_id,)).fetchone()
        return dict(row) if row else None

    def update(self, entity, record_id, **values):
        self._check_entity(entity, values)
        if not values: return self.get(entity, record_id)
        assignments = ', '.join(f'{k} = ?' for k in values)
        self.connection.execute(f'UPDATE {entity} SET {assignments} WHERE id = ?', (*values.values(), record_id))
        self.connection.commit()
        return self.get(entity, record_id)

    def delete(self, entity, record_id):
        self._check_entity(entity)
        cur = self.connection.execute(f'DELETE FROM {entity} WHERE id = ?', (record_id,))
        self.connection.commit()
        return cur.rowcount > 0

    @staticmethod
    def _check_entity(entity, values=None):
        if entity not in ENTITIES: raise ValueError(f'Unsupported entity: {entity}')
        allowed = {'id', *ENTITIES[entity][1], 'created_at', 'checked_at'}
        invalid = set(values or ()) - allowed
        if invalid: raise ValueError(f'Unsupported fields: {", ".join(sorted(invalid))}')
