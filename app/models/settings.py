from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class BotCommand(Base):
    __tablename__ = "bot_commands"

    command_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    command_name = Column(String, nullable=False)
    command_description = Column(Text, nullable=True)
    time_create = Column(TIMESTAMP(timezone=True), server_default=func.now())
    user_id_create = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    user_update = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    platform_enabled = Column(String, nullable=False, default="ALL") # ALL, TG, MAX
    time_update = Column(TIMESTAMP(timezone=True), onupdate=func.now())

class FaqSection(Base):
    __tablename__ = "faq_sections"

    section_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
