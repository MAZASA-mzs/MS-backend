from fastapi import APIRouter, Depends, HTTPException
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
    user = get_user_by_platform(db, platform, platform_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}/contacts", response_model=User)
def update_contacts(user_id: str, user_update: UserUpdate, db: Session = Depends(get_db)):
    user = update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{user_id}/consent")
def set_consent(user_id: str, consent: bool, db: Session = Depends(get_db)):
    user = update_user(db, user_id, UserUpdate(consent=consent))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Consent updated"}

@router.post("/{user_id}/dobroid")
def set_dobro_id(user_id: str, dobro_id: str, db: Session = Depends(get_db)):
    user = update_user(db, user_id, UserUpdate(dobro_id=dobro_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Dobro ID updated"}

@router.delete("/{user_id}/dobroid")
def delete_dobro_id(user_id: str, db: Session = Depends(get_db)):
    user = update_user(db, user_id, UserUpdate(dobro_id=None))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Dobro ID removed"}

@router.post("/me/generate-link-code")
def generate_code(user_id: str):
    # In real app, consider getting user_id from a JWT or session
    code = generate_link_code(user_id)
    return {"code": code}

@router.post("/link-account")
def link_acc(platform_name: str, platform_user_id: str, code: str, db: Session = Depends(get_db)):
    try:
        link_account(db, platform_name, platform_user_id, code)
        return {"message": "Account linked"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))