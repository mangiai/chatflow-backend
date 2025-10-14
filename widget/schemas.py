from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID

# -------------------------------
#  Widget Settings Schemas
# -------------------------------
class WidgetSettingsBase(BaseModel):
    business_id: UUID
    bot_name: str
    welcome_message: str
    avatar_url: Optional[str] = None
    theme: Optional[Dict] = None
    behavior: Optional[Dict] = None

class WidgetSettingsCreate(WidgetSettingsBase):
    pass

class WidgetSettingsResponse(BaseModel):
    bot_name: str
    welcome_message: str
    avatar_url: Optional[str]
    theme: Optional[Dict]
    behavior: Optional[Dict]

    class Config:
        orm_mode = True

# -------------------------------
#  Widget Chat Schemas
# -------------------------------
class WidgetQuery(BaseModel):
    business_id: UUID
    query: str

class WidgetQueryResponse(BaseModel):
    answer: str
