from sqlalchemy.orm import Session
from app.models.content import Post, Geolocation, post_users, user_geolocations, post_geolocations
from app.models.user import User


def create_post(db: Session, user_id: str, link: str, description: str) -> Post:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    post = Post(link=link, post_description=description)
    db.add(post)
    db.commit()
    db.refresh(post)

    # Connect user with post
    db.execute(post_users.insert().values(user_id=user_id, post_id=post.post_id))
    db.commit()
    return post


def create_geolocation(db: Session, user_id: str, x: float, y: float) -> Geolocation:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    geo = Geolocation(x=x, y=y)
    db.add(geo)
    db.commit()
    db.refresh(geo)

    # Connect user with geo
    db.execute(user_geolocations.insert().values(user_id=user_id, geo_id=geo.geo_id))
    db.commit()
    return geo


def link_photo_geo(db: Session, user_id: str, post_id: str, geo_id: str) -> bool:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise ValueError("User not found")

    db.execute(post_geolocations.insert().values(post_id=post_id, geo_id=geo_id))
    db.commit()
    return True