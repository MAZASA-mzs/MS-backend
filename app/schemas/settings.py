from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# BotCommand Schemas
class BotCommandBase(BaseModel):
    command_name: str = Field(..., description="Имя команды (например /start)")
    command_description: Optional[str] = Field(None, description="Описание команды")
    platform_enabled: str = Field(
        "ALL", description="Ограничение по платформе (ALL, TG, MAX)"
    )


class BotCommandCreate(BotCommandBase):
    user_id_create: Optional[UUID] = None


class BotCommandUpdate(BaseModel):
    command_name: Optional[str] = None
    command_description: Optional[str] = None
    platform_enabled: Optional[str] = None
    user_update: Optional[UUID] = None


class BotCommandResponse(BotCommandBase):
    command_id: UUID
    time_create: datetime
    user_id_create: Optional[UUID] = None
    user_update: Optional[UUID] = None
    time_update: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# FAQ Schemas
class FaqSectionBase(BaseModel):
    title: str = Field(..., description="Заголовок раздела")
    description: str = Field(..., description="Текст/Ответ раздела")
    sort_order: int = Field(0, description="Порядок сортировки при выдаче")
    is_enabled: bool = Field(True, description="Флаг активности")


class FaqSectionCreate(FaqSectionBase):
    pass


class FaqSectionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None


class FaqSectionResponse(FaqSectionBase):
    section_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
