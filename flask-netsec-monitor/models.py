"""Peewee schema for the NetSec Monitor ERD."""
from datetime import datetime
from pathlib import Path
import os
from peewee import (Model, SqliteDatabase, AutoField, CharField, TextField, IntegerField, ForeignKeyField, DateTimeField)

DEFAULT_DB = Path(__file__).resolve().parent / "instance" / "netsec_monitor.db"
DB_PATH = Path(os.environ.get("NETSEC_DB_PATH", str(DEFAULT_DB))).expanduser().resolve()
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
database = SqliteDatabase(str(DB_PATH), pragmas={"foreign_keys": 1})

class BaseModel(Model):
    class Meta: database = database

class User(BaseModel):
    id = AutoField(); username = CharField(max_length=50, unique=True); email = CharField(max_length=100)
    password_hash = CharField(max_length=255, default=""); role = CharField(max_length=20, default="analyst")
    class Meta: table_name = "users"

class Device(BaseModel):
    id = AutoField(); hostname = CharField(max_length=100); ip_address = CharField(max_length=45)
    device_type = CharField(max_length=50, default="unknown"); status = CharField(max_length=20, default="unknown")
    location = CharField(max_length=100, default="")
    class Meta: table_name = "devices"

class Service(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref="services", on_delete="CASCADE", column_name="device_id")
    service_name = CharField(max_length=100); port = IntegerField(); status = CharField(max_length=20, default="unknown")
    class Meta: table_name = "services"

class SecurityEvent(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref="events", on_delete="CASCADE", column_name="device_id")
    status_code = IntegerField(); latency_ms = IntegerField(default=0); checked_at = DateTimeField(default=datetime.now)
    class Meta: table_name = "monitor_logs"

class Alert(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref="alerts", on_delete="CASCADE", column_name="device_id")
    alert_type = CharField(max_length=50); severity = CharField(max_length=20, default="medium")
    description = TextField(default=""); created_at = DateTimeField(default=datetime.now)
    class Meta: table_name = "security_alerts"

class Incident(BaseModel):
    id = AutoField(); alert = ForeignKeyField(Alert, backref="incidents", on_delete="CASCADE", column_name="alert_id")
    assigned_user = ForeignKeyField(User, backref="incidents", null=True, on_delete="SET NULL", column_name="assigned_user_id")
    title = CharField(max_length=200); status = CharField(max_length=20, default="open"); created_at = DateTimeField(default=datetime.now)
    class Meta: table_name = "incidents"

ALL_MODELS = [User, Device, Service, SecurityEvent, Alert, Incident]
def initialize_database():
    if database.is_closed(): database.connect(reuse_if_open=True)
    database.create_tables(ALL_MODELS, safe=True)
    database.close()
