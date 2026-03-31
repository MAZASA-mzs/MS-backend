from sqlalchemy import Column, String, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base


class UserAccount(Base):
    __tablename__ = "user_accounts"

    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    platform_name = Column(String)  # "telegram" or "maks"
    platform_user_id = Column(String)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )  # noqa: E501
