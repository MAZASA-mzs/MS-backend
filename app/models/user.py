from sqlalchemy import Column, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fio = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    sex = Column(Boolean, nullable=True)  # True for male, False for female
    role = Column(String, default="user")  # admin or user
    dobro_id = Column(String, nullable=True)
    consent = Column(Boolean, default=False)
