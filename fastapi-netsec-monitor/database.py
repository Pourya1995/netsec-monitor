"""SQLite/Peewee connection configuration for NetSec Monitor."""
import os
from pathlib import Path
from peewee import SqliteDatabase

DEFAULT_DB = Path(__file__).resolve().parent / "instance" / "netsec_monitor.db"
DB_PATH = Path(os.environ.get("NETSEC_DB_PATH", str(DEFAULT_DB))).expanduser().resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
database = SqliteDatabase(None, pragmas={"foreign_keys": 1, "journal_mode": "wal"}, check_same_thread=False)

def initialize_database():
    """Bind the configured SQLite path and create any missing tables."""
    if database.is_closed():
        database.init(str(DB_PATH))
        database.connect(reuse_if_open=True)
    from models import ALL_MODELS
    database.create_tables(ALL_MODELS, safe=True)
    if not database.is_closed():
        database.close()

def connect_database():
    if database.is_closed():
        database.init(str(DB_PATH))
        database.connect(reuse_if_open=True)

def close_database():
    if not database.is_closed():
        database.close()
