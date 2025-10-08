from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from core.db import Base

class Knowledge(Base):
    __tablename__ = "knowledge"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_name = Column(String)
    file_url = Column(String, nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
