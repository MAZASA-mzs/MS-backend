from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    fio: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    sex: Optional[bool] = None
    role: str = "user"
    dobro_id: Optional[str] = None
    consent: bool = False


class UserCreate(UserBase):
    platform_name: str
    platform_user_id: str


class UserUpdate(UserBase):
    pass


class User(UserBase):
    user_id: UUID

    class Config:
        from_attributes = True


class UserAccountBase(BaseModel):
    platform_name: str
    platform_user_id: str


class UserAccount(UserAccountBase):
    account_id: UUID
    user_id: UUID
    created_at: str

    class Config:
        from_attributes = True
