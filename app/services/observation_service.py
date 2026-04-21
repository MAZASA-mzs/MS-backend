import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.content import (
    Post,
    Geolocation,
    post_users,
    user_geolocations,
    post_geolocations,
)
from app.models.user import User, UserStats
from app.services.ai_service import get_and_delete_stashed_image
from app.services.yandex_disk import upload_file_to_yandex_disk
from app.schemas.observation import PostCreate

from app.exceptions import NotFoundError, InvalidReferenceError, BusinessLogicError


def process_and_create_post(db: Session, payload: PostCreate) -> Post:
    # 1. Check if user exists
    user = db.query(User).filter(User.user_id == str(payload.user_id)).first()
    if not user:
        raise NotFoundError("User")

    # 2. Validate business logic: if AI failed, user must choose
    if payload.ai_plant_id == -1 and payload.user_plant_id == -1:
        raise BusinessLogicError(
            "User must select a plant class if AI failed to recognize it."
        )

    # 3. Get stashed image from AI service
    stashed_file = get_and_delete_stashed_image(payload.temp_file_id)
    if not stashed_file:
        raise BusinessLogicError("File expired or invalid temp_file_id")

    # 4. Upload file to Yandex Disk and get the link
    filename = f"{uuid.uuid4()}_{stashed_file['filename']}"
    link = upload_file_to_yandex_disk(
        file_bytes=stashed_file["bytes"],
        filename=filename,
        content_type=stashed_file["content_type"],
    )

    # 5. Save post to the database
    post = Post(
        link=link,
        post_description=payload.description,
        ai_plant_id=payload.ai_plant_id,
        ai_confidence=payload.ai_confidence,
        user_plant_id=payload.user_plant_id,
    )
    db.add(post)

    try:
        db.flush()
        # Link user with post
        db.execute(
            post_users.insert().values(
                user_id=str(payload.user_id), post_id=post.post_id
            )
        )
        db.commit()
        db.refresh(post)
        return post
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError(
            "Failed to link post. Integrity constraint violated."
        )


def create_post(
    db: Session,
    user_id: str,
    link: str,
    description: str,
    ai_plant_id: int,
    ai_confidence: float,
    user_plant_id: int,
) -> Post:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    # Validate that at least one of the plant IDs is provided
    if ai_plant_id == -1 and user_plant_id == -1:
        raise BusinessLogicError(
            "User must select a plant class if AI failed to recognize it."
        )

    # Send the post to the database
    post = Post(
        link=link,
        post_description=description,
        ai_plant_id=ai_plant_id,
        ai_confidence=ai_confidence,
        user_plant_id=user_plant_id,
    )
    db.add(post)

    try:
        db.flush()

        # Connect user with post
        db.execute(post_users.insert().values(user_id=user_id, post_id=post.post_id))

        db.commit()
        db.refresh(post)
        return post
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError(
            "Failed to link post. Integrity constraint violated."
        )


def create_geolocation(db: Session, user_id: str, x: float, y: float) -> Geolocation:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    geo = Geolocation(x=x, y=y)
    db.add(geo)

    try:
        db.flush()

        # Connect user with geo
        db.execute(
            user_geolocations.insert().values(user_id=user_id, geo_id=geo.geo_id)
        )

        db.commit()
        db.refresh(geo)
        return geo
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError(
            "Failed to link geolocation. Integrity constraint violated."
        )


def link_photo_geo(db: Session, user_id: str, post_id: str, geo_id: str) -> bool:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    try:
        db.execute(post_geolocations.insert().values(post_id=post_id, geo_id=geo_id))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError(
            "Provided Post ID or Geolocation ID does not exist, or link already exists."
        )


def get_user_stats(db: Session, user_id: str) -> UserStats:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")
    try:
        post_count = (
            db.query(Post)
            .join(post_users, Post.post_id == post_users.c.post_id)
            .filter(post_users.c.user_id == user_id)
            .count()
        )
        geo_count = (
            db.query(Geolocation)
            .join(user_geolocations, Geolocation.geo_id == user_geolocations.c.geo_id)
            .filter(user_geolocations.c.user_id == user_id)
            .count()
        )
        return UserStats(post_count, geo_count)

    except IntegrityError:
        db.rollback()
        raise InvalidReferenceError("Error while getting user stats.")
