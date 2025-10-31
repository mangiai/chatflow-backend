from sqlalchemy import Column, String, JSON, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from core.db import Base
import uuid

class WidgetSettings(Base):
    __tablename__ = "widget_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business.id"), nullable=False)
    bot_name = Column(String, nullable=False)
    welcome_message = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    theme = Column(JSON, nullable=True)
    behavior = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)




class WidgetChatSession(Base):
    __tablename__ = "widget_chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("business.id"), nullable=False)
    visitor_id = Column(String, nullable=False)  # random per-visitor ID
    created_at = Column(DateTime, default=datetime.utcnow)


class WidgetChatMessage(Base):
    __tablename__ = "widget_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("widget_chat_sessions.id"), nullable=False)
    sender = Column(String, nullable=False)   # 'user' or 'bot'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)