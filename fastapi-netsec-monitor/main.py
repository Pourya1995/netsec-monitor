"""REST API and lightweight HTML overview for NetSec Monitor."""
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from peewee import IntegrityError, DoesNotExist
from database import initialize_database, connect_database, close_database
from models import User, Device, Service, SecurityEvent, Alert, Incident
import schemas as s

ENTITIES = {
    "users": (User, s.UserCreate, s.UserUpdate, s.UserRead, "Users", "/api/users"),
    "devices": (Device, s.DeviceCreate, s.DeviceUpdate, s.DeviceRead, "Devices", "/api/devices"),
    "services": (Service, s.ServiceCreate, s.ServiceUpdate, s.ServiceRead, "Services", "/api/services"),
    "security-events": (SecurityEvent, s.SecurityEventCreate, s.SecurityEventUpdate, s.SecurityEventRead, "Security events", "/api/security-events"),
    "alerts": (Alert, s.AlertCreate, s.AlertUpdate, s.AlertRead, "Alerts", "/api/alerts"),
    "incidents": (Incident, s.IncidentCreate, s.IncidentUpdate, s.IncidentRead, "Incidents", "/api/incidents"),
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield
    close_database()

app = FastAPI(title="NetSec Monitor API", description="REST API for the NetSec Monitor SQLite schema.", version="1.0.0", lifespan=lifespan)

@app.middleware("http")
async def database_connection(request, call_next):
    connect_database()
    try:
        return await call_next(request)
    finally:
        close_database()

def serialize(model, obj):
    data = dict(obj.__data__)
    # Peewee stores FK values in the related field slot; expose stable SQL/API names.
    aliases = {"device": "device_id", "alert": "alert_id", "assigned_user": "assigned_user_id"}
    for key, target in aliases.items():
        if key in data:
            data[target] = data.pop(key)
    return data

def not_found():
    raise HTTPException(status_code=404, detail="Record not found")

def model_values(model, values):
    """Translate stable SQL/API FK names into Peewee relation field names."""
    mapping = {"device_id": "device", "alert_id": "alert", "assigned_user_id": "assigned_user"}
    return {mapping.get(key, key): value for key, value in values.items()}

def create_record(model, payload):
    try:
        obj = model.create(**model_values(model, payload.model_dump(exclude_none=True)))
        return serialize(model, obj)
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail=f"Integrity constraint failed: {exc}") from exc
    except DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="Referenced record not found") from exc

def list_records(model, q, device_id, alert_id, assigned_user_id, status, severity, limit, offset):
    query = model.select()
    # ID filters are applied only to entities carrying that relationship.
    for key, value in (("device_id", device_id), ("alert_id", alert_id), ("assigned_user_id", assigned_user_id), ("status", status), ("severity", severity)):
        field = model._meta.fields.get({"device_id":"device", "alert_id":"alert", "assigned_user_id":"assigned_user"}.get(key, key))
        if value is not None and field is not None:
            query = query.where(field == value)
    if q:
        terms = []
        for field in model._meta.sorted_fields:
            if field.field_type in ("VARCHAR", "TEXT"):
                terms.append(field.contains(q))
        if terms:
            from functools import reduce
            from operator import or_
            query = query.where(reduce(or_, terms))
    return [serialize(model, row) for row in query.order_by(model.id.desc()).limit(limit).offset(offset)]

def fetch_record(model, record_id):
    obj = model.get_or_none(model.id == record_id)
    if obj is None:
        not_found()
    return serialize(model, obj)

def update_record(model, record_id, payload):
    obj = model.get_or_none(model.id == record_id)
    if obj is None:
        not_found()
    values = payload.model_dump(exclude_unset=True)
    # Null only clears nullable assignment; other explicit nulls mean unchanged.
    values = {key: value for key, value in values.items() if value is not None or key == "assigned_user_id"}
    if values:
        try:
            model.update(**model_values(model, values)).where(model.id == record_id).execute()
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail=f"Integrity constraint failed: {exc}") from exc
    return fetch_record(model, record_id)

