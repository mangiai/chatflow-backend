from pydantic import BaseModel, AnyHttpUrl
from uuid import UUID
from datetime import datetime
from typing import List, Optional

class OAuthStartResponse(BaseModel):
    authorize_url: AnyHttpUrl
    state: str

class CalendlyStatus(BaseModel):
    connected: bool
    owner: Optional[str] = None
    expires_at: Optional[datetime] = None

class EventType(BaseModel):
    uri: str
    name: str
    slug: Optional[str] = None
    kind: Optional[str] = None
    scheduling_url: Optional[str] = None
    active: Optional[bool] = None

class EventTypesResponse(BaseModel):
    items: List[EventType]

class ScheduleLinkRequest(BaseModel):
    event_type_uri: str

class ScheduleLinkResponse(BaseModel):
    scheduling_url: AnyHttpUrl
