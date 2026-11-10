"""Pydantic v2 request and response schemas for every NetSec entity."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# Users
class UserCreate(Schema):
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=1, max_length=100)
    password_hash: str = Field(default="", max_length=255)
    role: str = Field(default="analyst", max_length=20)
class UserUpdate(Schema):
    username: Optional[str] = Field(default=None, min_length=1, max_length=50)
    email: Optional[str] = Field(default=None, min_length=1, max_length=100)
    password_hash: Optional[str] = Field(default=None, max_length=255)
    role: Optional[str] = Field(default=None, max_length=20)
class UserRead(UserCreate):
    id: int

# Devices
class DeviceCreate(Schema):
    hostname: str = Field(min_length=1, max_length=100)
    ip_address: str = Field(min_length=1, max_length=45)
    device_type: str = Field(default="unknown", max_length=50)
    status: str = Field(default="unknown", max_length=20)
    location: str = Field(default="", max_length=100)
class DeviceUpdate(Schema):
    hostname: Optional[str] = Field(default=None, min_length=1, max_length=100)
    ip_address: Optional[str] = Field(default=None, min_length=1, max_length=45)
    device_type: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=20)
    location: Optional[str] = Field(default=None, max_length=100)
class DeviceRead(DeviceCreate):
    id: int

# Services
class ServiceCreate(Schema):
    device_id: int = Field(gt=0)
    service_name: str = Field(min_length=1, max_length=100)
    port: int = Field(ge=0, le=65535)
    status: str = Field(default="unknown", max_length=20)
class ServiceUpdate(Schema):
    device_id: Optional[int] = Field(default=None, gt=0)
    service_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    port: Optional[int] = Field(default=None, ge=0, le=65535)
    status: Optional[str] = Field(default=None, max_length=20)
class ServiceRead(ServiceCreate):
    id: int

# monitor_logs / security events
class SecurityEventCreate(Schema):
    device_id: int = Field(gt=0)
    status_code: int
    latency_ms: int = Field(default=0, ge=0)
    checked_at: Optional[datetime] = None
class SecurityEventUpdate(Schema):
    device_id: Optional[int] = Field(default=None, gt=0)
    status_code: Optional[int] = None
    latency_ms: Optional[int] = Field(default=None, ge=0)
    checked_at: Optional[datetime] = None
class SecurityEventRead(Schema):
    id: int
    device_id: int
    status_code: int
    latency_ms: int
    checked_at: datetime

# security_alerts / alerts
class AlertCreate(Schema):
    device_id: int = Field(gt=0)
    alert_type: str = Field(min_length=1, max_length=50)
    severity: str = Field(default="medium", max_length=20)
    description: str = ""
    created_at: Optional[datetime] = None
class AlertUpdate(Schema):
    device_id: Optional[int] = Field(default=None, gt=0)
    alert_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    severity: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None
    created_at: Optional[datetime] = None
class AlertRead(Schema):
    id: int
    device_id: int
    alert_type: str
    severity: str
    description: str
    created_at: datetime

# Incidents
class IncidentCreate(Schema):
    alert_id: int = Field(gt=0)
    assigned_user_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=200)
    status: str = Field(default="open", max_length=20)
    created_at: Optional[datetime] = None
class IncidentUpdate(Schema):
    alert_id: Optional[int] = Field(default=None, gt=0)
    assigned_user_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    status: Optional[str] = Field(default=None, max_length=20)
    created_at: Optional[datetime] = None
class IncidentRead(Schema):
    id: int
    alert_id: int
    assigned_user_id: Optional[int]
    title: str
    status: str
    created_at: datetime