def delete_record(model, record_id):
    deleted = model.delete().where(model.id == record_id).execute()
    if not deleted:
        not_found()

# Register complete CRUD routes for each entity with precise Pydantic OpenAPI types.
def register_crud(model, create_schema, update_schema, read_schema, label, route):
    def list_endpoint(q: Optional[str] = None, device_id: Optional[int] = None,
                      alert_id: Optional[int] = None, assigned_user_id: Optional[int] = None,
                      status: Optional[str] = None, severity: Optional[str] = None,
                      limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
        return list_records(model, q, device_id, alert_id, assigned_user_id, status, severity, limit, offset)
    list_endpoint.__name__ = f"list_{model.__name__.lower()}"
    app.add_api_route(route, list_endpoint, methods=["GET"], response_model=list[read_schema], summary=f"List/search {label.lower()}")

    def create_endpoint(payload):
        return create_record(model, payload)
    create_endpoint.__name__ = f"create_{model.__name__.lower()}"
    create_endpoint.__annotations__ = {"payload": create_schema, "return": read_schema}
    app.add_api_route(route, create_endpoint, methods=["POST"], response_model=read_schema, status_code=201, summary=f"Create {label.lower().rstrip('s')}")

    def get_endpoint(record_id: int):
        return fetch_record(model, record_id)
    get_endpoint.__name__ = f"get_{model.__name__.lower()}"
    app.add_api_route(route + "/{record_id}", get_endpoint, methods=["GET"], response_model=read_schema, summary=f"Get {label.lower().rstrip('s')}")

    def patch_endpoint(record_id: int, payload):
        return update_record(model, record_id, payload)
    patch_endpoint.__name__ = f"patch_{model.__name__.lower()}"
    patch_endpoint.__annotations__ = {"record_id": int, "payload": update_schema, "return": read_schema}
    app.add_api_route(route + "/{record_id}", patch_endpoint, methods=["PATCH"], response_model=read_schema, summary=f"Partially update {label.lower().rstrip('s')}")
    app.add_api_route(route + "/{record_id}", patch_endpoint, methods=["PUT"], response_model=read_schema, summary=f"Update {label.lower().rstrip('s')}")

    def delete_endpoint(record_id: int):
        delete_record(model, record_id)
        from fastapi import Response
        return Response(status_code=204)
    delete_endpoint.__name__ = f"delete_{model.__name__.lower()}"
    app.add_api_route(route + "/{record_id}", delete_endpoint, methods=["DELETE"], status_code=204, summary=f"Delete {label.lower().rstrip('s')}")

for config in ENTITIES.values():
    register_crud(*config)

@app.get("/api", tags=["Overview"])
def api_overview():
    return {"name": "NetSec Monitor API", "docs": "/docs", "redoc": "/redoc",
            "resources": {cfg[4]: cfg[5] for cfg in ENTITIES.values()}}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    counts = []
    for model, _, _, _, label, route in ENTITIES.values():
        counts.append(f'<li><a href="{route}">{label}</a><strong>{model.select().count()}</strong></li>')
    items = "\n".join(counts)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>NetSec Monitor</title><style>body{{font:16px system-ui;max-width:850px;margin:4rem auto;padding:0 1rem;color:#172033;background:#f3f6fb}}main{{background:white;padding:2rem;border-radius:16px;box-shadow:0 8px 30px #17203312}}h1{{margin-top:0}}li{{display:flex;justify-content:space-between;padding:.75rem;border-bottom:1px solid #e7ebf1}}a{{color:#1456a0}}nav{{display:flex;gap:1rem;margin-top:1.5rem}}</style></head><body><main><h1>NetSec Monitor</h1><p>FastAPI + Peewee REST API · SQLite</p><h2>Resources</h2><ul>{items}</ul><nav><a href="/docs">Swagger UI</a><a href="/redoc">ReDoc</a><a href="/api">API overview</a></nav></main></body></html>"""
