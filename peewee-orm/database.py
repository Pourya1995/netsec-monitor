"""Peewee models and CRUD manager for NetSec Monitor."""
from pathlib import Path
from datetime import datetime
from peewee import (Model, SqliteDatabase, AutoField, CharField, TextField,
                    IntegerField, ForeignKeyField, DateTimeField)

DB = SqliteDatabase(str(Path(__file__).with_name('netsec_monitor.db')), pragmas={'foreign_keys': 1})

class BaseModel(Model):
    class Meta: database = DB

class User(BaseModel):
    id = AutoField(); username = CharField(max_length=50, unique=True)
    email = CharField(max_length=100); password_hash = CharField(max_length=255, default='')
    role = CharField(max_length=20, default='analyst')
    class Meta: table_name = 'users'

class Device(BaseModel):
    id = AutoField(); hostname = CharField(max_length=100); ip_address = CharField(max_length=45)
    device_type = CharField(max_length=50, default='unknown'); status = CharField(max_length=20, default='unknown')
    location = CharField(max_length=100, default='')
    class Meta: table_name = 'devices'

class Service(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref='services', on_delete='CASCADE', column_name='device_id')
    service_name = CharField(max_length=100); port = IntegerField(); status = CharField(max_length=20, default='unknown')
    class Meta: table_name = 'services'

class SecurityEvent(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref='events', on_delete='CASCADE', column_name='device_id')
    status_code = IntegerField(); latency_ms = IntegerField(default=0)
    checked_at = DateTimeField(default=datetime.now)  # populated by manager with an ISO timestamp
    class Meta: table_name = 'monitor_logs'

class Alert(BaseModel):
    id = AutoField(); device = ForeignKeyField(Device, backref='alerts', on_delete='CASCADE', column_name='device_id')
    alert_type = CharField(max_length=50); severity = CharField(max_length=20, default='medium')
    description = TextField(default=''); created_at = DateTimeField(default=datetime.now)
    class Meta: table_name = 'security_alerts'

class Incident(BaseModel):
    id = AutoField(); alert = ForeignKeyField(Alert, backref='incidents', on_delete='CASCADE', column_name='alert_id')
    assigned_user = ForeignKeyField(User, backref='incidents', null=True, on_delete='SET NULL', column_name='assigned_user_id')
    title = CharField(max_length=200); status = CharField(max_length=20, default='open'); created_at = DateTimeField(default=datetime.now)
    class Meta: table_name = 'incidents'

ENTITIES = {
 'users': (User, ('username','email','password_hash','role')),
 'devices': (Device, ('hostname','ip_address','device_type','status','location')),
 'services': (Service, ('device_id','service_name','port','status')),
 'monitor_logs': (SecurityEvent, ('device_id','status_code','latency_ms','checked_at')),
 'security_alerts': (Alert, ('device_id','alert_type','severity','description','created_at')),
}

class PeeweeDataManager:
    def __init__(self):
        if DB.is_closed(): DB.connect()
        DB.create_tables([User, Device, Service, SecurityEvent, Alert, Incident], safe=True)
    def close(self):
        if not DB.is_closed(): DB.close()
    def _model(self, entity):
        if entity not in ENTITIES: raise ValueError(f'Unsupported entity: {entity}')
        return ENTITIES[entity]
    def create(self, entity, **values):
        model, allowed = self._model(entity); self._validate(values, allowed)
        if entity in ('services','monitor_logs','security_alerts') and 'device_id' in values:
            values['device'] = values.pop('device_id')
        values.pop('id', None)
        obj = model.create(**values)
        return self.get(entity, obj.id)
    def list(self, entity):
        model, _ = self._model(entity)
        return [self._serialize(o) for o in model.select().order_by(model.id)]
    def get(self, entity, record_id):
        model, _ = self._model(entity)
        obj = model.get_or_none(model.id == record_id)
        return self._serialize(obj) if obj else None
    def update(self, entity, record_id, **values):
        model, allowed = self._model(entity); self._validate(values, allowed)
        if entity in ('services','monitor_logs','security_alerts') and 'device_id' in values:
            values['device'] = values.pop('device_id')
        values.pop('id', None)
        if values: model.update(**values).where(model.id == record_id).execute()
        return self.get(entity, record_id)
    def delete(self, entity, record_id):
        model, _ = self._model(entity)
        return model.delete().where(model.id == record_id).execute() > 0
    @staticmethod
    def _validate(values, allowed):
        invalid = set(values) - set(allowed) - {'id'}
        if invalid: raise ValueError(f'Unsupported fields: {", ".join(sorted(invalid))}')
    @staticmethod
    def _serialize(obj):
        result = dict(obj.__data__)
        for key in ('device','alert','assigned_user'):
            if key in result: result[key + '_id'] = result.pop(key)
        for key, value in list(result.items()):
            if hasattr(value, 'isoformat'): result[key] = value.isoformat(sep=' ')
        return result
