from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, NoResultFound
from app.models.user import User
from app.models.user_account import UserAccount
from app.schemas.user import UserCreate, UserUpdate
from app.redis_client import redis_client
import secrets
from app.exceptions import NotFoundError, InvalidReferenceError, BusinessLogicError


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        **user.model_dump(exclude={"platform_name", "platform_user_id"})
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)

        # Create user account
        db_account = UserAccount(
            user_id=db_user.user_id,
            platform_name=user.platform_name,
            platform_user_id=user.platform_user_id,
        )
        db.add(db_account)
        db.commit()
        return db_user
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError("Platform user ID already registered")


def get_user_by_platform(db: Session, platform: str, platform_user_id: str) -> User:
    account = (
        db.query(UserAccount)
        .filter(
            UserAccount.platform_name == platform,
            UserAccount.platform_user_id == platform_user_id,
        )
        .first()
    )
    if account:
        try:
            return db.query(User).filter(User.user_id == account.user_id).one()
        except NoResultFound:
            raise NotFoundError("User")

    raise NotFoundError("User")


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> User:
    try:
        db_user = db.query(User).filter(User.user_id == user_id).one()
    except NoResultFound:
        raise NotFoundError("User")

    for key, value in user_update.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def generate_link_code(user_id: str) -> str:
    code = secrets.token_hex(3).upper()  # e.g., ABC123
    redis_client.setex(f"link_code:{code}", 300, user_id)  # TTL 5 min
    return code


def link_account(db: Session, platform_name: str, platform_user_id: str, code: str):
    user_id = redis_client.get(f"link_code:{code}")
    if not user_id:
        raise BusinessLogicError("Invalid or expired code")

    try:
        user_id = user_id.decode()
    except AttributeError:
        raise BusinessLogicError("Invalid or expired code")

    # Check if account already exists
    existing = (
        db.query(UserAccount)
        .filter(
            UserAccount.platform_name == platform_name,
            UserAccount.platform_user_id == platform_user_id,
        )
        .first()
    )
    if existing:
        raise BusinessLogicError("Account already linked")

    db_account = UserAccount(
        user_id=user_id, platform_name=platform_name, platform_user_id=platform_user_id
    )
    db.add(db_account)

    try:
        db.commit()
        redis_client.delete(f"link_code:{code}")
        return True
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError("User for this code no longer exists in DB.")