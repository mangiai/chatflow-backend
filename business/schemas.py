from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class BusinessCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None



class BusinessResponse(BaseModel):
    id: UUID  # 👈 instead of str
    name: str
    industry: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

