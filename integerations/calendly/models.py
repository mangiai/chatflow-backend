from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from core.db import Base
import uuid


class CalendlyCredential(Base):
    __tablename__ = "calendly_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ✅ Adapted to match your current Business model
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("business.id"),  # matches your Business table name
        nullable=False,
        unique=True
    )

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    owner = Column(String, nullable=True)          # e.g. https://api.calendly.com/users/xxxx
    organization = Column(String, nullable=True)
    scope = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
