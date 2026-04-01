from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from app.database import get_db
from app.schemas.settings import (
    BotCommandCreate, BotCommandUpdate, BotCommandResponse,
    FaqSectionCreate, FaqSectionUpdate, FaqSectionResponse
)
from app.services.settings_service import (
    create_command, update_command, delete_command,
    create_faq, update_faq, delete_faq, get_faqs
)
from typing import List

router = APIRouter()

# -- Commands --
@router.post("/commands", response_model=BotCommandResponse)
def add_command(command: BotCommandCreate, db: Session = Depends(get_db)):
    return create_command(db, command)

@router.patch("/commands/{command_id}", response_model=BotCommandResponse)
def edit_command(command_id: uuid.UUID, command_update: BotCommandUpdate, db: Session = Depends(get_db)):
    updated = update_command(db, str(command_id), command_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Command not found")
    return updated

@router.delete("/commands/{command_id}")
def remove_command(command_id: uuid.UUID, db: Session = Depends(get_db)):
    if not delete_command(db, str(command_id)):
        raise HTTPException(status_code=404, detail="Command not found")
    return {"message": "Command deleted successfully"}


# -- FAQ --
@router.get("/faq/sections", response_model=List[FaqSectionResponse])
def read_all_faqs(db: Session = Depends(get_db)):
    # В админке отдаем даже скрытые (is_enabled=False) разделы
    return get_faqs(db, only_enabled=False)

@router.post("/faq/sections", response_model=FaqSectionResponse)
def add_faq(faq: FaqSectionCreate, db: Session = Depends(get_db)):
    return create_faq(db, faq)

@router.patch("/faq/sections/{section_id}", response_model=FaqSectionResponse)
def edit_faq(section_id: uuid.UUID, faq_update: FaqSectionUpdate, db: Session = Depends(get_db)):
    updated = update_faq(db, str(section_id), faq_update)
    if not updated:
        raise HTTPException(status_code=404, detail="FAQ section not found")
    return updated

@router.delete("/faq/sections/{section_id}")
def remove_faq(section_id: uuid.UUID, db: Session = Depends(get_db)):
    if not delete_faq(db, str(section_id)):
        raise HTTPException(status_code=404, detail="FAQ section not found")
    return {"message": "FAQ section deleted successfully"}
