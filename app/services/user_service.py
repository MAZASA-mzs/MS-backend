from sqlalchemy.orm import Session
from app.models.user import User
from app.models.user_account import UserAccount
from app.schemas.user import UserCreate, UserUpdate
from app.redis_client import redis_client
import secrets


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        **user.model_dump(exclude={"platform_name", "platform_user_id"})
    )  # noqa: E501
    db.add(db_user)
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
        return db.query(User).filter(User.user_id == account.user_id).first()
    return None


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> User:
    db_user = db.query(User).filter(User.user_id == user_id).first()
    if db_user:
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
        raise ValueError("Invalid or expired code")

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
        raise ValueError("Account already linked")

    db_account = UserAccount(
        user_id=user_id, platform_name=platform_name, platform_user_id=platform_user_id
    )
    db.add(db_account)
    db.commit()
    redis_client.delete(f"link_code:{code}")
    return True
