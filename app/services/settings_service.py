from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound
from app.models.settings import BotCommand, FaqSection
from app.schemas.settings import BotCommandCreate, BotCommandUpdate, FaqSectionCreate, FaqSectionUpdate
from app.exceptions import NotFoundError

def get_commands(db: Session, platform: str = None):
    query = db.query(BotCommand)
    if platform and platform != "ALL":
        query = query.filter(BotCommand.platform_enabled.in_([platform.upper(), "ALL"]))
    return query.all()

def create_command(db: Session, command: BotCommandCreate):
    db_command = BotCommand(**command.model_dump())
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    return db_command

def update_command(db: Session, command_id: str, command_update: BotCommandUpdate):
    try:
        db_command = db.query(BotCommand).filter(BotCommand.command_id == command_id).one()
    except NoResultFound:
        raise NotFoundError(entity_name="BotCommand")

    for key, value in command_update.model_dump(exclude_unset=True).items():
        setattr(db_command, key, value)
    db.commit()
    db.refresh(db_command)
    return db_command

def delete_command(db: Session, command_id: str):
    try:
        db_command = db.query(BotCommand).filter(BotCommand.command_id == command_id).one()
    except NoResultFound:
        raise NotFoundError(entity_name="BotCommand")

    db.delete(db_command)
    db.commit()
    return True

def get_faqs(db: Session, only_enabled: bool = True):
    query = db.query(FaqSection)
    if only_enabled:
        query = query.filter(FaqSection.is_enabled == True)
    return query.order_by(FaqSection.sort_order).all()

def create_faq(db: Session, faq: FaqSectionCreate):
    db_faq = FaqSection(**faq.model_dump())
    db.add(db_faq)
    db.commit()
    db.refresh(db_faq)
    return db_faq

def update_faq(db: Session, section_id: str, faq_update: FaqSectionUpdate):
    try:
        db_faq = db.query(FaqSection).filter(FaqSection.section_id == section_id).one()
    except NoResultFound:
        raise NotFoundError(entity_name="FaqSection")

    for key, value in faq_update.model_dump(exclude_unset=True).items():
        setattr(db_faq, key, value)
    db.commit()
    db.refresh(db_faq)
    return db_faq

def delete_faq(db: Session, section_id: str):
    try:
        db_faq = db.query(FaqSection).filter(FaqSection.section_id == section_id).one()
    except NoResultFound:
        raise NotFoundError(entity_name="FaqSection")

    db.delete(db_faq)
    db.commit()
    return True