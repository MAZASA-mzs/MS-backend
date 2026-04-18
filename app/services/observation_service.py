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

from app.exceptions import NotFoundError, InvalidReferenceError


def create_post(db: Session, user_id: str, link: str, description: str) -> Post:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise NotFoundError("User")

    post = Post(link=link, post_description=description)
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
