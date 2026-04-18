import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, User
from app.services.user_service import (
    create_user,
    get_user_by_platform,
    update_user,
    generate_link_code,
    link_account,
)

router = APIRouter()


@router.post("/register", response_model=User)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)


@router.get("/by-platform/{platform}/{platform_user_id}", response_model=User)
def get_user(platform: str, platform_user_id: str, db: Session = Depends(get_db)):
    return get_user_by_platform(db, platform, platform_user_id)


@router.patch("/{user_id}/contacts", response_model=User)
def update_contacts(
    user_id: uuid.UUID, user_update: UserUpdate, db: Session = Depends(get_db)
):
    return update_user(db, str(user_id), user_update)


@router.post("/{user_id}/consent")
def set_consent(user_id: uuid.UUID, consent: bool, db: Session = Depends(get_db)):
    update_user(db, str(user_id), UserUpdate(consent=consent))
    return {"message": "Consent updated"}


@router.post("/{user_id}/dobroid")
def set_dobro_id(user_id: uuid.UUID, dobro_id: str, db: Session = Depends(get_db)):
    update_user(db, str(user_id), UserUpdate(dobro_id=dobro_id))
    return {"message": "Dobro ID updated"}


@router.delete("/{user_id}/dobroid")
def delete_dobro_id(user_id: uuid.UUID, db: Session = Depends(get_db)):
    update_user(db, str(user_id), UserUpdate(dobro_id=None))
    return {"message": "Dobro ID removed"}


@router.post("/me/generate-link-code")
def generate_code(user_id: uuid.UUID):
    code = generate_link_code(str(user_id))
    return {"code": code}


@router.post("/link-account")
def link_acc(
    platform_name: str, platform_user_id: str, code: str, db: Session = Depends(get_db)
):
    link_account(db, platform_name, platform_user_id, code)
    return {"message": "Account linked"}
